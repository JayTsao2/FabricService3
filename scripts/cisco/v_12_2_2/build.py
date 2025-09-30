#!/usr/bin/env python3
"""
Build Script - Import all NDFC modules for fabric automation

This script automatically loads the NDFC management IP from fabric_builder.yaml
and provides access to all cisco 12.2.2 automation modules.

Configuration:
- NDFC IP is read from: network_configs/fabric_builder.yaml
- Falls back to default if config file is not found
"""
from operator import ge
import sys
import os
import json
import time

# Add the cisco 12.2.2 directory to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import all the manager classes from different modules
from modules.fabric import FabricManager
from modules.vrf import VRFManager  
from modules.network import NetworkManager
from modules.switch import SwitchManager
from modules.interface import InterfaceManager
from modules.vpc import VPCManager
from send_to_telegram import notify_telegram


class FabricBuilder:
    """
    Main class for building and managing NDFC fabric configurations.
    """
    
    def __init__(self):
        """Initialize all manager instances."""
        self.fabric_manager = FabricManager()
        self.vrf_manager = VRFManager()
        self.network_manager = NetworkManager()
        self.switch_manager = SwitchManager()
        self.interface_manager = InterfaceManager()
        self.vpc_manager = VPCManager()

        self.YELLOW = '\033[93m'
        self.BOLD = '\033[1m'
        self.END = '\033[0m'  # Reset to default color

    def banner(self):
        """Print a banner for the builder."""
        print("=========================================================")
        print("        NDFC Fabric Builder - Version 12.2.2")
        print("=========================================================")

    def get_root_dir(self):
        """
        Get the root directory of the repository.
        This is used to ensure that the script runs from the correct directory.
        """
        # Get current file's directory and navigate up to root
        current_dir = os.path.dirname(os.path.abspath(__file__))  # 12.2.2
        cisco_dir = os.path.dirname(current_dir)                  # cisco
        scripts_dir = os.path.dirname(cisco_dir)                  # scripts
        root_dir = os.path.dirname(scripts_dir)                   # Repo_fabric
        return root_dir

    def get_fabric_list(self):
        """
        Get the list of fabrics from the configuration.
        Returns a list of fabric names.
        """
        fabric_list = []
        fabric_dir = os.path.join(self.get_root_dir(), 'network_configs', 'vxlan_evpn', 'fabric')
        if os.path.exists(fabric_dir):
            for fabric_file in os.listdir(fabric_dir):
                if fabric_file.endswith('.yaml'):
                    fabric_list.append(fabric_file[:-5])
        return fabric_list

    def get_MSD_list(self):
        """
        Get the list of MSDs from the configuration.
        """
        msds = []
        msd_dir = os.path.join(self.get_root_dir(), 'network_configs', 'vxlan_evpn', 'multisite_deployment')
        if os.path.exists(msd_dir):
            for msd_file in os.listdir(msd_dir):
                if msd_file.endswith('.yaml'):
                    msds.append(msd_file[:-5])  # Remove .yaml extension
        return msds

    def get_ISN_list(self):
        """
        Get the list of ISNs from the configuration.
        """
        isn_list = []
        isn_dir = os.path.join(self.get_root_dir(), 'network_configs', 'vxlan_evpn', 'inter-site_network')
        if os.path.exists(isn_dir):
            for isn_file in os.listdir(isn_dir):
                if isn_file.endswith('.yaml'):
                    isn_list.append(isn_file[:-5])  # Remove .yaml extension
        return isn_list

    def get_switch_list(self):
        """
        Get the list of switches from the configuration.
        Returns a nested dictionary with fabric -> role -> [nodes] structure.
        """
        switches = {}
        switch_dir = os.path.join(self.get_root_dir(), 'network_configs', 'node')
        
        if os.path.exists(switch_dir):
            # Iterate through fabrics
            for fabric_name in os.listdir(switch_dir):
                fabric_path = os.path.join(switch_dir, fabric_name)
                if os.path.isdir(fabric_path):
                    switches[fabric_name] = {}
                    
                    # Iterate through roles within each fabric
                    for role_name in os.listdir(fabric_path):
                        if role_name == "vpc":
                            # Skip VPC directory since it is not a role
                            continue
                        role_path = os.path.join(fabric_path, role_name)
                        if os.path.isdir(role_path):
                            switches[fabric_name][role_name] = []
                            
                            # Iterate through node files within each role
                            for node_file in os.listdir(role_path):
                                if node_file.endswith('.yaml'):
                                    node_name = node_file[:-5]  # Remove .yaml extension
                                    switches[fabric_name][role_name].append(node_name)
        
        return switches

    def build(self):
        """
        Build the fabric configuration.
        """
        # TODO: revised
        from scripts.inventory.reachability_checks import conn_check, device_check, ping_check
        if not ping_check.check():
            print("PING CHECK FAILED")
            notify_telegram("PING CHECK FAILED")
            return
        if not device_check.check():
            print("DEVICE CHECK FAILED")
            notify_telegram("DEVICE CHECK FAILED")
            return
        if not conn_check.check():
            print("CONN CHECK FAILED")
            notify_telegram("CONN CHECK FAILED")
            return

        self.banner()
        # Get the structured switch data
        switches_data = self.get_switch_list()
        fabric_list = self.get_fabric_list()
        msd_list = self.get_MSD_list()
        isn_list = self.get_ISN_list()
        for isn in isn_list:
            fabric_list.append(isn)  # Include ISNs in the fabric list

        # Create fabrics
        print(f"{self.BOLD}{'=' * 20}Create fabrics{'=' * 20}{self.END}")
        for fabric_name in fabric_list:
            self.fabric_manager.create_fabric(fabric_name)
        
        for msd in msd_list:
            self.fabric_manager.create_fabric(msd)

        # Add switches to fabrics
        print(f"{self.BOLD}{'=' * 20}Add switches to fabrics{'=' * 20}{self.END}")
        for fabric_name, roles in switches_data.items():
            for role_name, switches in roles.items():
                for switch in switches:
                    preserve_config = False
                    if fabric_name in isn_list:
                        preserve_config = True
                    self.switch_manager.discover_switch(fabric_name, role_name, switch, preserve_config=preserve_config)
                    self.switch_manager.set_switch_role(fabric_name, role_name, switch)

        # Check switch reachability
        print(f"{self.BOLD}{'=' * 20}Checking switch reachability for each fabric{'=' * 20}{self.END}")
        for fabric_name in fabric_list:
            for role_name, switches in switches_data[fabric_name].items():
                for switch in switches:
                    self.switch_manager.rediscover_switch(fabric_name, role_name, switch)

        # Add fabrics to MSD
        print(f"{self.BOLD}{'=' * 20}Add fabrics to MSD{'=' * 20}{self.END}")
        if msd_list and switches_data:
            for msd in msd_list:
                for fabric_name in fabric_list:
                    self.fabric_manager.add_to_msd(msd, fabric_name)

        # Stage-1 / Recalculate and Deploy
        print(f"{self.BOLD}{'=' * 20}Recalculate & deploy for each fabric{'=' * 20}{self.END}")
        for fabric_name in fabric_list:
            success = self.fabric_manager.recalculate_config(fabric_name)
            while not success:
                # Sleep for 30 secs
                time.sleep(30)
                success = self.fabric_manager.recalculate_config(fabric_name)
            self.fabric_manager.deploy_fabric(fabric_name)

        for fabric_name in msd_list:
            success = self.fabric_manager.recalculate_config(fabric_name)
            while not success:
                # Sleep for 30 secs
                time.sleep(30)
                success = self.fabric_manager.recalculate_config(fabric_name)

            self.fabric_manager.deploy_fabric(fabric_name)

        # for fabric_name in fabric_list:
        #     for role_name, switches in switches_data[fabric_name].items():
        #         retry_time = 10
        #         for switch in switches:
        #             # Check interface operation status
        #             print(f"{self.BOLD}{'=' * 20}Check interface operation status for {switch} in {fabric_name}{self.END}")
        #             while not self.interface_manager.check_interface_operation_status(fabric_name, role_name, switch):
        #                 print(f"{self.BOLD}{self.YELLOW}Interface operation status check failed for {switch} in {fabric_name}. Trying in {retry_time} seconds.{self.END}")
        #                 time.sleep(retry_time)


        #Create VPC pairs for each fabric
        print(f"{self.BOLD}{'=' * 20}Create VPC pairs{'=' * 20}{self.END}")
        for fabric_name in fabric_list:
            self.vpc_manager.create_vpc_pairs(fabric_name)

        # Stage-2 / Recalculate and Deploy
        print(f"{self.BOLD}{'=' * 20}Recalculate & deploy for each fabric{'=' * 20}{self.END}")
        for fabric_name in fabric_list:
            success = self.fabric_manager.recalculate_config(fabric_name)
            while not success:
                # Sleep for 30 secs
                time.sleep(30)
                success = self.fabric_manager.recalculate_config(fabric_name)
            self.fabric_manager.deploy_fabric(fabric_name)

        for fabric_name in msd_list:
            success = self.fabric_manager.recalculate_config(fabric_name)
            while not success:
                # Sleep for 30 secs
                time.sleep(30)
                success = self.fabric_manager.recalculate_config(fabric_name)

            self.fabric_manager.deploy_fabric(fabric_name)


        # Create VRFs (delete unwanted, update existing, create missing)
        print(f"{self.BOLD}{'=' * 20}Create VRFs{'=' * 20}{self.END}")
        for msd in msd_list:
            self.vrf_manager.sync(msd)

        # Attach VRF to switches
        print(f"{self.BOLD}{'=' * 20}Attach VRF to switches{'=' * 20}{self.END}")
        for fabric_name, roles in switches_data.items():
            if fabric_name in isn_list:
                # Skip ISN fabrics for VRF attachment
                continue
            for role_name, switches in roles.items():
                for switch in switches:
                    self.vrf_manager.sync_attachments(fabric_name, role_name, switch)

        # Create Networks (delete unwanted, update existing, create missing)
        print(f"{self.BOLD}{'=' * 20}Create Networks{'=' * 20}{self.END}")
        for msd in msd_list:
            self.network_manager.sync(msd)

        # Attach Network to switches
        print(f"{self.BOLD}{'=' * 20}Attach Network to switches{'=' * 20}{self.END}")
        for fabric_name, roles in switches_data.items():
            if fabric_name in isn_list:
                # Skip ISN fabrics for network attachment
                continue
            for role_name, switches in roles.items():
                for switch in switches:
                    self.network_manager.sync_attachments(fabric_name, role_name, switch)

        # Apply interface configurations
        print(f"{self.BOLD}{'=' * 20}Apply interface configurations{'=' * 20}{self.END}")
        for fabric_name, roles in switches_data.items():
            for role_name, switches in roles.items():
                for switch in switches:
                    self.interface_manager.update_switch_interfaces(fabric_name, role_name, switch)
                    # self.interface_manager.deploy_switch_interfaces(fabric_name, role_name, switch)


        # Set switch freeform configs
        print(f"{self.BOLD}{'=' * 20}Set switch freeform configs{'=' * 20}{self.END}")
        # This step is optional and can be used to set any freeform configurations on switches
        for fabric_name, roles in switches_data.items():
            for role_name, switches in roles.items():
                for switch in switches:
                    self.switch_manager.set_switch_freeform(fabric_name, role_name, switch)

        # Final recalculate for each fabric
        print(f"{self.BOLD}{'=' * 20}Final recalculate for each fabric{'=' * 20}{self.END}")
        for fabric_name in fabric_list:
            success = self.fabric_manager.recalculate_config(fabric_name)
            while not success:
                time.sleep(10)
                success = self.fabric_manager.recalculate_config(fabric_name)

            # Get pending configs
            self.fabric_manager.get_pending_config(fabric_name)
        for fabric_name in msd_list:
            success = self.fabric_manager.recalculate_config(fabric_name)
            while not success:
                time.sleep(10)
                success = self.fabric_manager.recalculate_config(fabric_name)
            self.fabric_manager.get_pending_config(fabric_name)

        # Deploy fabric
        for fabric_name in switches_data.keys():
            self.fabric_manager.deploy_fabric(fabric_name)

    def delete(self):
        """
        Delete fabric configurations using dynamic data.
        """
        # Get the structured data
        switches_data = self.get_switch_list()
        fabric_list = self.get_fabric_list()
        msd_list = self.get_MSD_list()
        isn_list = self.get_ISN_list()

        # Delete all switches from all fabrics
        for fabric_name, roles in switches_data.items():
            for role_name, switches in roles.items():
                for switch in switches:
                    self.switch_manager.delete_switch(fabric_name, role_name, switch)

        # Remove fabrics from MSDs
        if msd_list and switches_data:
            for msd in msd_list:
                for fabric_name in fabric_list:
                    self.fabric_manager.remove_from_msd(msd, fabric_name)
                for isn in isn_list:
                    self.fabric_manager.remove_from_msd(msd, isn)

        # Delete all fabrics
        for fabric_name in fabric_list:
            self.fabric_manager.delete_fabric(fabric_name)

        # Delete ISN fabrics
        for isn in isn_list:
            self.fabric_manager.delete_fabric(isn)

        # Delete MSD fabrics
        for msd in msd_list:
            self.fabric_manager.delete_fabric(msd)


if __name__ == '__main__':
    builder = FabricBuilder()
    builder.build()
    notify_telegram("Fabric Builder Done ✅")

    # builder.delete()
    # notify_telegram("Fabric Deleted ✅")
