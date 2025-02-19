#!/usr/bin/python3.12
__author__ = "Jonathan Conwell"
__date__ = "1/26/2025"
__version__ = "2.0.0"
__maintainer__ = "Jonathan Conwell"
__email__ = "jconwell3115@gmail.com"
__status__ = "Development"
__docformat__ = 'reStructuredText'


import argparse
import csv
import fileinput
import json
import os
import signal
import time
import logging
from datetime import datetime


try:
    """Try to import non-standard libraries, send a list of missing libraries if any aren't installed."""
    from jinja2 import Environment, FileSystemLoader
    from termcolor import cprint

except ImportError as ie:
    mod_list = ['jinja2 import Environment, FileSystemLoader', 'from termcolor import cprint']

    print(ie)
    print('Please ensure the following modules are imported to the environment you are running python from before '
          'trying to run the program again.\n')
    print('Non-Standard Module List: ')
    for mod in mod_list:
        print(mod)
    input('\nPress any key to exit the program.')  # This keeps the window open when running the program outside the IDE
    exit()


class ConfigGenerator:
    """
    This class reads information from an old Cisco IOS or IOS-XE router or switch configuration and creates a new
    configuration based on site specific configurations and Agency standard baseline configurations.

    ========
    Methods
    ========
    read_old_config()
        Reads the old configuration file and extracts unique information for use in the new configuration.

    read_templates_and_set_conditions()
        This method reads the base jinja2 template into the variable ``data`` and modifies it to set the dictionary
        conditions prior to the template rendering, as well as insert all the block configuration.

    create_new_config()
        This method renders the new configuration template, outputs that to a new configuration file and then moves the
        new configuration template to a new folder outside of the project templates folder.

    ===========
    Attributes
    ===========
    :var str self.current_date: Date for use in output file naming
    :var str self.project_path: File path to the project
    :var str self.template_path: File path to the templates for the project
    :var str self.old_config_file: Input from user, is the file name of the old configuration file
    :var str self.old_config: Full file path and file name of the old configuration file
    :var str self.new_config:  File path to store the new configuration file later
    :var str self.new_config_template: Empty string, will be used to store the new config template created later
    :var dict self.parameters_dict: Dictionary that will be used to compile the dictionaries generated from the
        information gathering
    :var dict self.template_conditions: Dictionary for items that'll be used to set the conditions in the jinja2
        template prior to rendering
    :var dict self.switch_type_dict: Dictionary to store the switch type, used for conditionals in the program
    :var str self.vlan_priority: String to store block configuration for all VLAN priorities if they exist
    :var str self.interfaces: String to store block configuration for all configured interfaces
    :var str self.router_config: String to store block configuration for all router instances if they exist
    :var str self.ip_route: String to store block configuration for all configured static routes if they exist
    :var str self.logging: String to store block configuration for all logging statements
    :var str self.rp_address: String to store block configuration for all rp-address statements if they exist
    :var list self.base_config_dict_list: List of dictionaries used to render new base configs from CSV rows.
    """

    def __init__(self):
        """
        """

        self.current_date = datetime.now().strftime('%Y_%m_%d')
        self.project_path = r'Place_Holder for now'
        self.template_path = os.path.join(self.project_path, r'Templates')
        self.old_config_file = ''
        self.old_config = ''
        self.switch_template = os.path.join(self.template_path,  r'Switch_template.j2')
        self.new_config = os.path.join(self.project_path, r'Configurations\New')  # Set the path for new config
        self.new_config_template = ''
        self.parameters_dict = {}
        self.template_conditions = {}
        self.switch_type_dict = {'$switch_type': ''}
        self.site_prefix_dict = {'S1': 'site_1', 'S2': 'site_2', 'S3': 'Site_3'}
        self.site_dict = {'$site': ''}
        self.vlan_priority = ''
        self.interfaces = ''
        self.router_config = ''
        self.ip_route = ''
        self.logging = ''
        self.rp_address = ''
        self.base_config_dict_list = []

    def read_old_config(self):
        """Reads the old configuration file and extracts unique information for use in the new configuration.

        =========
        Variables
        =========

        ``:var dict site_dict:`` The site parameter used for conditions in site specific template selection\n
        ``:var dict hostname_dict:`` The hostname of the switch\n
        ``:var dict vlan_dict:`` The VLAN database\n
        ``:var dict source_interface_dict:`` The source interface for network services\n
        ``:var dict location_dict:`` The building and room number for SNMP lookup\n
        ``:var dict mtu_dict:`` The system MTU if it's configured in the old configuration\n
        ``:var dict gateway_dict:`` The default gateway if it's configured in the old configuration\n
        ``:var dict ecn_dict:`` Input from the user for the new switch ECN number\n
        ``:var lst dict_list:`` The list of all the dictionaries to use to update the ``self.parameters_dict`` for ease
        of rendering the jinja2 template\n
        ``:var lst condition_dict_list:`` List of dictionary objects used to set the template conditions prior to
        rendering\n
        ``:var lst access_switch_prefix_list:`` Prefixes used to determine if the switch is access layer

        :raise FileNotFoundError: If the filename is incorrect or file not being present in the correct folder.
        :except PermissionError: If the file is open

        :returns: **[dict, list, str]** Several different data stores with dictionaries, lists and strings of configuration
        extracted from the old switch configuration
        :rtype: dict
        :rtype: lst
        :rtype: str

        """
        self.old_config_file = str(input('What is the filename of the old config file that you want to upgrade? '
                                         '(Include the extension) '))
        self.old_config = os.path.join(self.project_path, r'Configurations\Old', self.old_config_file)
        hostname_dict = {'hostname': ''}
        vlan_dict = {'vlans': {}}
        source_interface_dict = {'source_interface': ''}
        location_dict = {'building': '', 'room': ''}
        mtu_dict = {'mtu': ''}
        gateway_dict = {'gateway': ''}
        ecn_dict = {'chassis_id': input('What is the ECN of the replacement switch? ')}
        # Turn into instance variable and remove dictionary names, append dictionaries to the list from each method
        dict_list = [hostname_dict, vlan_dict, source_interface_dict, location_dict, ecn_dict]  
        condition_dict_list = [self.site_dict, self.switch_type_dict]
        access_switch_prefix_list = ['AS', 'SE', 'EN']

        cprint('\nReading Old Configuration ...\n', 'blue', attrs=['bold'], force_color=True)
        time.sleep(.2)
        # TODO: Open the file and save to variable for iteration in it's own method
        try:
            with (open(self.old_config, 'r') as old_config):
                for line in old_config:
                    if line.startswith('hostname'):
                        cprint('Getting the hostname ...\n', 'light_cyan', force_color=True)
                        time.sleep(.1)
                        hostname_list = line.split(' ')  # Create a new list split on blank spaces
                        hostname_dict['hostname'] = hostname_list[1].replace('\n', '').upper()
                        site_prefix = hostname_dict['hostname'][:2]  # Get the prefix from the hostname
                        if site_prefix.upper() in self.site_prefix_dict:
                            cprint('Getting the site from the hostname ...\n', 'light_cyan', force_color=True)
                            self.site_dict['$site'] = self.site_prefix_dict[site_prefix.upper()]  # Use prefix as site variable
                            cprint('This switch will be configured for the ' + self.site_dict['$site'] + ' site!!\n',
                                   'red', attrs=['bold'], force_color=True)
                            time.sleep(.1)
                        cprint('Setting the location from the hostname ...\n', 'light_cyan', force_color=True)
                        time.sleep(.1)
                        location_list = hostname_dict['hostname'].split('-')  # Split the hostname to get location
                        location_dict['building'] = location_list[2]  # Set building number from hostname
                        location_dict['room'] = location_list[3]  # Set room number from hostname
                        switch_type_prefix = location_list[1]
                        if switch_type_prefix.upper() in access_switch_prefix_list:  # Set switch type from the prefix
                            self.switch_type_dict['$switch_type'] = 'access'
                        else:
                            self.switch_type_dict['$switch_type'] = 'router'
                    # TODO: Split here for VLAN Method
                    elif line.startswith('spanning-tree vlan'):  # Get spanning-tree vlan priorities if they exist
                        self.vlan_priority = line
                    elif line.startswith('vlan'):  # Get VLAN database information
                        vlan_list = line.split(' ')
                        vlan_id = vlan_list[1].replace('\n', '')
                        vlan_dict['vlans'].setdefault(vlan_id, {})
                        for vlan in old_config:
                            if vlan.startswith(' name'):
                                vlan_name_list = vlan.split(' ')
                                vlan_dict['vlans'][vlan_id]['name'] = vlan_name_list[-1].replace('\n', '')
                            elif vlan.startswith('!'):
                                break
                    # TODO: Split here for interface method
                    elif line.startswith('interface'):  # Copy the interface configurations
                        interfaces = ''
                        interfaces += line  # First Line is the interface name
                        for interface in old_config:
                            if '!' in interface:  # Stop copying lines at the !
                                interfaces += '!\n'
                                break
                            else:
                                interfaces += interface

                        # Set the standard SVI configurations if they don't exist
                        if 'interface Vlan' in interfaces and ' no ip proxy-arp' not in interfaces:
                            interfaces = interfaces.replace('!\n', ' no ip proxy-arp\n no ip redirects\n!\n')
                            # TODO: Add elif for access ports to add standard config and remove duplicates
                            # TODO: Add elif for trunk interfaces to remove native vlans
                        self.interfaces += interfaces
                    # TODO: Split here for router configuration method
                    elif line.startswith('router '):  # Copy all router instances as a block config
                        self.router_config += line
                        for router_config in old_config:
                            if '!' in router_config:
                                self.router_config += '!'
                                break
                            else:
                                self.router_config += router_config
                    elif line.startswith('ip route'):  # Copy all static routes as a block config
                        self.ip_route += line
                    # TODO: Split here for remaining services method
                    elif line.startswith('logging'):  # Copy the logging information as a block config
                        if 'buffered' in line:  # Skip buffered logging config, this will be set by a new standard
                            continue
                        else:
                            self.logging += line

                    # Gather the source interface from the 'tacacs source-interface' command
                    elif line.startswith('ip tacacs source-interface'):
                        source_list = line.split(' ')
                        if source_list[-1] == '\n':
                            del source_list[-1]
                        source_interface_dict['source_interface'] = source_list[-1]
                    elif line.startswith('ip pim rp-address'):  # Copy the rp-address for pim
                        self.rp_address += line
                    elif line.startswith('system mtu'):  # Copy the system MTU if it exists
                        mtu_list = line.split(' ')
                        mtu_dict['mtu'] = mtu_list[-1]
                        dict_list.append(mtu_dict)
                    elif line.startswith('ip default-gateway'):  # Copy the default gateway if it exists
                        default_list = line.split(' ')
                        gateway_dict['gateway'] = default_list[-1]
                        dict_list.append(gateway_dict)
            for dictionary in dict_list:  # Update the parameters_dict with all the gathered dictionaries
                self.parameters_dict.update(dictionary)
            for dictionary in condition_dict_list:  # Update the template_conditions dictionary
                self.template_conditions.update(dictionary)
            self.new_config_template = hostname_dict['hostname'] + '.j2'  # Set the new template name from hostname
            new_config_file = hostname_dict['hostname'] + '_' + self.current_date + '.cfg'
            self.new_config = os.path.join(self.new_config, new_config_file)  # Set the new config file from hostname
            # for key, value in self.parameters_dict.items():
            #     print(f"{key}: {value}")

        except FileNotFoundError:
            print('\n' + self.old_config, 'is not a valid file\nPlease check the filename and try again.\n')
            exit()
        except PermissionError:
            input('Please close the following file.\n\n' + self.old_config + '\n\nPress any key to try again.')
            self.read_old_config()

    def read_templates_and_set_conditions(self):
        """This method reads the base jinja2 template into the variable ``data`` and modifies it to set the dictionary
        conditions prior to the template rendering, as well as insert all the block configuration.

        =========
        Variables
        =========
        ``:var str data:`` The string object from the base switch template

        :return: **str** A new template names with the hostname from the switch
        :rtype: str

        """

        cprint('Copying Master Template and Setting Template Conditions ...\n', 'blue',
               attrs=['bold'], force_color=True)
        time.sleep(.1)
        new_config_template = os.path.join(self.template_path, self.new_config_template)

        # read in Switch_Template.j2 template to write to new template hostname.j2
        with open(self.switch_template, 'r') as master_template, open(new_config_template, 'w') as config_template:
            data = master_template.read()
            for key in self.template_conditions:  # Add the conditions to set the site and switch type
                data = data.replace(key, self.template_conditions[key])
            # Replace variables in the template with block configuration from the old config
            data = data.replace('!!!vlan_priority', self.vlan_priority)
            data = data.replace('!!!Interfaces', self.interfaces)
            data = data.replace('!!!router_config', self.router_config)
            data = data.replace('!!!rp-address', self.rp_address)
            data = data.replace('!!!ip_route', self.ip_route)
            data = data.replace('!!!logging', self.logging)
            config_template.write(data)

    def create_new_config(self):
        """This method renders the new configuration template, outputs that to a new configuration file and then moves the
        new configuration template to a new folder outside of the project templates folder.

        ``:var str source_file:`` New configuration template in the original location\n
        ``:var str destination_file:`` New configuration template in the new location outside the project templates
        folder\n

        :return: **str** New configuration file
        :rtype: str
        """
        cprint('Rendering Templates ....\n', 'blue', attrs=['bold'], force_color=True)
        time.sleep(.1)
        env = Environment(loader=FileSystemLoader(self.template_path))

        # render hostname.j2 template
        switch_config_template = env.get_template(self.new_config_template)
        switch_config = switch_config_template.render(self.parameters_dict)
        with open(self.new_config, 'w') as new_config:
            new_config.write(switch_config)
        source_file = os.path.join(self.template_path, self.new_config_template)
        destination_file = os.path.join(self.template_path, 'New_Templates', self.new_config_template)
        if os.path.exists(destination_file):
            os.remove(destination_file)

        os.rename(source_file, destination_file)

        cprint(f"Configuration file {self.new_config} is created!\n", 'green',
               attrs=['bold'], force_color=True)
        cprint(f"The template file {self.new_config_template} has been moved to {destination_file}!\n",
               'green', attrs=['bold'], force_color=True)

    def read_base_csv(self):
        """

        :return:
        """
        base_csv = input('What is the name of your base CSV file? ')
        full_csv_path = os.path.join(self.project_path, r'CSV_Files', base_csv)
        cprint('Reading Base Config CSV File ....\n', 'blue', attrs=['bold'], force_color=True)
        time.sleep(.1)

        try:
            try:
                with open(full_csv_path, 'r', encoding='utf-8') as csv_file:
                    reader = csv.DictReader(csv_file)
                    for row in reader:
                        self.base_config_dict_list.append(row)
            except UnicodeDecodeError:  # this does not catch txt files
                print("Input file is not a csv file. Please enter a valid csv file.")
                input("Press Enter to continue...")
                exit()
        except FileNotFoundError:
            print("Input CSV file not found. Please input a valid file name.")
            input("Press Enter to continue...")
            exit()

    def write_qip_hostnames(self):
        site_prefix = self.base_config_dict_list[0]['edge_hostname'][:2]  # Get the prefix from the hostname

        if site_prefix.upper() in self.site_prefix_dict:
            cprint('Getting the site from the hostname ...\n', 'light_cyan', force_color=True)
            self.site_dict['$site'] = self.site_prefix_dict[site_prefix.upper()]  # Use prefix as site variable
            cprint('These configurations will be configured for the ' + self.site_dict['$site'] + ' site!!\n',
                   'red', attrs=['bold'], force_color=True)
            time.sleep(.1)
            hostname_file = os.path.join(self.project_path, r'Hostnames', self.site_dict['$site'] + '_hostnames.txt')

            with open(hostname_file, 'w') as h_file:
                for row in self.base_config_dict_list:
                    h_file.write('*' * 79 + '\n')
                    h_file.write(
                        row['edge_interface_addr1'] + '\t-\tP2P-' + row['edge_hostname'].upper() + '-to-' +
                        row['in_hostname'].upper() + '-1\n')
                    h_file.write(
                        row['edge_interface_addr2'] + '\t-\tP2P-' + row['edge_hostname'].upper() + '-to-' +
                        row['in_hostname'].upper() + '-2\n')
                    h_file.write(
                        row['in_interface_addr1'] + '\t-\tP2P-' + row['in_hostname'].upper() + '-to-' +
                        row['edge_hostname'].upper() + '-1\n')
                    h_file.write(
                        row['in_interface_addr2'] + '\t-\tP2P-' + row['in_hostname'].upper() + '-to-' +
                        row['edge_hostname'].upper() + '-2\n\n')

            cprint(f"hostname file {hostname_file} has been created!\n", 'green',
                   attrs=['bold'], force_color=True)

    def create_edge_base_config(self):
        """

        :return:
        """
        base_config_list = ['new', 'replacement']
        base_config_type = input('Is this a new or replacement edge node? ')
        if base_config_type.lower() not in base_config_list:
            print('That is not a valid configuration type.  Please select either "new" or "replacement".')
            create_edge_base_config()

        cprint('Rendering Edge Node Base Config Template ....\n', 'blue', attrs=['bold'], force_color=True)
        time.sleep(.1)
        env = Environment(loader=FileSystemLoader(self.template_path))
        edge_base_config_template = 'SDA_edge_base_config_template.j2'
        in_isis_template = 'in_isis_template.j2'
        edge_template = env.get_template(edge_base_config_template)
        in_template = env.get_template(in_isis_template)
        try:
            for row in self.base_config_dict_list:
                edge_base_config = os.path.join(self.project_path, r'Configurations\Base_Configs',
                                                row['edge_hostname'] + '_base.txt')
                in_isis_config = os.path.join(self.project_path, r'Configurations\Base_Configs',
                                              row['in_hostname'] + '_isis.txt')
                row['in_interface_description'] = (row['in_hostname'].upper() +
                                                   ' To ' + row['edge_hostname'].upper() + ' - Fabric Underlay')
                if base_config_type.lower() == 'new':
                    isis_config = in_template.render(row)
                base_config = edge_template.render(row)
                with open(edge_base_config, 'w') as edge_config, open(in_isis_config, 'a') as in_config:
                    edge_config.write(base_config)
                    in_config.write(isis_config)

                cprint(f"Configuration file {edge_base_config} has been created!\n", 'green',
                       attrs=['bold'], force_color=True)
                cprint(f"Configuration file {in_isis_config} has been created!\n", 'green',
                       attrs=['bold'], force_color=True)

        except FileNotFoundError:
            with open(in_isis_config, 'w') as in_config:
                print(in_config, 'Not found.  Creating a new file. \n')
            create_edge_base_config()

    def create_in_base_config(self):
        """

        :return:
        """
        cprint('Rendering Intermediate Node Base Config Template ....\n', 'blue', attrs=['bold'], force_color=True)
        time.sleep(.1)
        env = Environment(loader=FileSystemLoader(self.template_path))
        in_base_config_template = 'SDA_in_base_config_template.j2'
        bn_isis_template = 'bn_isis_template.j2'
        in_template = env.get_template(in_base_config_template)
        bn_template = env.get_template(bn_isis_template)
        try:
            for row in self.base_config_dict_list:
                in_base_config = os.path.join(self.project_path, r'Configurations\Base_Configs',
                                              row['in_hostname'] + '_base.txt')
                bn1_isis_config = os.path.join(self.project_path, r'Configurations\Base_Configs',
                                               row['bn1_hostname'] + '_isis.txt')
                bn2_isis_config = os.path.join(self.project_path, r'Configurations\Base_Configs',
                                               row['bn2_hostname'] + '_isis.txt')
                in_name_list = row['in_hostname'].split('-')
                bn1_name_list = row['bn1_hostname'].split('-')
                bn2_name_list = row['bn2_hostname'].split('-')
                in_name = "-".join([in_name_list[1], in_name_list[2], in_name_list[-1]]).upper()
                bn1_name = "-".join(bn1_name_list[1:3]).upper()
                bn2_name = "-".join(bn2_name_list[1:3]).upper()
                row['in_interface1_description'] = in_name + '_TO_' + bn1_name + ' - Fabric Underlay'
                row['in_interface2_description'] = in_name + '_TO_' + bn2_name + ' - Fabric Underlay'
                row['bn1_interface_description'] = in_name + '_TO_' + bn1_name + ' - Fabric Underlay'
                row['bn2_interface_description'] = in_name + '_TO_' + bn2_name + ' - Fabric Underlay'
                bn1_title = '*' * 79 + '\n' + row['bn1_hostname'].center(79) + '\n' + '*' * 79
                bn2_title = '*' * 79 + '\n' + row['bn2_hostname'].center(79) + '\n' + '*' * 79

                base_config = in_template.render(row)
                bn_config = bn_template.render(row)
                half = len(bn_config) // 2
                with (open(in_base_config, 'w') as in_config, open(bn1_isis_config, 'a') as bn1_config,
                      open(bn2_isis_config, 'a') as bn2_config):
                    in_config.write(base_config)
                    bn1_config.write(bn1_title)
                    bn1_config.write(bn_config[:half])
                    bn2_config.write(bn2_title)
                    bn2_config.write(bn_config[half:])

                cprint(f"Configuration file {in_base_config} has been created!\n", 'green',
                       attrs=['bold'], force_color=True)
                cprint(f"Configuration file {bn1_isis_config} has been created!\n", 'green',
                       attrs=['bold'], force_color=True)
                cprint(f"Configuration file {bn2_isis_config} has been created!\n", 'green',
                       attrs=['bold'], force_color=True)
        except FileNotFoundError:
            with open(in_isis_config, 'w') as in_config:
                print(in_config, 'Not found.  Creating a new file. \n')
            create_edge_base_config()


