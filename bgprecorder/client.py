from datetime import datetime
import argparse
import json
import bgprecorder


def get_args():
    parser = argparse.ArgumentParser(
        description='This is sample argparse script')
    parser.add_argument('-a', '--address', type=str,
                        help='target address', required=True)
    parser.add_argument('-d', '--datetime', default=None, type=str,
                        help=f'target datetime. example: "200601021504"')
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()

    address = args.address
    if not args.datetime:
        dt = datetime.now()
    else:
        dt = datetime.strptime(args.datetime, bgprecorder.DATETIME_FORMAT)

    routes = bgprecorder.get_routes_from_address_and_datetime(
        address=address, target_datetime=dt)
    matched_routes = bgprecorder.longest_match(routes)
    for route in matched_routes:
        print(json.dumps(route, default=bgprecorder.json_serial_default))
