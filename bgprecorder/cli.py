from logzero import logger
import pickledb
import argparse
from datetime import datetime
import os
import json
import pathlib
import time

from .bgprecorder import BgpRecorder
from . import util
from importlib import metadata

__version__ = metadata.version(__package__)

if __version__ == "0.0.0":
    __version__ = "UNKNOWN(localy build)"


def query():
    '''
    Client CLI tool
    '''
    parser = argparse.ArgumentParser(
        description='bgpquery: get BGP rib json from bgprecorder db')
    parser.add_argument('--version', version='%(prog)s ' + __version__,
                        action='version',
                        default=False)
    parser.add_argument('-a', '--address', type=str,
                        help='target address', required=True)
    parser.add_argument('-t', '--datetime', default=None, type=str,
                        help=f'target datetime. example: "200601021504"')
    parser.add_argument('-H', '--db_host', default=os.getenv("BGPRECORDER_DB_HOST", "localhost"), type=str,
                        help=f'db host. default: localhost or $BGPRECORDER_DB_HOST')
    parser.add_argument('-p', '--db_port', default=int(os.getenv("BGPRECORDER_DB_PORT", "5432")), type=int,
                        help=f'db port. default: 5432 or $BGPRECORDER_DB_PORT')
    parser.add_argument('-u', '--db_user', default=os.getenv("BGPRECORDER_DB_USER", "postgres"), type=str,
                        help=f'db user. default: postgres or $BGPRECORDER_DB_USER')
    parser.add_argument('-w', '--db_password', default=os.getenv("BGPRECORDER_DB_PASSWORD"), type=str,
                        help=f'db user. default: None or $BGPRECORDER_DB_PASSWORD ')
    parser.add_argument('-d', '--db_name', default=os.getenv("BGPRECORDER_DB_NAME", "bgprecorder"), type=str,
                        help=f'db user. default: bgprecorder or $BGPRECORDER_DB_RECORDER')

    args = parser.parse_args()

    address = args.address
    if not args.datetime:
        target_datetime = datetime.now()
    else:
        target_datetime = datetime.strptime(
            args.datetime, BgpRecorder.datetime_format)

    br = BgpRecorder(db_host=args.db_host, db_port=args.db_port,
                     db_name=args.db_name, db_user=args.db_user, db_password=args.db_password)

    routes = br.get_routes_from_address_and_datetime(
        address=address, target_datetime=target_datetime)

    matched_routes = util.longest_match(routes=routes)

    for route in matched_routes:
        print(json.dumps(route, default=util.json_serial_default))


def recorder():
    parser = argparse.ArgumentParser(
        description='bgprecord dump BGP MRT rib to DB')
    parser.add_argument('--version', version='%(prog)s ' + __version__,
                        action='version',
                        default=False)
    parser.add_argument('-H', '--db_host', default=os.getenv("BGPRECORDER_DB_HOST", "localhost"), type=str,
                        help=f'db host. default: localhost or $BGPRECORDER_DB_HOST')
    parser.add_argument('-p', '--db_port', default=int(os.getenv("BGPRECORDER_DB_PORT", "5432")), type=int,
                        help=f'db port. default: 5432 or $BGPRECORDER_DB_PORT')
    parser.add_argument('-u', '--db_user', default=os.getenv("BGPRECORDER_DB_USER", "postgres"), type=str,
                        help=f'db user. default: postgres or $BGPRECORDER_DB_USER')
    parser.add_argument('-w', '--db_password', default=os.getenv("BGPRECORDER_DB_PASSWORD"), type=str,
                        help=f'db password. default: None or $BGPRECORDER_DB_PASSWORD')
    parser.add_argument('-d', '--db_name', default=os.getenv("BGPRECORDER_DB_NAME", "bgprecorder"), type=str,
                        help=f'db name. default: bgprecorder or $BGPRECORDER_DB_RECORDER')
    parser.add_argument('-c', '--compress', default=bool(os.getenv("BGPRECORDER_COMPRESS", False)), type=bool,
                        help=f'compress MRT dump after import. default: False')
    parser.add_argument('-i', '--duration', default=int(os.getenv("BGPRECORDER_DURATION", default="3600")), type=int,
                        help=f'interval of recording (sec.) default: 3600 or $BGPRECORDER_DURATION')
    parser.add_argument('-f', '--mrt_dump_files', default=os.getenv(
        "BGPRECORDER_TARGET_FILES", default="./mrt/*.dump"), type=str,
        help=f'target MRT dumpfile match rule.  default: ./mrt/*.dump or $BGPRECORDER_DURATION')

    args = parser.parse_args()

    saved_file_cache = pickledb.load(os.getenv(
        "BGPRECORDER_CACHE_FILE", default="/tmp/bgprecorder.db"), True)  # auto dump
    args.mrt_dump_files = args.mrt_dump_files

    br = BgpRecorder(db_host=args.db_host, db_port=args.db_port,
                     db_name=args.db_name, db_user=args.db_user, db_password=args.db_password)

    while True:
        logger.info("Cycle started.")
        # get current dump files
        files = util.get_files(args.mrt_dump_files)

        for file in files:
            table_name = util.get_table_name_from_file_path(file_path=file)
            logger.info(f"Check file:{file}")

            # check valid flag
            if saved_file_cache.get(table_name):
                logger.info(f"Already recorded: {file}")
                if args.compress:
                    logger.info(f"file: {file} try to compress....")
                    if util.bzip2(file):
                        logger.info(f"file: {file} is compressed.")
                continue

            # set valid flag
            if br.is_table_exists(table_name=table_name):
                logger.info(f"Already registered: {file}")
                logger.info(f"set valid flag")
                saved_file_cache.set(table_name, True)
                continue

            # 正常に登録できてないor新規なので一旦flagをfalseにする．
            saved_file_cache.set(table_name, False)

            # exists check
            if not pathlib.Path(file).exists():
                logger.warning("File not found. ignore")
                continue
            # check emptyfile or not
            if not os.stat(file).st_size > 0:
                logger.warning("Empty file. ignore")
                continue

            logger.info(f"file: {file} found! try to record...")
            if __create_table_and_insert_route(br=br, file_path=file):
                logger.info(f"file: {file} is successfully recorded.")
                # validation check when next reconcile?
            else:
                logger.error(f"file: {file} could not be recorded.")

        logger.info(f"Cycle finished. sleep {args.duration} sec.")
        time.sleep(args.duration)


def __create_table_and_insert_route(br: BgpRecorder, file_path: str) -> bool:

    table_name = util.get_table_name_from_file_path(file_path=file_path)

    cmd = f"bgpdump -m {file_path}"

    # drop table if exists
    if br.is_table_exists(table_name):
        br.drop_table(table_name=table_name)

    # create table
    if not br.create_new_rib_table(table_name):
        logger.error("Can not create table. abort")
        return False

    # insert
    insert_successed = False
    with br.get_db_connection() as con:
        for line in util.localExecGetLines(cmd):
            route_obj = util.parse_bgpdump_record_to_route_obj(
                line.decode().strip())

            if not br.insert_route(route_obj=route_obj, table_name=table_name, con=con):
                logger.error("Insert Error")
                con.cancel()
                break
        else:
            con.commit()
            insert_successed = True
    return insert_successed


if __name__ == "__main__":
    recorder()
