import psycopg2
from psycopg2.extras import DictCursor
import os
import pathlib
from datetime import datetime
import argparse
import sys
import glob
import time
import ipaddress
from datetime import datetime, date, timedelta
import json

DATETIME_FORMAT = '%Y%m%d%H%M'


def json_serial_default(obj):
    # 日付型の場合には、文字列に変換します
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    # 上記以外はサポート対象外.
    raise TypeError("Type %s not serializable" % type(obj))


def connect():
    host = os.getenv("BGPRECORDER_DB_HOST")
    port = int(os.getenv("BGPRECORDER_DB_PORT", "5432"))
    dbname = os.getenv("BGPRECORDER_DB_NAME")
    user = os.getenv("BGPRECORDER_DB_USER")
    password = os.getenv("BGPRECORDER_DB_PASSWORD")
    con = psycopg2.connect(host=host, port=port,
                           dbname=dbname, user=user, password=password)
    return con


def get_tables() -> list:
    sql = "select pg_stat_user_tables.relname from pg_stat_user_tables order by relname asc;"  # 新しいもの順
    with connect() as con:
        with con.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()  # [('bgprib_202207080313',),...]
            return [row[0] for row in rows]


def get_nearest_tablename(target_datetime: datetime) -> str:
    # get available tables
    table_names = get_tables()

    # convert table_name to datetime
    datetimes = [datetime.strptime(table_name.split("_")[1], DATETIME_FORMAT)
                 for table_name in table_names]

    # search nearenst
    nearrest_datetime = min(datetimes, key=lambda x: abs(x - target_datetime))

    table_name = f"bgprib_{nearrest_datetime.strftime(DATETIME_FORMAT)}"
    return table_name


def get_routes_from_address(address: str, table_name: str) -> list:
    sql = f"select * from {table_name} where inet %s << {table_name}.nlri;"

    with connect() as con:
        with con.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(sql, [address])
            rows = cur.fetchall()  # [('bgprib_202207080313',),...]
            return [dict(row) for row in rows]


def get_routes_from_address_and_datetime(address: str, target_datetime: datetime) -> list:
    table_name = get_nearest_tablename(target_datetime=target_datetime)
    return get_routes_from_address(address=address, table_name=table_name)


def get_args():
    parser = argparse.ArgumentParser(
        description='This is sample argparse script')
    parser.add_argument('-a', '--address', type=str,
                        help='target address', required=True)
    parser.add_argument('-d', '--datetime', default=None, type=str,
                        help=f'target datetime. format:{DATETIME_FORMAT}')
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()

    address = args.address
    if not args.datetime:
        dt = datetime.now()
    else:
        dt = datetime.strptime(args.datetime, DATETIME_FORMAT)

    routes = get_routes_from_address_and_datetime(
        address=address, target_datetime=dt)
    for route in routes:
        print(json.dumps(route, default=json_serial_default))
