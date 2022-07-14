import imp
from datetime import datetime
import psycopg2
import psycopg2.extras
from logzero import logger


class BgpRecorder():
    datetime_format = '%Y%m%d%H%M'
    table_name_prefix = "bgprib_"

    '''
    Common methods
    '''

    def __init__(self, db_host: str, db_port: int, db_name: str, db_user: str,  db_password: str) -> None:
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password

    def get_db_connection(self) -> psycopg2.extensions.connection:
        con = psycopg2.connect(host=self.db_host, port=self.db_port,
                               dbname=self.db_name, user=self.db_user, password=self.db_password)
        return con

    '''
    Client methods
    '''

    def get_tables(self) -> list:
        sql = '''
        SELECT
        pg_class.relname
        FROM pg_stat_user_tables
        INNER JOIN pg_class ON pg_stat_user_tables.relname = pg_class.relname
        where pg_class.reltuples > 1
        order by relname asc;
        '''
        with self.get_db_connection() as con:
            with con.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()  # [('bgprib_202207080313',),...]
                return [row[0] for row in rows]

    def get_nearest_tablename(self, target_datetime: datetime) -> str:
        # get available tables
        table_names = self.get_tables()

        # convert table_name to datetime
        datetimes = [datetime.strptime(table_name.split("_")[1], self.datetime_format)
                     for table_name in table_names]

        # search nearenst
        nearrest_datetime = min(
            datetimes, key=lambda x: abs(x - target_datetime))

        table_name = f"{self.table_name_prefix}{nearrest_datetime.strftime(self.datetime_format)}"
        return table_name

    def get_routes_from_address(self, address: str, table_name: str) -> list:
        sql = f"select * from {table_name} where inet %s << {table_name}.nlri;"

        with self.get_db_connection() as con:
            with con.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(sql, [address])
                rows = cur.fetchall()
                return [dict(row) for row in rows]

    def get_routes_from_address_and_datetime(self, address: str, target_datetime: datetime) -> list:
        table_name = self.get_nearest_tablename(
            target_datetime=target_datetime)
        return self.get_routes_from_address(address=address, table_name=table_name)

    def get_route_count(self, table_name: str) -> int:
        sql = f"SELECT count(*) from {table_name};"

        with self.get_db_connection() as con:
            with con.cursor() as cur:
                cur.execute(sql)
                count = cur.fetchone()[0]
                return count

    def is_table_exists(self, table_name: str) -> bool:
        try:
            # レコード0なら意味無し
            return self.get_route_count(table_name=table_name) > 0
        except Exception as e:
            return False

    def drop_table(self, table_name: str) -> bool:
        sql = f"DROP TABLE {table_name};"
        with self.get_db_connection() as con:
            with con.cursor() as cur:
                cur.execute(sql)
            con.commit()
        return True

    '''
    insert methods
    '''

    def __query_buildar(self, route_obj: dict, table_name: str) -> str:
        column_string = ",".join(route_obj.keys())
        holders = ["%s" for obj in route_obj.keys()]
        value_holder = ",".join(holders)

        sql = f'insert into {table_name}({column_string}) values({value_holder});'

        return sql

    def create_new_rib_table(self, table_name: str) -> bool:
        sql = f'''
        create table {table_name}
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
            with self.get_db_connection() as con:
                with con.cursor() as cur:
                    cur.execute(sql)
                con.commit()
        except psycopg2.errors.DuplicateTable as e:
            logger.warning(f"Table:{table_name} is already exists. ignore")
        except Exception as e:
            logger.error("Create Table Error")
            logger.error(e)
            return False
        return True

    def insert_route(self, route_obj: dict, table_name: str, con: psycopg2.extensions.connection = None):
        sql = self.__query_buildar(route_obj, table_name)
        try:
            if con is None:
                with self.get_db_connection() as con:
                    with con.cursor() as cur:
                        cur.execute(sql, list(route_obj.values()))
                    return True
            else:
                with con.cursor() as cur:
                    cur.execute(sql, list(route_obj.values()))
                return True
        except Exception as e:
            logger.error("DB Error. Can not insert record.")
            logger.error(e)
            return False
