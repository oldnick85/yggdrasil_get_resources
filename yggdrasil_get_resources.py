import subprocess
import logging
import os
import shutil
import sys
from dataclasses import dataclass
import json
import argparse
import re

_log_format = f"%(name)s [%(asctime)s] %(message)s"

def get_logger(name : str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(logging.Formatter(_log_format))
    logger.addHandler(stream_handler)
    return logger

logger = get_logger("YGR")

@dataclass(frozen=True)
class Settings:
    filter : str = ""
    export_json : str = ""

@dataclass(frozen=True)
class Resource:
    address : str
    url : str
    
    def __str__(self) -> str:
        s = f"{self.address}"
        return s
    
def get_resources_md_from_git() -> dict[str, str]:
    resources : dict[str, str] = {}
    commands = f'git clone --quiet --depth 1 "https://github.com/yggdrasil-network/yggdrasil-network.github.io"'
    current_dir = os.getcwd()
    os.chdir("/tmp")
    process = subprocess.Popen(commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    if (process.poll() != 0):
        logger.info("git clone error")
        return resources
    os.chdir("yggdrasil-network.github.io")
    try:
        with open("services.md", "r", encoding='UTF-8') as file:
            name1 = None
            lvl1 = None
            name2 = None
            lvl2 = None
            name3 = None
            lvl3 = None
            for line in file:
                m = re.match(r"# (.*)", line)
                if (m):
                    name1 = m.group(1)
                    resources[name1] = {}
                    lvl1 = resources[name1]
                    name2 = None
                    lvl2 = None
                    name3 = None
                    lvl3 = None
                    continue
                m = re.match(r"## (.*)", line)
                if (m):
                    name2 = m.group(1)
                    lvl1[name2] = {}
                    lvl2 = lvl1[name2]
                    name3 = None
                    lvl3 = None
                    continue
                m = re.match(r"### (.*)", line)
                if (m):
                    name3 = m.group(1)
                    lvl2[name3] = []
                    lvl3 = lvl2[name3]
                    continue
                if (name3 == "Tor bridges"):
                    m = re.match(r"- `(\S*)\s?(\[[\da-f:]+\]:\d+) (.+)` operated by (.+)", line)
                    if (m):
                        tor_bridge = {}
                        tor_bridge["prefix"] = m.group(1)
                        tor_bridge["address"] = m.group(2)
                        tor_bridge["postfix"] = m.group(3)
                        tor_bridge["operated"] = m.group(4)
                        lvl3.append(tor_bridge)
    finally:
        os.chdir("..")
        shutil.rmtree("yggdrasil-network.github.io")
        os.chdir(current_dir)
    return resources

def get_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Find yggdrasil public peers')
    parser.add_argument('--filter', dest='filter', metavar='FILTER', \
        type=str, default="", help='FIlter for resoerces')
    parser.add_argument('--export-json', dest='export_json', metavar='EXPJSON', \
        type=str, default="", help='Json file export to')
    parser.add_argument("-v", dest='verbose', help="Print extra logs",
        action="store_true")
    return parser.parse_args()

def set_logger_level(args : argparse.Namespace) -> None:
    if (args.verbose):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    return

def main() -> None:
    args = get_arguments()

    set_logger_level(args)

    settings = Settings(filter=args.filter, \
                        export_json=args.export_json)
    
    resources = get_resources_md_from_git()
    if (settings.export_json):
        with open(settings.export_json, "w") as json_file:
            json_file.write(json.dumps(resources, indent=4))
    else:
        print(f"==== JSON BEGIN ====")
        print(json.dumps(resources, indent=4))
        print(f"==== JSON END ====")
    sys.exit(0)

if __name__ == '__main__':
    main()