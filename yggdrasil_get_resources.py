#!/usr/bin/env python3
"""
Yggdrasil Resources Parser

A tool for extracting and structuring Yggdrasil Network services information
from the official documentation repository. The script clones the repository,
parses services.md file, and converts it to structured JSON format.
"""

import subprocess
import logging
import os
import sys
from dataclasses import dataclass
import json
import argparse
import re
import tempfile

# Logging configuration
_log_format = f"%(name)s [%(asctime)s] %(message)s"

def get_logger(name: str) -> logging.Logger:
    """
    Configure and return a logger with the specified name.
    
    Args:
        name (str): Logger name
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(logging.Formatter(_log_format))
    logger.addHandler(stream_handler)
    return logger

# Global logger instance
logger = get_logger("YGR")

@dataclass(frozen=True)
class Settings:
    """
    Application settings configuration.
    
    Attributes:
        verbose (bool): Enable verbose logging
        filter (str): Resource filter (not implemented)
        export_json (str): JSON export file path
        git_repo_url (str): Git repository URL for Yggdrasil documentation
    """
    verbose: bool = False
    filter: str = ""
    export_json: str = ""
    git_repo_url: str = "https://github.com/yggdrasil-network/yggdrasil-network.github.io"

# Global settings instance
settings = Settings()

def get_resources_md_from_git() -> dict | None:
    """
    Clone Git repository and extract services information.
    
    Returns:
        dict | None: Structured services data or None if error occurred
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = os.path.join(tmpdir, "yggdrasil-repo")
        commands = ['git', 'clone', '--quiet', '--depth', '1', settings.git_repo_url, repo_path]
        
        # Execute git clone command
        result = subprocess.run(commands, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("Git clone failed: %s", result.stderr)
            return None
        
        # Verify services.md file exists
        services_path = os.path.join(repo_path, "services.md")
        if not os.path.exists(services_path):
            logger.error("services.md not found")
            return None
            
        return parse_services_file(services_path)

def parse_services_file(file_path: str) -> dict:
    """
    Parse services.md file and extract structured data.
    
    The function processes Markdown headings and lists to build a hierarchical
    structure. Special handling is provided for Tor bridges section.
    
    Args:
        file_path (str): Path to services.md file
        
    Returns:
        dict: Hierarchical structure of services data
    """
    resources: dict = {}
    with open(file_path, "r", encoding='UTF-8') as file:
        # Stack to track current position in the resource tree
        res_tree = [resources]
        name = ""
        
        for line in file:
            # Process different heading levels and list items
            m = re.match(r"# (.*)", line)
            if m:
                # Level 1 heading - reset to root and create new section
                assert len(res_tree) >= 1
                res_tree = res_tree[:1]
                name = m.group(1)
                res_tree[-1][name] = {}
                res_tree.append(res_tree[-1][name])
                continue
                
            m = re.match(r"## (.*)", line)
            if m:
                # Level 2 heading - reset to level 1 and create subsection
                assert len(res_tree) >= 2
                name = m.group(1)
                res_tree = res_tree[:2]
                res_tree[-1][name] = {}
                res_tree.append(res_tree[-1][name])
                continue
                
            m = re.match(r"### (.*)", line)
            if m:
                # Level 3 heading - reset to level 2 and create list container
                assert len(res_tree) >= 3
                res_tree = res_tree[:3]
                name = m.group(1)
                res_tree[-1][name] = []
                res_tree.append(res_tree[-1][name])
                continue
                
            # Special parsing for Tor bridges list items
            if name == "Tor bridges":
                assert len(res_tree) >= 4  # Should be in list context
                
                # Match the entire line to extract content before and after "operated by"
                # This regex captures everything between backticks and the operator
                m = re.match(r"- (.+?) operated by (.+)", line)
                if m:
                    # Extract the main content (between backticks) and operator
                    content_between_backticks = m.group(1)  # Contains addresses and parameters
                    operator = m.group(2)  # Operator name

                    address_parts = re.split(r'\s+or\s+', content_between_backticks)
                    
                    # Process each address part
                    for address_part in address_parts:
                        m = re.match(r"`(\S*)\s?(\[[\da-f:]+\]:\d+) (.+)`", address_part)
                        if m:
                            tor_bridge = {
                                "prefix": m.group(1),
                                "address": m.group(2),
                                "postfix": m.group(3),
                                "operated": operator
                            }

                            assert isinstance(res_tree[-1], list)
                            res_tree[-1].append(tor_bridge)  # Add bridge to the current list
                    
    return resources

def get_arguments() -> argparse.Namespace:
    """
    Parse and return command line arguments.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Extract Yggdrasil Network services information from documentation repository'
    )
    parser.add_argument('--filter', dest='filter', metavar='FILTER',
        type=str, default="", help='Filter for resources (not implemented)')
    parser.add_argument('--export-json', dest='export_json', metavar='EXPJSON',
        type=str, default="", help='JSON file to export data to')
    parser.add_argument('--repo-url', dest='repo_url', metavar='REPO_URL',
        type=str, default="https://github.com/yggdrasil-network/yggdrasil-network.github.io",
        help='Custom repository URL with services documentation')
    parser.add_argument("-v", dest='verbose', help="Enable verbose logging",
        action="store_true")
    return parser.parse_args()

def validate_settings(args: argparse.Namespace) -> bool:
    """
    Validate application settings and update global settings.
    
    Args:
        args (argparse.Namespace): Command line arguments
        
    Returns:
        bool: True if settings are valid, False otherwise
    """
    global settings
    settings = Settings(
        verbose=args.verbose,
        filter=args.filter,
        export_json=args.export_json,
        git_repo_url=args.repo_url
    )
    
    # Validate export directory permissions
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
    """Set logger level based on verbose setting."""
    if settings.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

def main() -> None:
    """Main application entry point."""
    # Parse and validate command line arguments
    args = get_arguments()
    if not validate_settings(args):
        sys.exit(1)
        
    set_logger_level()
    
    # Extract resources data from Git repository
    logger.debug("Fetching resources from Git repository...")
    resources = get_resources_md_from_git()
    
    if resources is None:
        logger.error("Failed to extract resources data")
        sys.exit(1)
        
    # Output results
    if settings.export_json:
        # Save to JSON file
        with open(settings.export_json, "w", encoding='utf-8') as json_file:
            json.dump(resources, json_file, indent=4)
        logger.info("Data exported to: %s", settings.export_json)
    else:
        # Print to console
        print("==== JSON BEGIN ====")
        print(json.dumps(resources, indent=4))
        print("==== JSON END ====")
        
    sys.exit(0)

if __name__ == '__main__':
    main()