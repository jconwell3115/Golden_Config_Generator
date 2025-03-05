![Static Badge](https://img.shields.io/badge/Stage-Development-orange)
[![GitHub License](https://img.shields.io/github/license/jconwell3115/Golden_Config_Generator?label=License)](https://github.com/jconwell3115/Golden_Config_Generator?tab=MIT-1-ov-file)
![GitHub commit activity](https://img.shields.io/github/commit-activity/w/jconwell3115/Golden_Config_Generator?logo=github)

![IOS-XE Tested](https://img.shields.io/badge/Tested%20IOS--XE-16.9.x%7C17.6.x%7C17.9.x%7C17.12.x-blue?logo=cisco&logoColor=white&logoSize=auto)
[![Python Tested](https://img.shields.io/badge/Tested%20Python-%203.9%7C3.10%7C3.11%7C3.12-blue?logo=python&logoColor=green)](https://www.python.org/downloads/)

[![Jinja Version](https://img.shields.io/badge/Dependancy-Jinja2%3D%3D3.1.5-red?logo=jinja)](https://pypi.org/project/Jinja2/)




# Golden_Config_Generator
> This program reads in the configuration file from a Cisco router or switch running IOS-XE extracts the unique 
> information
> and inserts it into a new configuration using a golden configuration template.

## Use Case
This program was developed to meet the need to upgrade switch configurations during platform upgrades using the latest 
industry best practices and enterprise security standards.
---
## Features
- Leverages Jinja templating in a single .j2 file per site with macros for config blocks like DNS, SNMP, etc.
- Certain unique configurations are extracted as code blocks, such as interface configurations and routing configurations.
   > These configurations will need to be reviewed for relevance and application to the new platform.
   > 
   >> **_Future releases will include parsers for these configurations for easier transfer to the new configuration_**

## Usage

This runs from the CLI using the config file names as arguments. You can use one or many names.  
> **_Future release will include the option to convert all configurations in a given directory._**
```bash
(.venv) $ golden_config_generator.py S1-AS-3320-104-1.cfg  # Run on single configuration
(.venv) $ golden_config_generator.py S1-AS-3320-104-1.cfg S2-AS-527-109-1.cfg # Run on multiple configurations.
```
This will output the new configurations in the `configuration_files/new_configurations` folder 

---
## TODO:
- ~~Add Jinja tempaltes for sites~~
- ~~Add base configuration template~~
- ~~Modularize the code into smaller methods~~
- ~~Add generic old configuration files for testing and proof of concept~~
- Add elif for access ports to add standard config and remove duplicates
- CLI arguments to take the file name or names if multiples are desired
- then remove the prompt to ask for file name
- Add switch to read all files in directory
