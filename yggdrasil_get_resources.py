import subprocess
import logging
import os
import sys
from dataclasses import dataclass
import json
import argparse
import re
import tempfile

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
    verbose : bool = False
    filter : str = ""
    export_json : str = ""
    git_repo_url : str = "https://github.com/yggdrasil-network/yggdrasil-network.github.io"

settings = Settings()

@dataclass(frozen=True)
class TorBridge:
    prefix : str = ""
    address : str = ""
    postfix : str = ""
    operated : str = ""
    
    def to_dict(self) -> dict:
        return {
            "prefix" : self.prefix,
            "address" : self.address,
            "postfix" : self.postfix,
            "operated" : self.operated,
        }
    
def get_resources_md_from_git() -> dict | None:
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = os.path.join(tmpdir, "yggdrasil-repo")
        commands = ['git', 'clone', '--quiet', '--depth', '1', settings.git_repo_url, repo_path]
        
        result = subprocess.run(commands, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("Git clone failed: %s", result.stderr)
            return None
        
        services_path = os.path.join(repo_path, "services.md")
        if not os.path.exists(services_path):
            logger.error("services.md not found")
            return None
            
        return parse_services_file(services_path)
    
def parse_services_file(file_path: str) -> dict:
    resources : dict = {}
    with open(file_path, "r", encoding='UTF-8') as file:
        res_tree = [resources]
        name = ""
        for line in file:
            m = re.match(r"# (.*)", line)
            if (m):
                assert(len(res_tree) >= 1)
                res_tree = res_tree[:1]
                name = m.group(1)
                res_tree[-1][name] = {}
                res_tree.append(res_tree[-1][name])
                continue
            m = re.match(r"## (.*)", line)
            if (m):
                assert(len(res_tree) >= 2)
                name = m.group(1)
                res_tree = res_tree[:2]
                name = m.group(1)
                res_tree[-1][name] = {}
                res_tree.append(res_tree[-1][name])
                continue
            m = re.match(r"### (.*)", line)
            if (m):
                assert(len(res_tree) >= 3)
                res_tree = res_tree[:3]
                name = m.group(1)
                res_tree[-1][name] = []
                res_tree.append(res_tree[-1][name])
                continue
            if (name == "Tor bridges"):
                assert(len(res_tree) >= 4)
                m = re.match(r"- `(\S*)\s?(\[[\da-f:]+\]:\d+) (.+)` operated by (.+)", line)
                if (m):
                    tor_bridge = {}
                    tor_bridge["prefix"] = m.group(1)
                    tor_bridge["address"] = m.group(2)
                    tor_bridge["postfix"] = m.group(3)
                    tor_bridge["operated"] = m.group(4)
                    assert(type(res_tree[-1]) == list)
                    res_tree[-1].append(tor_bridge)
    return resources

def get_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Find yggdrasil public peers')
    parser.add_argument('--filter', dest='filter', metavar='FILTER', \
        type=str, default="", help='Filter for resources')
    parser.add_argument('--export-json', dest='export_json', metavar='EXPJSON', \
        type=str, default="", help='Json file export to')
    parser.add_argument('--repo-url', dest='repo_url', metavar='REPO_URL', \
        type=str, default="https://github.com/yggdrasil-network/yggdrasil-network.github.io", help='Repository with resources file')
    parser.add_argument("-v", dest='verbose', help="Print extra logs",
        action="store_true")
    return parser.parse_args()

def validate_settings(args: argparse.Namespace) -> bool:
    global settings
    settings = Settings(verbose=args.verbose, \
                filter=args.filter, \
                export_json=args.export_json, \
                git_repo_url=args.repo_url)
    
    if settings.export_json:
        export_dir = os.path.dirname(settings.export_json) or '.'
        if not os.path.exists(export_dir):
            logger.error("Export directory does not exist: %s", export_dir)
            return False
            
        if not os.access(export_dir, os.W_OK):
            logger.error("No write permission for directory: %s", export_dir)
            return False
    
    return True

def set_logger_level() -> None:
    if (settings.verbose):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    return

def main() -> None:
    args = get_arguments()
    if (not validate_settings(args)):
        sys.exit(1)
    set_logger_level()
    
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