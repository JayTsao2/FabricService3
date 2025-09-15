#!/usr/bin/env python3
"""
Switch Manager - Unified Switch Management Interface

This module provides a clean, unified interface for all switch operations with:
- YAML-based switch configuration management
- Switch discovery and deletion operations
- Role management and IP address changes
- Freeform policy configuration
- Hostname management
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
import paramiko
import time

import api.switch as switch_api
import api.policy as policy_api
from modules.config_utils import load_yaml_file, read_freeform_config
from config.config_factory import config_factory

# Valid switch roles enum
VALID_SWITCH_ROLES = {
    "leaf",
    "spine", 
    "super spine",
    "border gateway",
    "border gateway spine",
    "border gateway super spine",
    "core router",
    "edge router",
    "tor"
}

class SwitchManager:
    """Unified switch operations manager with YAML configuration support."""
    
    def __init__(self):
        """Initialize with centralized configuration paths."""
        self.config_paths = config_factory.create_switch_config()
        self.config_base_path = self.config_paths['configs_dir']
        self.GREEN = '\033[92m'
        self.YELLOW = '\033[93m'
        self.BOLD = '\033[1m'
        self.END = '\033[0m'

    def _validate_switch_role(self, role: str) -> bool:
        """Validate if the role is in the allowed enum values."""
        role_lower = role.lower().strip()
        if role_lower not in VALID_SWITCH_ROLES:
            print(f"Error: Invalid switch role '{role}'. Valid roles are:")
            for valid_role in sorted(VALID_SWITCH_ROLES):
                print(f"  - {valid_role}")
            return False
        return True
    
    def _load_switch_config(self, fabric_name: str, role: str, switch_name: str) -> Optional[Dict[str, Any]]:
        """Load switch configuration from YAML file."""
        config_path = self.config_base_path / fabric_name / role / f"{switch_name}.yaml"
        
        if not config_path.exists():
            print(f"Switch configuration not found: {config_path}")
            return None
        return load_yaml_file(str(config_path))
    
    def _extract_model_name(self, platform: str) -> str:
        """Extract model name from platform string."""
        # Extract model from platform (e.g., "N9K-C9300v" -> "N9K")
        if "-" in platform:
            return platform.split("-")[0]
        return platform
    
    def _build_switch_config(self, fabric_name: str, role: str, switch_name: str, 
                           switch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build switch config dictionary from YAML data."""
        # Extract required fields from switch_data
        ip_address = switch_data.get("IP Address", "")
        serial_number = switch_data.get("Serial Number", "")
        platform = switch_data.get("Platform", "")
        version = switch_data.get("Version", "9.3(15)")  # Default version if not specified
        
        # Apply transformations
        model_name = self._extract_model_name(platform)
        device_index = f"{switch_name}-{model_name}({serial_number})"
        
        # Build and return the config structure
        return {
            "fabric_name": fabric_name,
            "sys_name": switch_name,
            "serial_number": serial_number,
            "ip_address": ip_address,
            "platform": platform,
            "version": version,
            "device_index": device_index,
            # API format fields
            "sysName": switch_name,
            "serialNumber": serial_number,
            "ipaddr": ip_address,
            "deviceIndex": device_index
        }
    
    def _build_discovery_payload(self, switch_config: Dict[str, Any], preserve_config: bool = False) -> Dict[str, Any]:
        """Build discovery payload for API."""
        # Extract required fields from switch_config
        seed_ip = switch_config["ip_address"]
        switch_api_data = {
            "sysName": switch_config["sys_name"],
            "serialNumber": switch_config["serial_number"],
            "ipaddr": switch_config["ip_address"],
            "platform": switch_config["platform"],
            "deviceIndex": switch_config["device_index"],
            "version": switch_config["version"]
        }
        
        # Build and return the payload structure
        return {
            "seedIP": seed_ip,
            "username": "admin",
            "password": "",  # Will be filled from environment
            "maxHops": 0,
            "preserveConfig": preserve_config,
            "switches": [switch_api_data],
            "platform": "null"
        }
    
    def discover_switch(self, fabric_name: str, role: str, switch_name: str, preserve_config: bool = False) -> bool:
        """Discover switch based on YAML configuration."""
        print(f"[Switch] {self.GREEN}Discovering switch {switch_name} in fabric {fabric_name}{self.END}")
        switch_data = switch_api.get_switches(fabric_name)
        for switch in switch_data:
            if switch['logicalName'] == switch_name:
                print(f"[Switch] {self.YELLOW}Switch {switch_name} already exists in fabric {fabric_name}. Skipping discovery.{self.END}")
                return True

        switch_data = self._load_switch_config(fabric_name, role, switch_name)
        if not switch_data:
            return False
        
        switch_config = self._build_switch_config(fabric_name, role, switch_name, switch_data)
        payload = self._build_discovery_payload(switch_config, preserve_config)
        
        return switch_api.discover_switch(fabric_name, payload)
    
    def delete_switch(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Delete switch based on YAML configuration."""
        print(f"[Switch] {self.YELLOW}{self.BOLD}Deleting switch {switch_name} from fabric {fabric_name}{self.END}")
        
        switch_data = self._load_switch_config(fabric_name, role, switch_name)
        if not switch_data:
            return False
        
        serial_number = switch_data.get("Serial Number")
        if not serial_number:
            print(f"[Switch] Error: Serial Number not found in {switch_name} configuration")
            return False
        return switch_api.delete_switch(fabric_name, serial_number)
    
    def set_switch_role(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Set switch role based on YAML configuration."""
        switch_data = self._load_switch_config(fabric_name, role, switch_name)
        if not switch_data:
            return False
        
        serial_number = switch_data.get("Serial Number")
        switch_role = switch_data.get("Role")
        
        if not serial_number:
            print(f"[Switch] Error: Serial Number not found in {switch_name} configuration")
            return False
        
        if not switch_role:
            print(f"[Switch] Error: Role not found in {switch_name} configuration")
            return False
        
        if not self._validate_switch_role(switch_role):
            print(f"[Switch] Error: Invalid role '{switch_role}' for switch {switch_name}")
            return False
        
        switch_role_lower = switch_role.lower().strip()
        print(f"[Switch] {self.GREEN}Setting role for switch '{switch_name}' to '{switch_role_lower}'{self.END}")

        return switch_api.set_switch_role(serial_number, switch_role_lower)
    
    def change_switch_ip(self, fabric_name: str, role: str, switch_name: str, 
                        original_ip: str, new_ip: str) -> bool:
        """Change switch management IP through SSH and update NDFC."""
        print(f"[Switch] Changing IP for switch {switch_name} from {original_ip} to {new_ip}")
        
        switch_data = self._load_switch_config(fabric_name, role, switch_name)
        if not switch_data:
            return False
        
        serial_number = switch_data.get("Serial Number")
        if not serial_number:
            print(f"[Switch] Error: Serial Number not found in {switch_name} configuration")
            return False
        
        original_ip_only = original_ip.split('/')[0]
        new_ip_with_mask = new_ip
        new_ip_only = new_ip.split('/')[0]
        
        if not self._ssh_change_management_ip(original_ip_only, new_ip_with_mask):
            return False
        
        switch_api.change_discovery_ip(fabric_name, serial_number, new_ip_only)
        switch_api.rediscover_device(fabric_name, serial_number)
        
        print(f"[Switch] Successfully changed IP for switch {switch_name}")
        return True
    
    def _ssh_change_management_ip(self, original_ip: str, new_ip_with_mask: str) -> bool:
        """SSH to switch and change management IP address."""
        try:
            # Load environment for password from the correct path
            from dotenv import load_dotenv
            # Go to the script directory and then to api/.env
            script_dir = Path(__file__).resolve().parents[2]  # Go up to scripts/cisco/12.2.2/
            env_path = script_dir / "api" / ".env"
            load_dotenv(env_path)
            password = os.getenv("SWITCH_PASSWORD")
            
            if not password:
                print("Error: SWITCH_PASSWORD not found in environment")
                print(f"Please check .env file at: {env_path}")
                return False
            
            # SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            print(f"[*] Connecting to {original_ip}")
            ssh.connect(original_ip, username="admin", password=password, timeout=30)
            
            # Execute IP change command
            command = f"configure terminal ; interface mgmt0 ; ip address {new_ip_with_mask} ; exit ; exit"
            print(f"[*] Executing: ip address {new_ip_with_mask}")

            stdin, stdout, stderr = ssh.exec_command(command)
            
            # Wait for command execution
            time.sleep(2)
            
            ssh.close()
            print("[+] IP address changed successfully")
            return True
            
        except Exception as e:
            print(f"SSH Error: {e}")
            return False
    
    def set_switch_freeform(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Create a freeform policy for switch based on YAML configuration."""
        print(f"[Switch] {self.GREEN}Creating freeform policy for switch {switch_name}{self.END}")

        switch_data = self._load_switch_config(fabric_name, role, switch_name)
        if not switch_data:
            return False
        
        serial_number = switch_data.get("Serial Number")
        if not serial_number:
            print(f"[Switch] Error: Serial Number not found in {switch_name} configuration")
            return False
        
        freeform_config_paths = switch_data.get("Switch Freeform Config")
        if not freeform_config_paths:
            print(f"[Switch] Switch Freeform Config not found in {switch_name} configuration, skipping freeform policy creation")
            return False
        freeform_config_paths = freeform_config_paths.split(',')
        for freeform_config_path in freeform_config_paths:
            freeform_config_path = freeform_config_path.strip()
            print(f"[Switch] Using freeform config file: {freeform_config_path}")

            policy_api.delete_existing_policies_for_switch(switch_name, serial_number)

            cli_commands = self._parse_freeform_config(fabric_name, role, freeform_config_path)
            if not cli_commands:
                return False
            
            policy_id = policy_api.create_policy_with_random_id(
                switch_name, serial_number, fabric_name, cli_commands
            )

            if not policy_id:
                print(f"Failed to create policy for switch {switch_name}")
                return False

            print(f"[Switch] Retrieving and saving policy {policy_id}")
            numeric_id = policy_id.split('-')[1]
            policy_api.get_policy_by_id(numeric_id, switch_name=switch_name)
        return True
    
    def _parse_freeform_config(self, fabric_name: str, role: str, freeform_config_path: str) -> Optional[str]:
        """Parse freeform configuration file and return CLI commands."""
        # Build the full path to the freeform config file
        # The path is relative to the switch YAML file location
        switch_dir = self.config_base_path / fabric_name / role
        config_file_path = switch_dir / freeform_config_path
        
        print(f"[Switch] Reading freeform config: {config_file_path.name}")
        
        # Use config_utils function to read the freeform config
        cli_commands = read_freeform_config(str(config_file_path))

        if "$BGP_ASN" in cli_commands:
            fabric_dir = self.config_base_path / ".." / "vxlan_evpn" / "fabric"
            fabric_config_path = fabric_dir / f"{fabric_name}.yaml"
            fabric_config = load_yaml_file(str(fabric_config_path))
            general = fabric_config.get("General Parameter")
            bgp_asn = general.get("BGP ASN")
            if not bgp_asn:
                print(f"[Switch] Error: BGP ASN not found in fabric {fabric_name} configuration")
                return None
            cli_commands = cli_commands.replace("$BGP_ASN", str(bgp_asn))

        if not cli_commands:
            print(f"[Switch] Warning: No freeform config found or file is empty")
            return None
        
        return cli_commands
    
    def _get_switch_password(self) -> Optional[str]:
        """Get switch password from environment."""
        from dotenv import load_dotenv
        script_dir = Path(__file__).resolve().parents[2]
        env_path = script_dir / "api" / ".env"
        load_dotenv(env_path)
        password = os.getenv("SWITCH_PASSWORD")
        
        if not password:
            print("Error: SWITCH_PASSWORD not found in environment")
            print(f"Please check .env file at: {env_path}")
        
        return password
    
    def change_switch_hostname(self, fabric_name: str, role: str, switch_name: str, new_hostname: str) -> bool:
        """Change the hostname of a switch by updating the host_11_1 policy."""
        print(f"[Switch] Changing hostname for switch {switch_name} to {new_hostname}")
        
        switch_data = self._load_switch_config(fabric_name, role, switch_name)
        if not switch_data:
            return False
        
        serial_number = switch_data.get("Serial Number")
        if not serial_number:
            print(f"[Switch] Error: Serial Number not found in {switch_name} configuration")
            return False
        
        policies = policy_api.get_policies_by_serial_number(serial_number)
        if not policies:
            print(f"[Switch] No policies found for switch {switch_name}")
            return False
        
        hostname_policy = None
        for policy in policies:
            if policy.get("templateName") == "host_11_1" and not policy.get("deleted"):
                hostname_policy = policy
                break
        
        if not hostname_policy:
            print(f"[Switch] Error: host_11_1 policy not found for switch {switch_name}")
            return False
        
        policy_id = hostname_policy.get("policyId")
        hostname_policy["nvPairs"]["SWITCH_NAME"] = new_hostname
        
        print(f"[Switch] Updating hostname policy {policy_id}")
        return policy_api.update_policy(policy_id, hostname_policy)
        
    def rediscover_switch(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Rediscover a switch by its name."""
        config = self._load_switch_config(fabric_name, role, switch_name)
        if not config:
            print(f"[Switch] Error: Switch {switch_name} configuration not found")
            return False

        serial_number = config.get("Serial Number")
        if not serial_number:
            print(f"[Switch] Error: Serial Number not found in {switch_name} configuration")
            return False

        # TODO: generate error report
        retry_times = 10
        success = False
        check_interval = 10
        for i in range(retry_times):
            print(f"[Switch] {self.GREEN}{self.BOLD}Rediscovering switch {switch_name} with serial {serial_number}{self.END}")
            switch_data = switch_api.get_switches(fabric_name)
            for switch in switch_data:
                if switch['logicalName'] != switch_name:
                    continue
                status = switch["status"]
                if status == "ok":
                    print(f"[Switch] {self.GREEN}Status of switch {switch_name} is now OK.{self.END}")
                    success = True
                    break
                print(f"[Switch] {self.YELLOW}Status of switch {switch_name} is {status}, retrying...{self.END}")
                switch_api.rediscover_device(fabric_name, serial_number)
                time.sleep(check_interval)
        return True