"""
VPC Module - VPC Management functionality

This module provides VPC management functionality including:
- Creating VPC pairs for all switches in a fabric
- Deleting VPC pairs for specific switches
- Parsing VPC YAML configuration files
"""

import json
import api.vpc as vpc_api
import api.interface as interface_api
from modules.config_utils import load_yaml_file
from config.config_factory import config_factory


class VPCManager:
    """Manager class for VPC operations."""
    
    def __init__(self):
        """Initialize VPC Manager with centralized configuration paths."""
        self.config_paths = config_factory.create_vpc_config()
        self.config_base_path = self.config_paths['configs_dir']

    def create_vpc_pairs(self, fabric_name: str) -> bool:
        """Create VPC pairs and set policies for all VPC configurations in the specified fabric."""
        try:
            print(f"[VPC] Creating VPC pairs for fabric: {fabric_name}")
            # Build path to VPC configurations
            vpc_dir = self.config_base_path / fabric_name / "vpc"
            
            if not vpc_dir.exists():
                print(f"[VPC] VPC directory not found: {vpc_dir}")
                return False
            
            # Find all YAML files in the VPC directory
            vpc_files = list(vpc_dir.glob("*.yaml")) + list(vpc_dir.glob("*.yml"))
            
            if not vpc_files:
                print(f"[VPC] No VPC configuration files found in {vpc_dir}")
                return False
            
            print(f"[VPC] Found {len(vpc_files)} VPC configuration file(s) in {fabric_name}")
            
            success_count = 0
            for vpc_file in vpc_files:
                print(f"[VPC] Processing VPC configuration: {vpc_file.name}")

                # Load VPC configuration
                vpc_data = load_yaml_file(vpc_file)
                if not vpc_data:
                    print(f"Failed to load VPC configuration from {vpc_file}")
                    continue
                
                # Extract peer serial numbers
                peer_one_id = vpc_data.get("Peer-1 Serial Number")
                peer_two_id = vpc_data.get("Peer-2 Serial Number")
                
                if not peer_one_id or not peer_two_id:
                    print(f"[VPC] Error: Missing peer serial numbers in {vpc_file.name}")
                    print(f"[VPC]   Peer-1: {peer_one_id}")
                    print(f"[VPC]   Peer-2: {peer_two_id}")
                    continue
                
                # Step 1: Create VPC pair via API
                print(f"[VPC] Step 1: Creating VPC pair for {peer_one_id} and {peer_two_id}")
                vpc_api.create_vpc_pair(peer_one_id, peer_two_id)

                # Step 2: Set VPC policy if VPC pair was created successfully
                print(f"[VPC] Step 2: Setting VPC policy for {peer_one_id} and {peer_two_id}")

                # Extract policy details
                policy_data = vpc_data.get("Policy", {})
                if not policy_data:
                    print(f"[VPC] No policy data found in {vpc_file.name}, skipping policy configuration")
                    success_count += 1
                    continue
                
                policy_name = policy_data.get("Name", "int_vpc_trunk_host")
                policy_data = policy_data.get("Policy Options", {})
                # Parse VPC name from filename (format: switch1=switch2=vpcname.yaml)
                filename_without_ext = vpc_file.stem
                parts = filename_without_ext.split('=')
                vpc_name = parts[2] if len(parts) >= 3 else filename_without_ext
                
                # Build the policy payload
                policy_payload = [{
                        "serialNumber": f"{peer_one_id}~{peer_two_id}",
                        "interfaceType": "INTERFACE_VPC",
                        "fabricName": fabric_name,
                        "ifName": vpc_name,
                        "nvPairs": {
                            "PEER1_PCID": str(policy_data.get("Peer-1 Port-Channel ID", "1")),
                            "PEER2_PCID": str(policy_data.get("Peer-2 Port-Channel ID", "1")),
                            "PC_MODE": policy_data.get("Port Channel Mode", "active"),
                            "PEER1_MEMBER_INTERFACES": policy_data.get("Peer-1 Member Interfaces", ""),
                            "PEER2_MEMBER_INTERFACES": policy_data.get("Peer-2 Member Interfaces", ""),
                            "PEER1_ALLOWED_VLANS": policy_data.get("Peer-1 Trunk Allowed Vlans", "none"),
                            "PEER2_ALLOWED_VLANS": policy_data.get("Peer-2 Trunk Allowed Vlans", "none"),
                            "BPDUGUARD_ENABLED": str(policy_data.get("Enable BPDU Guard", False)).lower(),
                            "PORTTYPE_FAST_ENABLED": policy_data.get("Enable Port Type Fast", False),
                            "INTF_NAME": vpc_name
                        }
                    }]

                if interface_api.update_interface(policy_name, policy_payload):
                    success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            print(f"Error creating VPC pairs: {e}")
            return False

    def delete_vpc_pairs(self, fabric_name: str, switch_name: str) -> bool:
        """Delete VPC pairs for a specific switch in the specified fabric."""
        try:
            print(f"[VPC] Deleting VPC pairs for switch: {switch_name} in fabric: {fabric_name}")
            # Build path to VPC configurations
            vpc_dir = self.config_base_path / fabric_name / "vpc"
            
            if not vpc_dir.exists():
                print(f"[VPC] VPC directory not found: {vpc_dir}")
                return False
            
            # Find all YAML files in the VPC directory
            vpc_files = list(vpc_dir.glob("*.yaml")) + list(vpc_dir.glob("*.yml"))
            
            if not vpc_files:
                print(f"[VPC] No VPC configuration files found in {vpc_dir}")
                return False
            
            # Find VPC files that contain the switch name
            matching_files = []
            for vpc_file in vpc_files:
                # Parse filename format: {switchname1}={switchname2}={vpc_name}.yaml
                filename_without_ext = vpc_file.stem
                if '=' in filename_without_ext:
                    parts = filename_without_ext.split('=')
                    if len(parts) >= 3:  # Need at least 3 parts: switch1, switch2, vpc_name
                        switch1, switch2, vpc_name = parts[0], parts[1], parts[2]
                        if switch_name in [switch1, switch2]:
                            matching_files.append((vpc_file, switch1, switch2, vpc_name))
            
            if not matching_files:
                print(f"[VPC] No VPC configuration files found containing switch '{switch_name}' in {fabric_name}")
                return False

            print(f"[VPC] Found {len(matching_files)} VPC configuration file(s) containing switch '{switch_name}' in {fabric_name}")

            success_count = 0
            for vpc_file, switch1, switch2, vpc_name in matching_files:
                print(f"[VPC] Processing VPC configuration: {vpc_file.name}")

                # Load VPC configuration
                vpc_data = load_yaml_file(vpc_file)
                if not vpc_data:
                    print(f"[VPC] Failed to load VPC configuration from {vpc_file}")
                    continue
                
                # Extract peer serial numbers
                peer_one_serial = vpc_data.get("Peer-1 Serial Number")
                peer_two_serial = vpc_data.get("Peer-2 Serial Number")
                
                if not peer_one_serial or not peer_two_serial:
                    print(f"[VPC] Error: Missing peer serial numbers in {vpc_file.name}")
                    print(f"[VPC]   Peer-1: {peer_one_serial}")
                    print(f"[VPC]   Peer-2: {peer_two_serial}")
                    continue
                
                # Determine which serial number corresponds to the target switch
                target_serial = None
                if switch_name == switch1:
                    target_serial = peer_one_serial
                    print(f"[VPC] Target switch '{switch_name}' matches Peer-1: {peer_one_serial}")
                elif switch_name == switch2:
                    target_serial = peer_two_serial
                    print(f"[VPC] Target switch '{switch_name}' matches Peer-2: {peer_two_serial}")

                if not target_serial:
                    print(f"[VPC] Error: Could not determine serial number for switch '{switch_name}'")
                    continue
                
                # Create serial numbers string for policy deletion
                serial_numbers = f"{peer_one_serial}~{peer_two_serial}"
                
                print(f"[VPC] Deleting VPC policy and pair for switch '{switch_name}':")
                print(f"[VPC]  VPC Name: {vpc_name}")
                print(f"[VPC]  Target Serial: {target_serial}")
                print(f"[VPC]  Serial Numbers: {serial_numbers}")

                # Step 1: Delete VPC policy first
                print(f"[VPC] Step 1: Deleting VPC policy for {vpc_name}...")
                interface_api.delete_interfaces([{
                    "ifName": vpc_name,
                    "serialNumber": serial_numbers
                }])
                
                # Step 2: Delete VPC pair
                print(f"[VPC] Step 2: Deleting VPC pair with serial number {target_serial}...")
                if vpc_api.delete_vpc_pair(target_serial):
                    success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            print(f"Error deleting VPC pairs: {e}")
            return False
