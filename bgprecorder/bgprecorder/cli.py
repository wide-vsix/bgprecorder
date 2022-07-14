from logzero import logger
import argparse
from datetime import datetime
import os
import json

from .bgprecorder import BgpRecorder
from . import util


def query():
    '''
    Client CLI tool
    '''
    parser = argparse.ArgumentParser(
        description='This is sample argparse script')
    parser.add_argument('-a', '--address', type=str,
                        help='target address', required=True)
    parser.add_argument('-d', '--datetime', default=None, type=str,
                        help=f'target datetime. example: "200601021504"')

    args = parser.parse_args()

    address = args.address
    if not args.datetime:
        target_datetime = datetime.now()
    else:
        target_datetime = datetime.strptime(
            args.datetime, BgpRecorder.datetime_format)

    db_host = os.getenv("BGPRECORDER_DB_HOST")
    db_port = int(os.getenv("BGPRECORDER_DB_PORT", "5432"))
    db_name = os.getenv("BGPRECORDER_DB_NAME")
    db_user = os.getenv("BGPRECORDER_DB_USER")
    db_password = os.getenv("BGPRECORDER_DB_PASSWORD")

    br = BgpRecorder(db_host=db_host, db_port=db_port,
                     db_name=db_name, db_user=db_user, db_password=db_password)

    routes = br.get_routes_from_address_and_datetime(
        address=address, target_datetime=target_datetime)

    matched_routes = util.longest_match(routes=routes)

    for route in matched_routes:
        print(json.dumps(route, default=util.json_serial_default))
