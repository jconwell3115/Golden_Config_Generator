![Static Badge](https://img.shields.io/badge/Stage-Development-orange)
![Static Badge](https://img.shields.io/badge/Tested%20Python-%203.9%7C3.10%7C3.11%7C3.12-blue?logo=python&logoColor=green&link=https%3A%2F%2Fwww.python.org%2Fdownloads%2F)
![GitHub License](https://img.shields.io/github/license/jconwell3115/Golden_Config_Generator?label=License&link=https%3A%2F%2Fgithub.com%2Fjconwell3115%2FGolden_Config_Generator)

# Golden_Config_Generator
> This program takes the configuration file from a Cisco router or switch running IOS-XE extracts the unique information and inserts it into a new configuration using a golden configuration template.
> 
> This was developed to meet the need to upgrade switch configurations during platform upgrades using the latest industry best practices and enterprise security standards.
---
## Features
- Leverages Jinja templating in a single .j2 file per site with macros for config blocks like DNS, SNMP, etc.
- Certain unique configurations are extracted as code blocks, such as interface configurations and routing configurations.
   > These configurations will need to be reviewed for relevance and applicaiton to the new platform.
   > 
   >> **_Future releases will include parsers for these configrurations_**


