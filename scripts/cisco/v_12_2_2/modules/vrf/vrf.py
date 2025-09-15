#!/usr/bin/env python3
"""
VRF Manager - Unified VRF Management Interface

This module provides a clean, unified interface for all VRF operations with:
- YAML-based VRF configuration management
- VRF CRUD operations with configuration merging
- Template payload generation with field mapping
- Corp defaults integration
- VRF attachment/detachment to switch interfaces
"""

from multiprocessing import process
from pickle import NONE
from typing import List, Dict, Any, Tuple, Optional
from modules.config_utils import load_yaml_file, validate_configuration_files, merge_configs, apply_field_mapping, flatten_config
from config.config_factory import config_factory
import api.vrf as vrf_api
import json

class VRFManager:
    """Unified VRF operations manager with YAML configuration support."""
    
    def __init__(self):
        """Initialize with centralized configuration paths."""
        # Get configuration paths from factory
        config_paths = config_factory.create_vrf_config()
        self.switch_config_paths = config_factory.create_switch_config()
        
        # Set up configuration file paths
        self.config_path = config_paths.config_path
        self.defaults_path = config_paths.defaults_path
        self.field_mapping_path = config_paths.field_mapping_path
        
        # Lazy-loaded cached configurations
        self._defaults = None
        self._field_mapping = None
        self._vrfs = None

        self.GREEN = '\033[92m'
        self.YELLOW = '\033[93m'
        self.BOLD = '\033[1m'
        self.END = '\033[0m'

    @property
    def defaults(self) -> Dict[str, Any]:
        """Get corp defaults with lazy loading."""
        if self._defaults is None:
            self._defaults = load_yaml_file(str(self.defaults_path))
        return self._defaults
    
    @property
    def field_mapping(self) -> Dict[str, Any]:
        """Get field mapping with lazy loading."""
        if self._field_mapping is None:
            self._field_mapping = load_yaml_file(str(self.field_mapping_path))
        return self._field_mapping
    
    @property
    def vrfs(self) -> List[Dict[str, Any]]:
        """Get VRF configurations with lazy loading and caching."""
        if self._vrfs is None:
            try:
                # print(f"[VRF] Loading VRF config from: {self.config_path}")
                config_data = load_yaml_file(str(self.config_path))
                self._vrfs = config_data.get('VRF', [])
            except Exception as e:
                print(f"Error loading VRF configuration: {e}")
                self._vrfs = []
        return self._vrfs
    
    def _validate_resources(self) -> None:
        """Validate required resource files exist."""
        validate_configuration_files([str(self.defaults_path), str(self.field_mapping_path)])
    
    def _build_vrf_template_config(self, vrf_name: str, vrf: Dict[str, Any]) -> Dict[str, Any]:
        """Build VRF template configuration dictionary."""
        # Extract required fields from VRF data
        vrf_id = str(vrf.get('VRF ID', 0))
        vlan_id = str(vrf.get('VLAN ID', 0))
        general_params = vrf.get('General Parameters', {})
        
        # Build base template config
        template_config = {
            "vrfName": vrf_name,
            "vrfSegmentId": vrf_id,
            "vrfVlanId": vlan_id,
            "vrfDescription": general_params.get("VRF Description", vrf_name),
            "vrfVlanName": general_params.get("VRF VLAN Name", vrf_name),
            "vrfIntfDescription": general_params.get("VRF Interface Description", vrf_name),
        }
        
        # Apply corp defaults with field mapping
        self._apply_template_defaults(template_config, vrf)
        
        return template_config
    
    def _apply_template_defaults(self, template_config: Dict[str, Any], vrf: Dict[str, Any]) -> None:
        """Apply corp defaults with field mapping to template config."""
        # Merge VRF config with defaults
        final_config = {}
        for key in self.defaults:
            if key in vrf:
                final_config[key] = merge_configs(self.defaults[key], vrf[key])
            else:
                final_config[key] = self.defaults[key]
        
        # Flatten and apply field mapping
        flat_config = flatten_config(final_config)
        mapped_config = apply_field_mapping(flat_config, flatten_config(self.field_mapping))
        
        # Update template config with mapped values
        for key, value in mapped_config.items():
            if value:  # Only add non-empty values
                template_config[key] = value
    
    def _build_vrf_payload(self, fabric_name: str, vrf_name: str, vrf: Dict[str, Any]) -> Dict[str, Any]:
        """Build VRF payload dictionary."""
        # Extract required fields from VRF data
        vrf_id = vrf.get('VRF ID', 0)
        vlan_id = vrf.get('VLAN ID', 0)
        general_params = vrf.get('General Parameters', {})
        
        # Build base payload
        payload = {
            "fabric": fabric_name,
            "vrfName": vrf_name,
            "vrfTemplate": self.defaults.get("vrfTemplate", "Default_VRF_Universal"),
            "vrfExtensionTemplate": self.defaults.get("vrfExtensionTemplate", "Default_VRF_Extension_Universal"),
            "vrfId": str(vrf_id),
            "vrfVlanId": str(vlan_id),
            "vrfDescription": general_params.get("VRF Description", vrf_name),
        }
        
        return payload

    def _build_complete_payload(self, fabric_name: str, vrf_name: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Build complete VRF payload for API operations."""
        self._validate_resources()
        
        for item in self.vrfs:
            if item.get('VRF Name') == vrf_name:
                vrf = item
                break
        if not vrf:
            raise ValueError(f"VRF '{vrf_name}' not found in configuration")
        
        # Build VRF payload using dictionary approach
        payload = self._build_vrf_payload(fabric_name, vrf_name, vrf)
        
        # Build template config using dictionary approach
        template_config = self._build_vrf_template_config(vrf_name, vrf)

        return payload, template_config

    def _get_serial_number(self, fabric_name: str, role: str, switch_name: str) -> Optional[str]:
        """Get the serial number of a switch in a fabric."""
        switch_path = self.switch_config_paths['configs_dir'] / fabric_name / role / f"{switch_name}.yaml"
        if not switch_path.exists():
            print(f"[VRF] Switch configuration not found: {switch_path}")
            return None

        switch_config = load_yaml_file(str(switch_path))
        if not switch_config:
            print(f"[VRF] Failed to load switch configuration: {switch_path}")
            return None

        serial_number = switch_config.get('Serial Number', '')
        if not serial_number:
            print(f"[VRF] No serial number found in switch configuration: {switch_name}")
            return None

        return serial_number

    # --- VRF CRUD Operations ---
    
    def sync(self, fabric_name: str) -> bool:
        """Update all VRFs for a fabric - delete unwanted, update existing, and create missing VRFs."""
        print(f"[VRF] {self.GREEN}{self.BOLD}Updating all VRFs in fabric '{fabric_name}'{self.END}")

        try:
            # Get existing VRFs from the fabric
            existing_vrfs = vrf_api.get_VRFs(fabric_name)
            existing_vrf_names = {vrf.get('vrfName') for vrf in existing_vrfs}
            
            # Get VRFs from YAML config for this fabric
            fabric_vrfs = [vrf for vrf in self.vrfs if vrf.get('Fabric') == fabric_name]
            yaml_vrf_names = {vrf.get('VRF Name') for vrf in fabric_vrfs}
            
            # Find VRFs to delete (exist in fabric but not in YAML)
            vrfs_to_delete = existing_vrf_names - yaml_vrf_names
            # print(f"[VRF] VRFs to delete: {vrfs_to_delete if vrfs_to_delete else 'None'}")

            # Find VRFs to create (exist in YAML but not in fabric)
            vrfs_to_create = yaml_vrf_names - existing_vrf_names
            # print(f"[VRF] VRFs to create: {vrfs_to_create if vrfs_to_create else 'None'}")

            # Find VRFs to update (exist in both fabric and YAML)
            vrfs_to_update = existing_vrf_names.intersection(yaml_vrf_names)
            # print(f"[VRF] VRFs to update: {vrfs_to_update if vrfs_to_update else 'None'}")
            
            overall_success = True
            
            # Delete unwanted VRFs
            for vrf_name in vrfs_to_delete:
                if not self.delete_vrf(fabric_name, vrf_name):
                    overall_success = False
    
            # Update existing VRFs
            for vrf_name in vrfs_to_update:
                if not self.update_vrf(fabric_name, vrf_name):
                    overall_success = False

            # Create missing VRFs
            for vrf_name in vrfs_to_create:
                if not self.create_vrf(fabric_name, vrf_name):
                    overall_success = False

            if overall_success:
                print(f"[VRF] {self.GREEN}{self.BOLD}Successfully synchronized all VRFs in fabric '{fabric_name}'{self.END}")
            else:
                print(f"[VRF] {self.YELLOW}{self.BOLD}VRF synchronization completed with some errors in fabric '{fabric_name}'{self.END}")

            return overall_success
            
        except Exception as e:
            print(f"[VRF] Error updating VRFs: {e}")
            return False
    
    def create_vrf(self, fabric_name: str, vrf_name: str) -> bool:
        """Create a VRF using YAML configuration."""
        print(f"[VRF] {self.GREEN}Creating VRF '{vrf_name}' in fabric '{fabric_name}'{self.END}")

        try:
            # Check if VRF already exists
            existing_vrfs = vrf_api.get_VRFs(fabric_name)
            existing_vrf_names = {vrf.get('vrfName') for vrf in existing_vrfs}
            
            if vrf_name in existing_vrf_names:
                print(f"[VRF] VRF '{vrf_name}' already exists in fabric '{fabric_name}', skipping creation")
                return True
            
            payload, template_config = self._build_complete_payload(fabric_name, vrf_name)
            return vrf_api.create_vrf(fabric_name, payload, template_config)
            
        except Exception as e:
            print(f"[VRF] Error creating VRF '{vrf_name}': {e}")
            return False
    
    def update_vrf(self, fabric_name: str, vrf_name: str) -> bool:
        """Update a VRF using YAML configuration."""
        print(f"[VRF] {self.GREEN}Updating VRF '{vrf_name}' in fabric '{fabric_name}'{self.END}")
        payload, template_config = self._build_complete_payload(fabric_name, vrf_name)
        return vrf_api.update_vrf(fabric_name, vrf_name, payload, template_config)
    
    def delete_vrf(self, fabric_name: str, vrf_name: str) -> bool:
        """Delete a VRF after detaching from all switches."""
        print(f"[VRF] {self.YELLOW}Deleting VRF '{vrf_name}' in fabric '{fabric_name}'{self.END}")
        print(f"[VRF] Trying to detach '{vrf_name}' from all switches in fabric '{fabric_name}' before deletion")
        if not self._detach_vrf_by_serial_number(fabric_name, vrf_name):
            print(f"[VRF] Failed to detach '{vrf_name}' from all switches in fabric '{fabric_name}', aborting deletion")
            return False
        return vrf_api.delete_vrf(fabric_name, vrf_name)
    
    # --- VRF Attachment Operations ---
    def sync_attachments(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Sync VRF attachments for a specific switch."""
        print(f"[VRF] {self.GREEN}{self.BOLD}Syncing VRF attachments for switch '{switch_name}' in fabric '{fabric_name}'{self.END}")
        success = True
        if not self.detach_vrfs(fabric_name, role, switch_name):
            success = False
        if not self.attach_vrfs(fabric_name, role, switch_name):
            success = False
        print(f"[VRF] {self.GREEN}{self.BOLD}Sync attachments completed for switch '{switch_name}' in fabric '{fabric_name}'{self.END}")
        return success

    def attach_vrf(self, fabric_name: str, role: str, switch_name: str, vrf_name: str) -> bool:
        """Attach a specific VRF to a switch."""
        print(f"[VRF] {self.GREEN}Attaching VRF '{vrf_name}' to switch '{switch_name}' in fabric '{fabric_name}'{self.END}")

        try:
            # Load and validate switch configuration
            serial_number = self._get_serial_number(fabric_name, role, switch_name)
            if not serial_number:
                print(f"[VRF] No serial number found for switch '{switch_name}'")
                return False

            for vrf in self.vrfs:
                if vrf.get('VRF Name') == vrf_name:
                    vlan_id = vrf.get('VLAN ID', -1)
                    break

            payload = self._build_vrf_attachment_payload([{
                    'fabric_name': fabric_name,
                    'vrf_name': vrf_name,
                    'serial_number': serial_number,
                    'vlan_id': vlan_id,
                    'deployment': True  # True for attach
            }])
            return vrf_api.update_vrf_attachment(fabric_name, payload)

        except Exception as e:
            print(f"[VRF] Error attaching VRF '{vrf_name}': {e}")
            return False

    def attach_vrfs(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Attach all VRFs found on switch interfaces based on YAML configuration."""
        print(f"[VRF] {self.GREEN}{self.BOLD}Attaching VRFs to switch '{switch_name}' in fabric '{fabric_name}'{self.END}")
        try:
            # Load and validate switch configuration
            config_path = self.switch_config_paths['configs_dir'] / fabric_name / role / f"{switch_name}.yaml"
            # print(f"[VRF] Loading switch config from: {config_path}")
            switch_config = load_yaml_file(str(config_path))
            if not switch_config:   
                print(f"[VRF] Failed to load switch configuration: {config_path}")
                return False
            interfaces = switch_config.get("Interface", [])
            if not isinstance(interfaces, list):
                print(f"[VRF] Invalid interface format in switch '{switch_name}'")
                return False
            # Find all VRFs in switch configuration
            processed_vrfs = set()
            overall_success = True

            for interface in interfaces:
                if not isinstance(interface, dict):
                    continue
                    
                # Each interface item is a dict with one key (interface name)
                for interface_name, interface_config in interface.items():
                    if not isinstance(interface_config, dict):
                        continue

                    if interface_config.get("policy") != "int_routed_host":
                        continue

                    vrf_name = interface_config.get("Interface VRF")
                    if not vrf_name:
                        print(f"[VRF] No VRF found for interface '{interface_name}' in switch '{switch_name}'")
                        continue
                    if vrf_name in processed_vrfs:
                        continue
                    if not self.attach_vrf(fabric_name, role, switch_name, vrf_name):
                        overall_success = False
                    processed_vrfs.add(vrf_name)

            return overall_success
            
        except Exception as e:
            print(f"[VRF] Error attaching VRFs: {e}")
            return False

    def _detach_vrf_by_serial_number(self, fabric_name: str, vrf_name: str, serial_number: str = None) -> bool:
        """Detach a VRF from a switch by serial number."""
        vrf_attachments = vrf_api.get_vrf_attachment(fabric_name, save_files=False)
        if not vrf_attachments:
            print(f"[VRF] No VRF attachment found for '{vrf_name}'")
            return False
        detach_data = []
        for attachment in vrf_attachments:
            if attachment.get('vrfName') != vrf_name:
                continue
            lan_attach_list = attachment.get('lanAttachList', [])
            for lan_attach in lan_attach_list:
                if serial_number is not None and lan_attach.get('switchSerialNo') != serial_number:
                    continue

                is_attach = lan_attach.get('isLanAttached', False)
                if not is_attach:
                    continue

                detach_data.append({
                    'fabric_name': fabric_name,
                    'vrf_name': vrf_name,
                    'serial_number': lan_attach.get('switchSerialNo'),
                    'vlan_id': lan_attach.get('vlanId', -1),
                    'deployment': False,  # False for detach
                })
        payload = self._build_vrf_attachment_payload(detach_data)
        if not payload:
            print(f"[VRF] No need to detach '{vrf_name}' from switch with SN: {serial_number}")
            return True
        return vrf_api.update_vrf_attachment(fabric_name, payload)
    
    def detach_vrf(self, fabric_name: str, role: str, switch_name: str, vrf_name: str) -> bool:
        """Detach a specific VRF from a switch."""
        print(f"[VRF] {self.YELLOW}Detaching VRF '{vrf_name}' from switch '{switch_name}' in fabric '{fabric_name}'{self.END}")

        try:
            serial_number = self._get_serial_number(fabric_name, role, switch_name)
            if not serial_number:
                print(f"[VRF] No serial number found for switch '{switch_name}'")
                return False

            return self._detach_vrf_by_serial_number(fabric_name, vrf_name, serial_number)

        except Exception as e:
            print(f"[VRF] Error detaching VRF '{vrf_name}': {e}")
            return False

    def detach_vrfs(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Detach VRFs that are currently attached in the NDFC by given switch."""
        print(f"[VRF] {self.YELLOW}{self.BOLD}Detaching VRFs from switch '{switch_name}' ({role}) in fabric '{fabric_name}'{self.END}")
        try:
            # Load and validate switch configuration
            serial_number = self._get_serial_number(fabric_name, role, switch_name)
            if not serial_number:
                print(f"[VRF] No serial number found for switch '{switch_name}'")
                return False
            
            vrf_attachments = vrf_api.get_vrf_attachment(fabric_name, save_files=False)
            for attachment in vrf_attachments:
                lan_attach_list = attachment.get('lanAttachList', [])
                for lan_attach in lan_attach_list:
                    if lan_attach.get('switchSerialNo') != serial_number:
                        continue

                    is_attach = lan_attach.get('isLanAttached', False)
                    if not is_attach:
                        continue
                    self.detach_vrf(fabric_name, role, switch_name, attachment.get('vrfName'))
                
        except Exception as e:
            print(f"[VRF] Error detaching unwanted VRFs from switch '{switch_name}': {e}")
            return False
    
    def _build_vrf_attachment_payload(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build VRF attachment payload from normalized data structure.

        Args:
            attach_data: List of dicts with keys: vrf_name, serial_number, vlan_id, switch_name
        """
        payload = []
        for item in data:
            vrf_payload = {
                "vrfName": item.get('vrf_name'),
                "lanAttachList": [{
                    "fabric": item.get('fabric_name'),
                    "vrfName": item.get('vrf_name'),
                    "serialNumber": item.get('serial_number'),
                    "vlan": str(item.get('vlan_id', -1)),
                    "deployment": item.get('deployment', False),  # False for detach
                }]
            }
            payload.append(vrf_payload)
            # print(f"[VRF] Added VRF '{item.get('vrf_name')}' on switch (SN: {item.get('serial_number')}, VLAN: {item.get('vlan_id')}) to {'attach' if item.get('deployment') else 'detach'} payload")

        return payload