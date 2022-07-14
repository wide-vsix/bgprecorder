from datetime import datetime, date
import ipaddress
import subprocess

import glob
import pathlib

from .bgprecorder import BgpRecorder

'''



New Util


'''


def json_serial_default(obj):
    # 日付型の場合には、文字列に変換します
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    # 上記以外はサポート対象外.
    raise TypeError("Type %s not serializable" % type(obj))


def longest_match(routes: list) -> list:
    longest_prefix = 0
    for route in routes:
        prefixlen = ipaddress.ip_network(route["nlri"]).prefixlen
        if prefixlen >= longest_prefix:
            longest_prefix = prefixlen
    return [route for route in routes if ipaddress.ip_network(route["nlri"]).prefixlen == longest_prefix]


def localExec(cmd):
    proc = subprocess.run(
        cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc.returncode == 0


def localExecCaptureOutput(cmd):
    proc = subprocess.run(
        cmd, shell=True, capture_output=True, text=True)
    return proc.stdout


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


def parse_bgpdump_record_to_route_obj(bgpdump_record: str) -> dict:
    params = bgpdump_record.split("|")
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


def get_files(match_rule: str) -> list:
    files = glob.glob(f"{match_rule}")
    return files


def get_table_name_from_file_path(file_path: str) -> str:
    prefix = BgpRecorder.table_name_prefix
    table_name_origin = pathlib.Path(
        file_path).stem.replace('bz2', '').replace('.', '').replace('dump', '')  # TODO refine
    return prefix + table_name_origin
