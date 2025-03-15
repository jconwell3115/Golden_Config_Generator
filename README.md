![Static Badge](https://img.shields.io/badge/Stage-Development-orange)
[![GitHub License](https://img.shields.io/github/license/jconwell3115/Golden_Config_Generator?label=License)](https://github.com/jconwell3115/Golden_Config_Generator?tab=MIT-1-ov-file)
![GitHub commit activity](https://img.shields.io/github/commit-activity/w/jconwell3115/Golden_Config_Generator?logo=github)

![IOS-XE Tested](https://img.shields.io/badge/Tested%20IOS--XE-16.9.x%7C17.6.x%7C17.9.x%7C17.12.x-blue?logo=cisco&logoColor=white&logoSize=auto)
[![Python Tested](https://img.shields.io/badge/Tested%20Python-%203.9%7C3.10%7C3.11%7C3.12-blue?logo=python&logoColor=green)](https://www.python.org/downloads/)

[![Jinja Version](https://img.shields.io/badge/Dependancy-Jinja2-red?logo=jinja)](https://pypi.org/project/Jinja2/)

![Pre-Commit](https://img.shields.io/badge/Pre--Commit%20Linters-black?style=for-the-badge&logo=pre-commit&logoSize=auto)

![Ruff Linter](https://img.shields.io/badge/Ruff-Green?logo=ruff&logoSize=auto)
![YAMLLINT](https://img.shields.io/badge/yamllint-Green?logo=yaml&logoSize=auto)
![DJLint](https://img.shields.io/badge/DJLint-Green?logo=jinja&logoSize=auto)
![TrufflHog](https://img.shields.io/badge/Trufflehog-Green?logo=grunt&logoColor=white&logoSize=auto)









# Golden_Config_Generator
> This program reads in the configuration file from a Cisco router or switch running IOS-XE extracts the unique 
> information and inserts it into a new configuration at designated locations. 
> 
> This new configuration is then rendered with a Jinja template with site specific configuration parameters and a 
> golden configuration Jinja template that consists of best practice configurations standard across all site.

## Use Case
This program was developed to meet the need to upgrade switch configurations during platform upgrades using the latest 
industry best practices and enterprise security standards in an automated fashion.

---
## Features
- Leverages Jinja templating in a .j2 template per site with macros for config blocks like DNS, SNMP, etc.
- Certain unique configurations are extracted as unstructured code blocks, such as interface configurations and routing 
  configurations.
   - These configurations are currently just pasted into the new configuration at set locations in the config 
     designated by `!!![config_name]!!!`. 
     - i.e `!!!Interfaces` is used to designate where the interface configuration goes.
   - These copied configurations should be peer-reviewed for relevance and application to the new platform. 
     Specifically interfaces names might change, VLANs might no longer be needed, etc.
   - **_Future releases will include parsers for these configurations for easier transfer to the new configuration_**

## Installation

**[Step 1] Clone repo:**
```bash
git clone git@github.com:jconwell3115/Golden_Config_Generator.git
```

**[Step 2] Navigate to the project directory**
```bash
cd Golden_Config_Generator
```

**[Step 3] Install required dependencies:**
```bash
pip install -r requirements.txt
```

**[Step 4] Install [pre-commit](https://pre-commit.com/index.html#intro):**
```bash
pre-commit install
```

## Usage
```plain
(GoldenConfigGenerator) jconw483@Jons-PC ~/Work_Environments/GoldenConfigGenerator/Golden_Config_Generator $ python3 golden_config_generator.py -h
usage: golden_config_generator.py [-h] [-c CONFIG]

This program reads in an old configuration file and then converts it to a new 'golden' 
configuration using industry standard best practices for Cisco Catalyst switches running 
IOS-XE versions 16.9 and up.

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Configuration file to convert

Thanks for using golden_config_generator!
```
> This program can be ran with the `-c {{ switch_config }}` or with no argument. If run 
> with no 
> argument the program will ask for the name of the switch configuration
> 
>> **_Future release will include the option to convert all configurations in a given 
> directory._**
> 
**Run the program on the test configurations for proof of concept:**

_Sample configurations files are located in the `configuration_files/old_configurations` directory._


```bash
(.venv) $ golden_config_generator.py -c S1-AS-3320-104-1.cfg
```
_This will output the new configurations in the `configuration_files/new_configurations` directory._

_There will be a template rendered with the `{{ hostname }}.j2` located in the 
`templates/new_switch_templates` directory_

---
## Directory Structure
```bash
.
├── configuration_files
│   ├── new_configurations
│   │   ├── S1-AS-3320-104-1_2025_03_14.cfg
│   │   └── S3-CS-2015-321-1_2025_03_14.cfg
│   └── old_configurations
│       ├── S1-AS-3320-104-1.cfg
│       ├── S2-AS-527-109-1.cfg
│       └── S3-CS-2015-321-1.cfg
├── golden_config_generator.py
├── LICENSE
├── pipdeptree_current.txt
├── pyproject.toml
├── README.md
├── requirements.txt
└── templates
    ├── new_switch_templates
    │   ├── S1-AS-3320-104-1.j2
    │   └── S3-CS-2015-321-1.j2
    ├── site_1.j2
    ├── site_2.j2
    ├── site_3.j2
    └── switch_template.j2
    
```
- **configuration_files** - Directory to store old and new configurations
  
  - **new_configurations** - Directory that holds the new golden configs created by the 
    program
  -  **old_configurations** - Directory that the program searches for the 
     configurations to be converted
- **templates** - Directory that stores the site specific templates and the base 
  golden config switch template
  - **new_switch_templates** - These are the templates created during the program run, 
    these aren't really needed, but are good reference to see the workflow.

---

## Possible Automation Enhancements
> This is a general idea and the details would need to be defined a bit more
- Create Ansible Playbook that orchestrates the following
  
  1. Login to a live network device and gather the configuration.
  2. Save the file locally and to the flash on the network device.
  3. Copy the configuration to flash:[hostname]_automated_reconfigure.cfg.
  4. Run the configuration through the golden_config_generator.py program to generate a new configuration.
  5. Copy the new configuration to the live network device
  6. Create an eem script that will copy the new configuration into startup and reload the device.
     - **The EEM script needs to be in the new configuration as well.**
  7. The EEM script will run checkouts after the reboot to ensure everything is working fine, else it will revert the 
     configuration to the old config and reload again.

---
## TODO:
- ~~Add Jinja tempaltes for sites~~
- ~~Add base configuration template~~
- ~~Modularize the code into smaller methods~~
- ~~Add generic old configuration files for testing and proof of concept~~
- ~~CLI arguments to take the file name~~
- Add a CLI switch to read and convert all files in a given directory

## Author
>[Jonathan Conwell](https://github.com/jconwell3115)
>
>Email: `jconwell3115@gmail.com`
> 
>Phone: [867-5309](https://youtu.be/6WTdTwcmxyo?si=v07HrJN91Ezz9KMs)

#### DISCLAIMER

<b>Please note:</b> This script is meant for demo purposes only. All tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.