def sub_main(args):
    """
    This function controls the flow of the program and calls the methods in the class.

    :param args: Parsed CLI arguments
    :return: None
    """

    cfg = ConfigGenerator()

    while True:
        config_type = input('What configuration do you want to perform? (Type "List" for options.) ')
        config_list = ['whole', 'edge_base', 'in_base']
        if config_type.lower() == 'whole':
            cfg.read_old_config()
            cfg.read_templates_and_set_conditions()
            cfg.create_new_config()
            break
        elif config_type.lower() == 'list' or config_type.lower() not in config_list:
            print('The following configuration types are supported:\n'
                  '"whole"\t-\tfor entire switch configurations\n'
                  '"edge_base"\t-\tFor creating base configurations for SDA Edge Node migrations\n'
                  '"in_base"\t-\tFor creating base configurations for SDA Intermediate Node discovery\n')
            input('Press any key to continue ...\n')
            continue
        else:
            cfg.read_base_csv()
            if config_type.lower() == 'edge_base':
                cfg.create_edge_base_config()
                cfg.write_qip_hostnames()
            else:
                cfg.create_in_base_config()
            break

    input('Press any key to exit the program.')


def main():
    """
    This is the main function and initial entry point into the program.  The command line arguments are set here and
    passed to the sub_main function.  Not all programs use command line arguments, but I leave the code in to allow
    for possible expansion later

    :return: Parsed CLI arguments if there are any
    """

    signal.signal(signal.SIGINT, signal.SIG_DFL)  # KeyboardInterrupt: Ctrl-C
    # Create CLI arguments and descriptions
    parser = argparse.ArgumentParser(description='This program creates new configurations from old configuration files '
                                                 'for Cisco switches')
    args = parser.parse_args()
    sub_main(args)


if __name__ == '__main__':
    main()
