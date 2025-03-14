#!/usr/bin/python3.12
__author__ = "Jonathan Conwell"
__date__ = "1/26/2025"
__version__ = "2.0.0"
__maintainer__ = "Jonathan Conwell"
__email__ = "jconwell3115@gmail.com"
__status__ = "Development"
__docformat__ = "reStructuredText"

import argparse
import csv
import fileinput
import json
import os
import signal
import sys
import time
import logging
from datetime import datetime


try:
    # Try to import non-standard libraries, send a list of libraries if any aren't
    # installed.
    from jinja2 import Environment, FileSystemLoader
    from termcolor import cprint

except ImportError as ie:
    mod_list = [
        "jinja2 import Environment, FileSystemLoader",
        "from termcolor import cprint",
    ]

    print(ie)
    print(
        "Please ensure the following modules are imported to the environment you are "
        "running python from before trying to run the program again.\n"
    )
    print("Non-Standard Module List: ")
    for mod in mod_list:
        print(mod)
    input(
        "\nPress any key to exit the program."
    )  # This keeps the window open when running the program outside the IDE
    exit()


class ConfigGenerator:
    """
    This class reads information from an old Cisco IOS or IOS-XE router or switch
    configuration and creates a new configuration based on site specific configurations
    and Agency standard baseline configurations.


    Methods
    ========
    read_old_config()
        Reads the old configuration file and extracts unique information for use in the
        new configuration.

    read_templates_and_set_conditions()
        This method reads the base jinja2 template into the variable ``data`` and modifies
         it to set the dictionary conditions prior to the template rendering, as well
         as insert all the block configuration.

    create_new_config()
        This method renders the new configuration template, outputs that to a new
        configuration file and then moves the new configuration template to a new
        folder outside of the project templates folder.


    Attributes
    ===========
    :var str self.current_date: Date for use in output file naming
    :var str self.project_path: File path to the project
    :var str self.template_path: File path to the templates for the project
    :var str self.new_config:  File path to store the new configuration file later
    :var str self.new_config_template: Empty string, will be used to store the new config
    template created later
    :var dict self.parameters_dict: Dictionary that will be used to compile the
    dictionaries generated from the information gathering
    :var dict self.template_conditions: Dictionary for items that'll be used to set the
    conditions in the jinja2 template prior to rendering
    :var dict self.switch_type_dict: Dictionary to store the switch type, used for
    conditionals in the program
    :var str self.vlan_priority: String to store block configuration for all VLAN
    priorities if they exist
    :var str self.interfaces: String to store block configuration for all configured
    interfaces
    :var str self.router_config: String to store block configuration for all router
    instances if they exist
    :var str self.ip_route: String to store block configuration for all configured static
    routes if they exist
    :var str self.logging: String to store block configuration for all logging statements
    :var str self.rp_address: String to store block configuration for all rp-address
    statements if they exist
    :var list self.base_config_dict_list: List of dictionaries used to render new base
    configs from CSV rows.
    """

    def __init__(self):
        """ """

        self.current_date = datetime.now().strftime("%Y_%m_%d")
        # Change this to the path for your project
        self.project_path = (
            "/home/jconw483/Work_Environments/GoldenConfigGenerator/"
            "Golden_Config_Generator/"
        )
        self.template_path = os.path.join(self.project_path, r"Templates")
        self.old_config_list = []
        self.switch_template = os.path.join(self.template_path, r"Switch_template.j2")
        self.new_config = os.path.join(
            self.project_path, r"configuration_files/new_configurations"
        )  # new config path
        self.new_config_template = ""
        self.parameters_dict = {}
        self.template_conditions = {}
        self.switch_type_dict = {"$switch_type": ""}
        self.site_prefix_dict = {"S1": "site_1", "S2": "site_2", "S3": "Site_3"}
        self.site_dict = {"$site": ""}
        self.vlan_priority = ""
        self.interfaces = ""
        self.router_config = ""
        self.ip_route = ""
        self.logging = ""
        self.rp_address = ""
        self.dict_list = []
        self.base_config_dict_list = []

    def read_old_config(self, config: str) -> None:
        """
        Reads the old configuration file and stores it in a variable used by other methods
        to extract information.

        :parameter config: File name to the old configuration file

        :exception FileNotFoundError: If the filename is incorrect or file not being
        present in the correct folder.
        :exception PermissionError: If the file is open or unreadable

        """
        if config.endswith(".cfg"):
            cprint(config + " file submitted ...", "light_green", force_color=True)
        else:
            config = config + ".cfg"

        print(config)

        old_config_file = config
        old_config_path = os.path.join(
            self.project_path,
            r"configuration_files/old_configurations",
            old_config_file,
        )
        cprint(
            "\nReading in Old Configuration ...\n",
            "blue",
            attrs=["bold"],
            force_color=True,
        )
        time.sleep(0.2)
        try:
            with open(old_config_path, "r", encoding="UTF-8") as old_config:
                self.old_config_list = old_config.readlines()
        except FileNotFoundError:
            cprint(
                "A file named " + old_config_file + " was not found!!\n"
                "Please check the filename and try again.\n",
                color="red",
                attrs=["bold"],
                force_color=True,
            )
            sys.exit()
        except PermissionError:
            input(
                "Please close the following file.\n\n"
                + old_config_path
                + "\n\nPress any key to try again."
            )
            self.read_old_config(config=config)

    def get_switch_info(self):
        """

        This method parses the old_config_var and extracts the hostname, from the hostname
        it gathers the site name used to set the Jinja parameters per site later.  It
        also extracts the location for the building and room. These all assume a
        certain naming convention for the network device,
        ``site-switch_type-building-room-instance``.

        Example: S1-EN-3320-104-1

        """
        cprint(
            "\nGathering basic switch information ...\n",
            "blue",
            attrs=["bold"],
            force_color=True,
        )
        time.sleep(0.2)
        site_prefix_dict = {"S1": "site_1", "S2": "site_2", "S3": "Site_3"}

        cprint("Getting the hostname ...\n", "light_cyan", force_color=True)
        time.sleep(0.1)

        hostname_dict = {"hostname": ""}
        location_dict = {"building": "", "room": ""}
        access_switch_prefix_list = ["AS", "SE", "EN"]
        condition_dict_list = [self.site_dict, self.switch_type_dict]

        for line in self.old_config_list:
            if line.startswith("hostname"):
                hostname_list = line.split(" ")  # Create a new list split on blank spaces
                hostname_dict["hostname"] = hostname_list[1].replace("\n", "").upper()
                site_prefix = hostname_dict["hostname"][
                    :2
                ]  # Get the prefix from the hostname
                if site_prefix.upper() in site_prefix_dict:
                    cprint(
                        "Getting the site from the hostname ...\n",
                        "light_cyan",
                        force_color=True,
                    )
                    self.site_dict["$site"] = site_prefix_dict[
                        site_prefix.upper()
                    ]  # Use prefix as site variable
                    cprint(
                        f"This switch will be configured for the "
                        f"{self.site_dict['$site']} site!!\n",
                        "red",
                        attrs=["bold"],
                        force_color=True,
                    )
                    time.sleep(0.1)
                cprint(
                    "Setting the location from the hostname ...\n",
                    "light_cyan",
                    force_color=True,
                )
                time.sleep(0.1)
                # Split the hostname to get location
                location_list = hostname_dict["hostname"].split("-")
                # Set building number from hostname
                location_dict["building"] = location_list[2]
                location_dict["room"] = location_list[3]  # Set room number from hostname
                switch_type_prefix = location_list[1]
                # Set switch type from the prefix
                if switch_type_prefix.upper() in access_switch_prefix_list:
                    self.switch_type_dict["$switch_type"] = "access"
                else:
                    self.switch_type_dict["$switch_type"] = "router"
        self.dict_list.extend([hostname_dict, location_dict])
        for dictionary in condition_dict_list:  # Update template_conditions dictionary
            self.template_conditions.update(dictionary)
        # Set the new template name from hostname
        self.new_config_template = hostname_dict["hostname"] + ".j2"
        new_config_file = hostname_dict["hostname"] + "_" + self.current_date + ".cfg"
        # Set the new config file from hostname
        self.new_config = os.path.join(self.new_config, new_config_file)

    def get_vlan_info(self):
        """ """
        cprint(
            "Gathering VLAN Information ...\n",
            "blue",
            attrs=["bold"],
            force_color=True,
        )
        time.sleep(0.2)
        vlan_dict = {"vlans": {}}

        for line in self.old_config_list:
            # Get spanning-tree vlan priorities if they exist
            if line.startswith("spanning-tree vlan"):
                self.vlan_priority = line
            elif line.startswith("vlan"):  # Get VLAN database information
                match_index = self.old_config_list.index(line)
                vlan_list = line.split(" ")
                vlan_id = vlan_list[1].replace("\n", "")
                vlan_dict["vlans"].update({vlan_id: {}})
                # Copy the line after for the name of the VLAN
                vlan_name_list = self.old_config_list[match_index + 1].split(" ")
                vlan_dict["vlans"][vlan_id]["name"] = vlan_name_list[-1].replace("\n", "")
                continue
        self.dict_list.extend([vlan_dict])
        breakpoint()

    def get_interface_info(self):
        """
        This method parses the old_config_list and extracts the physical and switched virtual interface
        configuration. This is a simple copy and paste, breaking the copying at each '!'.  Future releases will
        convert this into a parsers that returns a dictionary, used for testing and simpler modification.

        """
        cprint(
            "Gathering Interface Information ...\n",
            "blue",
            attrs=["bold"],
            force_color=True,
        )
        time.sleep(0.2)
        standard_config = " no ip proxy-arp\n no ip redirects\n!\n"
        for line in self.old_config_list:
            if line.startswith("interface"):  # Copy the interface configurations
                interfaces = ""
                interfaces += line  # First Line is the interface name
                for interface in self.old_config_list:
                    if "!" in interface:  # Stop copying lines at the !
                        interfaces += "!\n"
                        break
                    else:
                        interfaces += interface

                # Set the standard SVI configurations if they don't exist
                if (
                    "interface Vlan" in interfaces
                    and " no ip proxy-arp" not in interfaces
                ):
                    interfaces = interfaces.replace("!\n", standard_config)
                    # TODO: Add elif for access ports to add standard config and remove duplicates
                self.interfaces += interfaces

    def get_router_config(self):
        """
        This method parses the old_config_list and extracts the router instance configurations along with any static
        routes that may be configured.

        """
        cprint(
            "\nGathering Router Instance Configuration and Static Routes ...\n",
            "blue",
            attrs=["bold"],
            force_color=True,
        )
        time.sleep(0.2)
        for line in self.old_config_list:
            if line.startswith("router "):  # Copy all router instances as a block config
                self.router_config += line
                for router_config in self.old_config_list:
                    if "!" in router_config:
                        self.router_config += "!"
                        break
                    else:
                        self.router_config += router_config
            elif line.startswith("ip route"):  # Copy all static routes as a block config
                self.ip_route += line

    def get_network_services_info(self):
        """This method parses the old_config_list and extracts the configuration information for any network services."""
        cprint(
            "Gathering Network Services Information ...\n",
            "blue",
            attrs=["bold"],
            force_color=True,
        )
        time.sleep(0.2)
        source_interface_dict = {"source_interface": ""}
        mtu_dict = {"mtu": ""}
        gateway_dict = {"gateway": ""}
        for line in self.old_config_list:
            if line.startswith("logging"):  # Copy the logging information
                if "buffered" in line:  # Skip buffered logging config
                    continue
                else:
                    self.logging += line
            # Gather the source interface from the 'tacacs source-interface' command
            elif line.startswith("ip tacacs source-interface"):
                source_list = line.split(" ")
                if source_list[-1] == "\n":
                    del source_list[-1]
                source_interface_dict["source_interface"] = source_list[-1]
                self.dict_list.extend([source_interface_dict])
            elif line.startswith("ip pim rp-address"):  # Copy the rp-address for pim
                self.rp_address += line
            elif line.startswith("system mtu"):  # Copy the system MTU if it exists
                mtu_list = line.split(" ")
                mtu_dict["mtu"] = mtu_list[-1]
                self.dict_list.extend([mtu_dict])
            elif line.startswith("ip default-gateway"):  # Copy the default gateway
                default_list = line.split(" ")
                gateway_dict["gateway"] = default_list[-1]
                self.dict_list.extend([gateway_dict])
        for dictionary in self.dict_list:  # Update the parameters_dict
            self.parameters_dict.update(dictionary)
        # for key, value in self.parameters_dict.items():
        #     print(f"{key}: {value}")
        breakpoint()

    def read_templates_and_set_conditions(self):
        """This method reads the base jinja2 template into the variable ``data`` and modifies it to set the dictionary
        conditions prior to the template rendering, as well as insert all the copied block configuration.

        """

        cprint(
            "Copying Master Template and Setting Template Conditions ...\n",
            "blue",
            attrs=["bold"],
            force_color=True,
        )
        time.sleep(0.1)
        new_config_template = os.path.join(self.template_path, self.new_config_template)

        # read in Switch_Template.j2 template to write to new template hostname.j2
        with (
            open(self.switch_template, "r") as master_template,
            open(new_config_template, "w") as config_template,
        ):
            data = master_template.read()
            for key in self.template_conditions:  # Set the site and switch type
                data = data.replace(key, self.template_conditions[key])
            # Replace variables in the template with block config from the old config
            data = data.replace("!!!vlan_priority", self.vlan_priority)
            data = data.replace("!!!Interfaces", self.interfaces)
            data = data.replace("!!!router_config", self.router_config)
            data = data.replace("!!!rp-address", self.rp_address)
            data = data.replace("!!!ip_route", self.ip_route)
            data = data.replace("!!!logging", self.logging)
            config_template.write(data)

    def create_new_config(self):
        """This method renders the new configuration template, outputs that to a new
        configuration file and then moves the new configuration template to a new
        folder outside the project templates folder.

        """
        cprint("Rendering Templates ....\n", "blue", attrs=["bold"], force_color=True)
        time.sleep(0.1)
        env = Environment(loader=FileSystemLoader(self.template_path))

        # render hostname.j2 template
        switch_config_template = env.get_template(self.new_config_template)
        switch_config = switch_config_template.render(self.parameters_dict)
        with open(self.new_config, "w") as new_config:
            new_config.write(switch_config)
        source_file = os.path.join(self.template_path, self.new_config_template)
        destination_file = os.path.join(
            self.template_path, "New_Templates", self.new_config_template
        )
        if os.path.exists(destination_file):
            os.remove(destination_file)

        os.rename(source_file, destination_file)

        cprint(
            f"Configuration file {self.new_config} is created!\n",
            "green",
            attrs=["bold"],
            force_color=True,
        )
        cprint(
            f"The template file {self.new_config_template} has been moved to {destination_file}!\n",
            "green",
            attrs=["bold"],
            force_color=True,
        )


