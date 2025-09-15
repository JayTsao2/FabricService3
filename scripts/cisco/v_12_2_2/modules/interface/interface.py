#!/usr/bin/env python3
"""
Interface Manager - Unified Interface Management Interface

This module provides a clean, unified interface for all interface operations with:
- YAML-based interface configuration management
- Interface configuration updates using switch YAML files
- Freeform configuration integration
- Policy-based interface management (access, trunk, routed)
"""
import json
import time

import api.interface as interface_api
from modules.config_utils import load_yaml_file, read_freeform_config
from typing import Dict, Any
from pathlib import Path

class InterfaceManager:
    """Unified interface operations manager with YAML configuration support."""
    
    def __init__(self):
        """Initialize with centralized configuration paths."""
        current_file = Path(__file__).resolve()
        self.root_path = current_file.parents[5]
        self.switch_base_path = self.root_path / "network_configs" / "node"
        self.GREEN = "\033[92m"
        self.YELLOW = "\033[93m"
        self.RED = "\033[91m"
        self.BOLD = "\033[1m"
        self.END = "\033[0m"

    def _load_config(self, fabric_name: str, role: str, switch_name: str) -> Dict[str, Any]:
        """Load and validate switch configuration from YAML file."""
        return load_yaml_file(str(self.switch_base_path / fabric_name / role / f"{switch_name}.yaml"))

    def check_interface_operation_status(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Check the operational status of interfaces for a switch."""
        print(f"[Interface] {self.GREEN}{self.BOLD}Checking interface operation status for switch '{switch_name}' ({role}) in fabric '{fabric_name}'{self.END}")
        switch_config = self._load_config(fabric_name, role, switch_name)
        if not switch_config or "Interface" not in switch_config:
            print(f"[Interface] {self.YELLOW}Warning: No interface configuration found for '{switch_name}', skipping.{self.END}")
            return True
        
        serial_number = switch_config.get("Serial Number")
        if not serial_number:
            print(f"[Interface] {self.YELLOW}Warning: No serial number found in switch config for '{switch_name}', skipping.{self.END}")
            return True

        for interface_dict in switch_config["Interface"]:
            interface_name = next(iter(interface_dict.keys()))
            interface_config = interface_dict[interface_name]

            admin_status_config = interface_config.get("Enable Interface")
            if admin_status_config is None:
                admin_status_config = interface_config.get("Enable Port Channel")

            if admin_status_config is None:
                print(f"[Interface] {self.YELLOW}Warning: No admin status found for interface '{interface_name}' in config, skipping.{self.END}")
                continue

            if admin_status_config == False:
                print(f"[Interface] {self.YELLOW}Interface '{interface_name}' is administratively down, skip interface operation status check.{self.END}")
                continue
            policy = interface_config.get("policy", "").lower()
            if policy:
                continue
            # print(f"[Interface] Interface '{interface_name}' does not have a policy defined, checking the operation status.{self.END}")
            data = interface_api.get_interface_details(serial_number, interface_name)
            data = data[0] if isinstance(data, list) and len(data) > 0 else data
            if not data:
                print(f"[Interface] {self.RED}Error: No data found for interface '{interface_name}'{self.END}")
                continue
            oper_status = data.get("operStatusStr", "unknown")
            admin_status = data.get("adminStatusStr", "unknown")
            if oper_status != admin_status:
                print(f"[Interface] {self.RED}Error: Operation status for Interface '{interface_name}' is {oper_status}, but admin status is {admin_status}.{self.END}")
                return False
        print(f"[Interface] {self.GREEN}{self.BOLD}All interfaces for switch '{switch_name}' are operational.{self.END}")
        return True

    def update_switch_interfaces(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Update all interfaces for a switch based on YAML configuration."""
        print(f"[Interface] {self.GREEN}{self.BOLD}Updating interfaces for switch '{switch_name}' ({role}) in fabric '{fabric_name}'{self.END}")

        try:
            switch_config = self._load_config(fabric_name, role, switch_name)
            if not switch_config or "Interface" not in switch_config:
                print(f"[Interface] {self.RED}Error: No interface configuration found for '{switch_name}'{self.END}")
                return False
            
            serial_number = switch_config.get("Serial Number")
            if not serial_number:
                print(f"[Interface] {self.RED}Error: No serial number found in switch config for '{switch_name}'{self.END}")
                return False    
            
            # Process all interfaces
            updated_interfaces = {}
            port_channel_map = {}
            for interface_dict in switch_config["Interface"]:
                interface_name = next(iter(interface_dict.keys()))
                interface_config = interface_dict[interface_name]

                policy = interface_config.get("policy", "").lower()
                if not policy:
                    self._handle_no_policy_interface(interface_name, serial_number, interface_config)
                    continue

                nv_pairs = self._get_nv_pairs(interface_config, interface_name)
                if interface_name.lower().startswith('port-channel'):
                    port_channel_map.update(self._create_port_channel_mapping(interface_name, interface_config))

                if "port_channel" in policy and "member" in policy:
                    nv_pairs.update(self._get_port_member_nv_pairs(interface_name, port_channel_map))

                nv_pairs["CONF"] = self._get_freeform_config(interface_config, fabric_name, role)
                if policy not in updated_interfaces:
                    updated_interfaces[policy] = []

                updated_interfaces[policy].append({
                    "serialNumber": serial_number,
                    "ifName": interface_name,
                    "nvPairs": nv_pairs
                })
            return self._apply_interface_updates(updated_interfaces)
            
        except Exception as e:
            print(f"[Interface] Error updating switch interfaces: {e}")
            return False
    
    def deploy_switch_interfaces(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Deploy the interfaces configuration"""
        print(f"[Interface] {self.GREEN}{self.BOLD}Deploying interfaces for switch '{switch_name}' ({role}) in fabric '{fabric_name}'{self.END}")
        try:
            switch_config = self._load_config(fabric_name, role, switch_name)
            if not switch_config or "Interface" not in switch_config:
                print(f"[Interface] {self.RED}Error: No interface configuration found for '{switch_name}'{self.END}")
                return False
            serial_number = switch_config.get("Serial Number")
            if not serial_number:
                print(f"[Interface] {self.RED}Error: No serial number found in switch config for '{switch_name}'{self.END}")
                return False

            # Process all interfaces
            for interface_dict in switch_config["Interface"]:
                interface_name = next(iter(interface_dict.keys()))
                if not interface_api.deploy_interface(serial_number, interface_name):
                    print(f"[Interface] {self.RED}Error deploying interface '{interface_name}' on switch '{switch_name}'{self.END}")
            print(f"[Interface] {self.GREEN}{self.BOLD}Successfully deployed interfaces for switch '{switch_name}'{self.END}")
            return True

        except Exception as e:
            print(f"[Interface] Error deploying switch interfaces: {e}")
            return False

    def _create_port_channel_mapping(self, name, data):
        """Create mapping of member interfaces to port channel names."""
        pc_mapping = {}
        po_name = 'Port-channel' + name[12:] if name.startswith('port-channel') else name

        vlan = ""
        vlan_type = ""
        if data.get("policy") == "int_port_channel_trunk_host":
            vlan = data.get("Trunk Allowed Vlans", "none")
            vlan_type = "trunk"
        elif data.get("policy") == "int_port_channel_access_host":
            vlan = data.get("Access Vlan", "")
            vlan_type = "access"

        members_str = data.get("Port Channel Member Interfaces", "")
        if members_str:
            members = self._parse_interfaces(members_str)
            for member in members:
                normalized = self._normalize_interface_name(member)
                pc_mapping[normalized] = {
                    "port_channel": po_name,
                    "vlan": vlan,
                    "vlan_type": vlan_type
                }
        return pc_mapping
    
    def _parse_interfaces(self, interfaces_str):
        """Parse interface string into list of interface names."""
        interfaces = []
        parts = [part.strip() for part in interfaces_str.split(',')]
        
        for part in parts:
            if '-' in part:
                start_part, end_part = part.split('-', 1)
                start_interface = self._normalize_interface_name(start_part.strip())
                end_num = end_part.strip()
                
                if '/' in start_interface:
                    base_part, start_num = start_interface.rsplit('/', 1)
                    try:
                        for i in range(int(start_num), int(end_num) + 1):
                            interfaces.append(f"{base_part}/{i}")
                    except ValueError:
                        interfaces.append(self._normalize_interface_name(part))
                else:
                    interfaces.append(self._normalize_interface_name(part))
            else:
                interfaces.append(self._normalize_interface_name(part))
        return interfaces
    
    def _normalize_interface_name(self, name):
        """Normalize interface name to standard format."""
        name = name.strip()
        if name.lower().startswith('e1/'):
            return name.replace('e1/', 'Ethernet1/', 1)
        elif name.lower().startswith('eth1/'):
            return name.replace('eth1/', 'Ethernet1/', 1)
        elif name.lower().startswith('ethernet1/'):
            return 'Ethernet1/' + name[10:]
        elif '/' not in name:
            return f"Ethernet1/{name}"
        return name

    def _handle_no_policy_interface(self, name, serial_number, config):
        """Handle interfaces without policy - update admin state only."""
        print(f"[Interface] {self.YELLOW}Interface {name} has no policy specified, updating admin status only{self.END}")
        admin_status = config.get("Enable Interface", False)
        nv_pairs = {
            "ADMIN_STATE": "true" if admin_status else "false"
        }
        return interface_api.change_interface_admin_status(serial_number, name, nv_pairs, admin_status)

    def _get_port_member_nv_pairs(self, interface_name, pc_mapping):
        nv_pairs = {}
        map = pc_mapping.get(interface_name, {})
        po_name = map.get("port_channel", "")
        vlan = map.get("vlan", "")
        vlan_type = map.get("vlan_type", "")
        if not map:
            print(f"[Interface] Warning: No port channel mapping found for member interface {interface_name}")
            return nv_pairs
        
        nv_pairs["PO_ID"] = str(po_name)

        if vlan_type == "access":
            nv_pairs["ACCESS_VLAN"] = str(vlan)
        elif vlan_type == "trunk":
            nv_pairs["ALLOWED_VLANS"] = str(vlan)
        # print(f"[Interface] Interface {interface_name} is set to the member of '{po_name}'")
        return nv_pairs

    def _get_freeform_config(self, config, fabric_name, role):
        freeform_path = config.get("Freeform Config")
        if not freeform_path:
            return ""
        
        switch_dir = self.switch_base_path / fabric_name / role
        freeform_full_path = switch_dir / freeform_path
        return read_freeform_config(str(freeform_full_path))

    def _get_nv_pairs(self, config, interface_name):
        """
        Get the payload for interface updates.
        """
        nv_pairs = {}
        # Common fields
        nv_pairs["INTF_NAME"] = interface_name
        nv_pairs["DESC"] = str(config.get("Interface Description")) if config.get("Interface Description") else ""
        nv_pairs["ADMIN_STATE"] = "true" if config.get("Enable Interface", False) else "false"
        nv_pairs["SPEED"] = str(config.get("SPEED", "Auto"))
        policy = config.get("policy", "")
        
        # Policy-specific updates
        if policy == "int_access_host":
            nv_pairs["ACCESS_VLAN"] = str(config.get("Access Vlan", ""))
            nv_pairs["MTU"] = str(config.get("MTU", "jumbo"))

        elif policy == "int_trunk_host":
            nv_pairs["ALLOWED_VLANS"] = str(config.get("Trunk Allowed Vlans", "none"))
            nv_pairs["MTU"] = str(config.get("MTU", "jumbo"))

        elif policy == "int_routed_host":
            if config.get("Interface IP"):
                nv_pairs["IP"] = str(config.get("Interface IP"))
            if config.get("IP Netmask Length"):
                nv_pairs["PREFIX"] = str(config.get("IP Netmask Length"))
            if config.get("Interface VRF"):
                nv_pairs["INTF_VRF"] = str(config.get("Interface VRF"))
            nv_pairs["MTU"] = str(config.get("MTU", "jumbo"))

        elif "int_loopback" in policy:
            nv_pairs["IP"] = str(config.get("Interface IP", ""))

        elif "port_channel" in policy and "host" in policy:
            nv_pairs["PO_ID"] = interface_name
            nv_pairs["MTU"] = str(config.get("MTU", "jumbo"))
            nv_pairs["PC_MODE"] = str(config.get("Port Channel Mode", "active"))
            nv_pairs["MEMBER_INTERFACES"] = str(config.get("Port Channel Member Interfaces", ""))
            nv_pairs["BPDUGUARD_ENABLED"] = "true" if config.get("Enable BPDU Guard", False) else "no"
            nv_pairs["PORTTYPE_FAST_ENABLED"] = str(config.get("Enable Port Fast", False)).lower()
            if "access" in policy:
                nv_pairs["ACCESS_VLAN"] = str(config.get("Access Vlan", ""))
            elif "trunk" in policy:
                nv_pairs["ALLOWED_VLANS"] = str(config.get("Trunk Allowed Vlans", "none"))

        return nv_pairs
    
    def _apply_interface_updates(self, updated_interfaces):
        """Apply interface updates to NDFC."""
        policy_order = [
            # Port channel member interfaces first
            'int_port_channel_access_member_11_1',
            'int_port_channel_trunk_member_11_1',
            
            # Then regular interfaces
            'int_access_host',
            'int_trunk_host', 
            'int_routed_host',
            'int_loopback0',
            
            # Port channel host interfaces last
            'int_port_channel_access_host',
            'int_port_channel_trunk_host'
        ]
        # Process policies in order
        processed_policies = set()
        for policy in policy_order:
            if policy in updated_interfaces and updated_interfaces[policy]:
                self._process_policy_interfaces(policy, updated_interfaces[policy])
                processed_policies.add(policy)
        
        # Process any remaining policies not in the order list
        for policy, interfaces in updated_interfaces.items():
            if policy not in processed_policies and interfaces:
                self._process_policy_interfaces(policy, interfaces)
        
        return True
    
    def _process_policy_interfaces(self, policy, interfaces):
        """Process interfaces for a specific policy with retry logic."""
        success = False
        count = 0
        while not success and count < 5:
            if interface_api.update_interface(policy=policy, interfaces_payload=interfaces):
                print(f"[Interface] {self.GREEN}{self.BOLD}Successfully updated {len(interfaces)} interfaces for policy {policy}{self.END}")
                success = True
            else:
                count = count + 1
                print(f"[Interface] {self.YELLOW}{self.BOLD}Failed to update interfaces for policy {policy}, retrying ({count}/5){self.END}")
                time.sleep(5)  # Retry after delay