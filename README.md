# Yggdrasil Resources Parser

A Python tool for extracting and structuring Yggdrasil Network services information from the official documentation repository.

## Description

This project is a python script for get [YGGDRASIL](https://yggdrasil-network.github.io/) resources.

It takes list of all resources from [yggdrasil-network.github.io repository](https://github.com/yggdrasil-network/yggdrasil-network.github.io) and filters it according to some criteria.

This script automatically clones the Yggdrasil Network repository, parses the *services.md* file, and converts it into structured JSON format. Special attention is paid to correctly extracting Tor bridges information. At the moment, only Tor bridges are parsed. Any help is welcome!

## Requirements

 - Python 3.7+
 - Git (must be available in PATH)
 - Internet connection for repository cloning

## Installation
```bash
git clone <repository>
cd <project_folder>
# Make sure Python 3.7+ is installed
```

## Usage

### Basic usage (console output)
```bash
python yggdrasil_parser.py
```

### Save to JSON file
```bash
python yggdrasil_parser.py --export-json services.json
```

### Verbose output with logs
```bash
python yggdrasil_parser.py -v --export-json services.json
```

### Using custom repository
```bash
python yggdrasil_parser.py --repo-url https://github.com/your-fork/yggdrasil-network.github.io
```

### All parameters
```bash
python yggdrasil_parser.py --help
```

## Output Examples

### Console Output
```text
==== JSON BEGIN ====
{
    "Services": {
        "Proxy services": {
            "Tor bridges": [
                {
                    "prefix": "",
                    "address": "[220:0000:0000:0000:0000:0000:0000:1111]:1111",
                    "postfix": "1111111111111111111111111111111111111111",
                    "operated": "Foo"
                },
                {
                    "prefix": "obfs4",
                    "address": "[220:0000:0000:0000:0000:0000:0000:2222]:2222",
                    "postfix": "2222222222222222222222222222222222222222",
                    "operated": "Bar"
                }
            ]
        }
    }
}
==== JSON END ====
```

## Data Structure

The program creates a tree structure based on Markdown headings:

 - # - root level;
 - ## - second level;
 - ### - third level (list items);

## Implementation Features

 - Temporary Cloning: Repository is cloned to a temporary directory and automatically deleted after processing.
 - Strong Typing: Uses dataclasses for data structuring.
 - Flexibility: Supports custom repository URLs.
 - Logging: Detailed process logging for debugging.

## Limitations

 - The --filter parameter is not implemented in the current version.
 - Only supports specific Tor bridges list format.
 - Requires Git installed on the system.

## Use Cases

The extracted data can be used for:

 - automatic Yggdrasil client configuration;
 - service availability monitoring;
 - Yggdrasil Network infrastructure analysis;
 - integration with other tools via JSON API.