def sub_main(args):
    """
    This function controls the flow of the program and calls the methods in the class.

    :param args: Parsed CLI arguments
    :return: None
    """
    cfg = ConfigGenerator()
    # Check for CLI arguments, send the list as a parameter else ask for the file name
    if args.config:
        cfg.read_old_config(config=args.config)
    else:
        config = input(
            "What is the filename of the old config file that you want to upgrade? "
            "(Include the .cfg extension) "
        )
        cfg.read_old_config(config=config)
    cfg.get_switch_info()
    cfg.get_vlan_info()
    cfg.get_interface_info()
    cfg.get_router_config()
    cfg.get_network_services_info()
    cfg.read_templates_and_set_conditions()
    cfg.create_new_config()

    input("Press any key to exit the program.")


def main():
    """
    This is the main function and initial entry point into the program.  The command line arguments are set here and
    passed to the sub_main function.  Not all programs use command line arguments, but I leave the code in to allow
    for possible expansion later

    :return: Parsed CLI arguments if there are any
    """
    # TODO: add CLI arguments to take the file name
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # KeyboardInterrupt: Ctrl-C
    # Create CLI arguments and descriptions
    parser = argparse.ArgumentParser(
        prog="golden_config_generator",
        description="This program creates new 'golden' configurations using industry standard best practices from old "
        "configuration files for Cisco switches running IOS-XE versions 16.9 and up.",
        epilog="Thanks for using %(prog)s!",
    )
    parser.add_argument(
        "-c", "--config", required=False, help="Configuration file to convert"
    )

    args = parser.parse_args()
    sub_main(args)


if __name__ == "__main__":
    main()
