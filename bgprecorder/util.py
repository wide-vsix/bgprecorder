import json
from datetime import datetime, date
import os
import psycopg2
import ipaddress

from psycopg2.extras import DictCursor


def json_serial_default(obj):
    # 日付型の場合には、文字列に変換します
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    # 上記以外はサポート対象外.
    raise TypeError("Type %s not serializable" % type(obj))


DATETIME_FORMAT = '%Y%m%d%H%M'


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
    sql = '''
    SELECT
    pg_class.relname
    FROM pg_stat_user_tables
    INNER JOIN pg_class ON pg_stat_user_tables.relname = pg_class.relname
    where pg_class.reltuples > 1
    order by relname asc;
    '''
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


def longest_match(routes) -> list:
    longest_prefix = 0
    for route in routes:
        prefixlen = ipaddress.ip_network(route["nlri"]).prefixlen
        if prefixlen >= longest_prefix:
            longest_prefix = prefixlen
    return [route for route in routes if ipaddress.ip_network(route["nlri"]).prefixlen == longest_prefix]
