import psycopg2
import os
import pathlib
from datetime import datetime
import subprocess
from logzero import logger
import pickledb
import glob
import time


def localExec(cmd):
    proc = subprocess.run(
        cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc.returncode == 0


def bzip2(filename, delete_src=True):
    delete_options = "" if delete_src else "-k"
    cmd = f"bzip2 {delete_options} {filename}"
    return localExec(cmd)


def localExecGetLines(cmd):
    proc = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    while True:
        line = proc.stdout.readline()
        if line:
            yield line

        if not line and proc.poll() is not None:
            break


def connect():
    host = os.getenv("BGPRECORDER_DB_HOST")
    port = int(os.getenv("BGPRECORDER_DB_PORT", "5432"))
    dbname = os.getenv("BGPRECORDER_DB_NAME")
    user = os.getenv("BGPRECORDER_DB_USER")
    password = os.getenv("BGPRECORDER_DB_PASSWORD")
    con = psycopg2.connect(host=host, port=port,
                           dbname=dbname, user=user, password=password)
    return con


def parse_record(record: str):
    params = record.split("|")
    route_obj = {
        "time": datetime.fromtimestamp(int(params[1])),
        "path_id": params[6],
        "type_name": params[0],
        "aspath": params[7],
        # sequence
        "from_ip": params[3],
        "from_as": params[4],
        "origin": params[8],
        # originated
        # nlri_type
        "nlri": params[5],
        "nexthop": params[9],
        "community": params[12],
        # large_community

    }
    return route_obj


def query_buildar(route_obj, table_name):
    column_string = ",".join(route_obj.keys())
    holders = ["%s" for obj in route_obj.keys()]
    value_holder = ",".join(holders)

    sql = f'insert into {table_name}({column_string}) values({value_holder});'

    return sql


def insert_route(route_obj, con, table_name):
    sql = query_buildar(route_obj, table_name)
    try:
        with con.cursor() as cur:
            cur.execute(sql, list(route_obj.values()))
        return True
    except Exception as e:
        logger.Error("DB Error. Can not insert record.")
        logger.Error(e)
        return False


def create_new_table(tablename):
    sql = f'''
    create table {tablename}
    (
        id SERIAL NOT NULL,
        time timestamp,
        path_id integer,
        type_name VARCHAR (64),
        sequence integer,
        from_ip inet,
        from_as integer,
        originated  timestamp,
        origin VARCHAR(32),
        aspath VARCHAR (256),
        nlri_type VARCHAR(32),
        nlri cidr,
        nexthop  inet,
        community VARCHAR (256),
        large_community VARCHAR (256)
    );
    '''
    try:
        with connect() as con:
            with con.cursor() as cur:
                cur.execute(sql)
            con.commit()
    except psycopg2.errors.DuplicateTable as e:
        logger.warning(f"Table:{tablename} is already exists. ignore")
    except Exception as e:
        logger.error("Create Table Error")
        logger.error(e)
        return False
    return True


def create_table_and_insert_route(filepath):
    # It takes about 20 sec. per IPv6 fullroutes.
    # filepath = "mrt/20220711.1647.dump"
    filename = pathlib.Path(filepath).name
    table_name = get_table_name_from_filepath(filepath=filepath)
    cmd = f"bgpdump -m {filepath}"

    # exists check
    if not pathlib.Path(filepath).exists():
        logger.warning("File not found. ignore")
        return False
    # check emptyfile or not
    if not os.stat(filepath).st_size > 0:
        logger.warning("Empty file. ignore")
        return False

    # create table
    if not create_new_table(table_name):
        logger.Error("Can not create table. abort")
        return False

    # insert
    insert_successed = False
    with connect() as con:
        for line in localExecGetLines(cmd):
            route_obj = parse_record(line.decode().strip())
            if not insert_route(route_obj, con, table_name):
                logger.Error("Insert Error")
                con.cancel()
                break
        else:
            con.commit()
            insert_successed = True
    return insert_successed


def get_table_name_from_filepath(filepath):
    return f"bgprib_{pathlib.Path(filepath).stem.replace('.','')}"


def get_dump_files():
    target_match = os.getenv(
        "BGPRECORDER_TARGET_FILES", default="./mrt/*.dump")
    files = glob.glob(f"{target_match}")
    return files


def is_table_exists(filepath):
    table_name = get_table_name_from_filepath(filepath=filepath)

    sql = "SELECT count(*) from %s;"

    with connect() as con:
        with con.cursor() as cur:
            try:
                cur.execute(sql, [table_name])
                cur.fetchone()
            except Exception as e:
                logger.error("table lookup error")
                logger.error(e)
                return False
    return True


def main():
    saved_file_cache = pickledb.load(os.getenv(
        "BGPRECORDER_CACHE_FILE", default="./bgprecorder.db"), True)  # auto dump
    sleep_second = int(os.getenv("BGPRECORDER_DURATION", default="3600"))
    is_compress = os.getenv("BGPRECORDER_COMPRESS", default=True)

    while True:
        logger.info("Cycle started.")
        # get current dump files
        files = get_dump_files()
        for file in files:
            logger.info(f"Check file:{file}")

            # check already exists or not
            if saved_file_cache.get(file) and is_table_exists(filepath=file):
                logger.info(f"Already registered: {file}")
                if is_compress:
                    if bzip2(file):
                        logger.info(f"file: {file} is compressed.")
                continue
            # 正常に登録できてないので一旦flagをfalseにする． 誤ってsetされているとこうなる．
            saved_file_cache.set(file, False)

            logger.info(f"file: {file} found! try to record...")
            if create_table_and_insert_route(file):
                logger.info(f"file: {file} is successfully recorded.")
                saved_file_cache.set(file, True)  # successfully flag
                if is_compress:
                    if bzip2(file):
                        logger.info(f"file: {file} is compressed.")
            else:
                logger.error(f"file: {file} could not be recorded.")

        logger.info(f"Cycle finished. sleep {sleep_second} sec.")
        time.sleep(sleep_second)


if __name__ == "__main__":
    main()
