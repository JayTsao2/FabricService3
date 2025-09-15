#!/usr/bin/env python3
"""
Fabric Manager - Unified Fabric Management Interface

This module provides a clean, unified interface for all fabric operations with:
- YAML-based fabric configuration management
- Fabric CRUD operations with configuration merging
- Template payload generation with field mapping
- Corp defaults integration
- Freeform configuration support for VXLAN EVPN and ISN fabrics
"""

from typing import Dict, Any, Tuple, Optional
from enum import Enum
from modules.config_utils import (
    load_yaml_file, validate_configuration_files, validate_file_exists,
    merge_configs, apply_field_mapping, flatten_config, 
    get_nested_value, read_freeform_config
)
from config.config_factory import config_factory
import api.fabric as fabric_api

import json

class FabricType(Enum):
    """Enumeration of supported fabric types."""
    VXLAN_EVPN = "Easy_Fabric"
    MULTI_SITE_DOMAIN = "MSD_Fabric"
    INTER_SITE_NETWORK = "External_Fabric"
    
    @classmethod
    def from_yaml_type(cls, yaml_type: str) -> Optional['FabricType']:
        """Convert YAML fabric type string to FabricType enum."""
        yaml_to_enum_mapping = {
            "Data Center VXLAN EVPN": cls.VXLAN_EVPN,
            "VXLAN EVPN Multi-Site": cls.MULTI_SITE_DOMAIN,
            "Multi-Site Interconnect Network": cls.INTER_SITE_NETWORK
        }
        return yaml_to_enum_mapping.get(yaml_type)

class FabricManager:
    """Unified fabric operations manager with YAML configuration support."""
    
    def __init__(self):
        """Initialize with centralized configuration paths."""
        # Get fabric paths from factory
        self.fabric_paths = config_factory.get_fabric_paths()
        self.GREEN = '\033[92m'
        self.YELLOW = '\033[93m'
        self.BOLD = '\033[1m'
        self.END = '\033[0m'

    def _determine_fabric_type_from_file(self, fabric_name: str) -> Optional[FabricType]:
        """Determine the fabric type by reading the YAML configuration file."""
        # Try each possible fabric type configuration path
        possible_paths = [
            (FabricType.VXLAN_EVPN, str(self.fabric_paths['fabric'] / f"{fabric_name}.yaml")),
            (FabricType.MULTI_SITE_DOMAIN, str(self.fabric_paths['multisite'] / f"{fabric_name}.yaml")),
            (FabricType.INTER_SITE_NETWORK, str(self.fabric_paths['inter_site'] / f"{fabric_name}.yaml"))
        ]
        
        for fabric_type, config_path in possible_paths:
            if validate_file_exists(config_path):
                fabric_config = load_yaml_file(config_path)
                if fabric_config and 'Fabric' in fabric_config:
                    yaml_type = get_nested_value(fabric_config, ('Fabric', 'type'))
                    if yaml_type:
                        return FabricType.from_yaml_type(yaml_type)
        
        print(f"[Fabric] Could not determine fabric type for: {fabric_name}")
        return None
    
    def _build_fabric_payload(self, fabric_config: Dict[str, Any], defaults_config: Dict[str, Any], 
                             field_mapping: Dict[str, Any], fabric_name: str, fabric_type: FabricType) -> Dict[str, Any]:
        """Build fabric payload dictionary."""
        # Merge configurations
        final_config = {}
        for key in defaults_config:
            if key in fabric_config:
                final_config[key] = merge_configs(defaults_config[key], fabric_config[key])
            else:
                final_config[key] = defaults_config[key]
        
        # Flatten and apply field mapping
        flat_config = flatten_config(final_config)
        mapped_config = apply_field_mapping(flat_config, flatten_config(field_mapping))
        
        # Clean up mapped config - remove VRF/Network template settings
        template_keys = ['vrfTemplate', 'networkTemplate', 'vrfExtensionTemplate', 'networkExtensionTemplate']
        for key in template_keys:
            mapped_config.pop(key, None)
        
        # Set required fields
        mapped_config["FABRIC_NAME"] = fabric_name
        
        if "BGP_AS" in mapped_config:
            mapped_config["SITE_ID"] = mapped_config["BGP_AS"]
        
        # Apply fabric-type specific modifications
        if fabric_type == FabricType.MULTI_SITE_DOMAIN:
            mapped_config["FABRIC_TYPE"] = "MFD"
            mapped_config["FF"] = "MSD"
        elif fabric_type == FabricType.INTER_SITE_NETWORK:
            mapped_config.pop("SITE_ID", None)  # Remove SITE_ID if it exists
            mapped_config["FABRIC_TYPE"] = "External"
            mapped_config["EXT_FABRIC_TYPE"] = "Multi-Site External Network"
        return mapped_config
    
    def _get_freeform_paths(self, fabric_name: str, fabric_type: FabricType, fabric_config: Dict[str, Any]) -> Dict[str, str]:
        """Get freeform configuration file paths for a fabric."""
        freeform_paths = {}
        resources_freeform_dir = self.fabric_paths['freeform']
        
        if fabric_type == FabricType.VXLAN_EVPN:
            # Initialize paths - only banner has default, others are YAML-only
            freeform_paths = {
                'banner': str(resources_freeform_dir / "Banner.sh"),  # Default banner path
            }
            fabric_path = self.fabric_paths['fabric']
            # Read freeform paths from fabric configuration YAML
            if fabric_config:
                # Check Manageability section for AAA config
                manageability_config = fabric_config.get('Manageability', {})
                aaa_config = manageability_config.get('AAA Freeform Config', {})
                if isinstance(aaa_config, dict) and 'Freeform' in aaa_config:
                    freeform_paths['aaa'] = str(fabric_path / aaa_config['Freeform'])

                # Check Advanced section
                advanced_config = fabric_config.get('Advanced', {})
                
                # Check for other freeform configs
                for config_key, path_key in [
                    ('Leaf Freeform Config', 'leaf'),
                    ('Spine Freeform Config', 'spine'),
                    ('Intra-fabric Links Additional Config', 'intra_links'),
                    ('Banner', 'banner')
                ]:
                    config = advanced_config.get(config_key, {})
                    if isinstance(config, dict) and 'Freeform' in config:
                        freeform_paths[path_key] = str(fabric_path / config['Freeform'])

        elif fabric_type == FabricType.INTER_SITE_NETWORK:
            # Initialize paths - no defaults, only read from YAML
            if fabric_config:
                fabric_path = self.fabric_paths['inter_site']
                advanced_config = fabric_config.get('Advanced', {})
                # Check for Fabric Freeform Config
                fabric_freeform_config = advanced_config.get('Fabric Freeform', {})
                if isinstance(fabric_freeform_config, dict) and 'Freeform' in fabric_freeform_config:
                    freeform_paths['fabric'] = str(fabric_path / fabric_freeform_config['Freeform'])

                # Check for AAA Freeform Config
                aaa_freeform_config = advanced_config.get('AAA Freeform Config', {})
                if isinstance(aaa_freeform_config, dict) and 'Freeform' in aaa_freeform_config:
                    freeform_paths['aaa'] = str(fabric_path / aaa_freeform_config['Freeform'])

        return freeform_paths
    
    def _add_freeform_content_to_payload(self, payload_data: Dict[str, Any], fabric_type: FabricType, 
                                       freeform_paths: Dict[str, str], fabric_config: Dict[str, Any] = None) -> None:
        """Add freeform configuration content to the API payload."""
        if fabric_type == FabricType.VXLAN_EVPN:
            # AAA Freeform Config
            aaa_path = freeform_paths.get('aaa')
            if aaa_path and validate_file_exists(aaa_path):
                payload_data["AAA_SERVER_CONF"] = read_freeform_config(aaa_path)
            elif aaa_path:
                print(f"[Fabric] AAA freeform config file not found: {aaa_path}")
            
            # Leaf Freeform Config
            leaf_path = freeform_paths.get('leaf')
            if leaf_path and validate_file_exists(leaf_path):
                payload_data["EXTRA_CONF_LEAF"] = read_freeform_config(leaf_path)
            elif leaf_path:
                print(f"[Fabric] Leaf freeform config file not found: {leaf_path}")
            
            # Spine Freeform Config
            spine_path = freeform_paths.get('spine')
            if spine_path and validate_file_exists(spine_path):
                payload_data["EXTRA_CONF_SPINE"] = read_freeform_config(spine_path)
            elif spine_path:
                print(f"[Fabric] Spine freeform config file not found: {spine_path}")
            
            # Intra-fabric Links Additional Config
            intra_links_path = freeform_paths.get('intra_links')
            if intra_links_path and validate_file_exists(intra_links_path):
                payload_data["EXTRA_CONF_INTRA_LINKS"] = read_freeform_config(intra_links_path)
            elif intra_links_path:
                print(f"[Fabric] Intra-fabric links freeform config file not found: {intra_links_path}")
                
            # Banner config (always has default)
            banner_path = freeform_paths.get('banner')
            if banner_path and validate_file_exists(banner_path):
                banner_data = '`' + read_freeform_config(banner_path) + '`'
                payload_data["BANNER"] = banner_data
            else:
                print(f"[Fabric] Banner config file not found: {banner_path}")
            
            # iBGP Peer-Template Configs
            self._add_ibgp_template_configs(payload_data, fabric_config)

        elif fabric_type == FabricType.INTER_SITE_NETWORK:
            # Fabric Freeform Config
            fabric_path = freeform_paths.get('fabric')
            if fabric_path and validate_file_exists(fabric_path):
                payload_data["FABRIC_FREEFORM"] = read_freeform_config(fabric_path)
            elif fabric_path:
                print(f"[Fabric] Fabric freeform config file not found: {fabric_path}")
                
            # AAA Freeform Config
            aaa_path = freeform_paths.get('aaa')
            if aaa_path and validate_file_exists(aaa_path):
                payload_data["AAA_SERVER_CONF"] = read_freeform_config(aaa_path)
            elif aaa_path:
                print(f"[Fabric] AAA freeform config file not found: {aaa_path}")
    
    def _add_ibgp_template_configs(self, payload_data: Dict[str, Any], fabric_config: Dict[str, Any]) -> None:
        """Add iBGP Peer-Template configurations to the payload for VXLAN EVPN fabrics."""
        # Get BGP ASN from fabric config
        bgp_asn = get_nested_value(fabric_config, ('General Parameter', 'BGP ASN'))
        if not bgp_asn:
            print("[Fabric] Warning: No BGP ASN found in fabric config, skipping iBGP template configs")
            return
        
        # Template file paths
        template_dir = self.fabric_paths['template']
        ibgp_template_path = template_dir / "iBGP Peer-Template Config.sh"
        leaf_border_template_path = template_dir / "Leaf_Border_Border Gateway iBGP Peer-Template Config.sh"
        
        print(f"[Fabric] Processing iBGP Peer-Template Config path: {ibgp_template_path}")
        # Process iBGP Peer-Template Config
        if validate_file_exists(str(ibgp_template_path)):
            template_content = read_freeform_config(str(ibgp_template_path))
            # Replace $BGP_ASN with actual ASN value
            processed_content = template_content.replace('$BGP_ASN', str(bgp_asn))
            payload_data["IBGP_PEER_TEMPLATE"] = processed_content
            print(f"[Fabric] Added iBGP Peer-Template Config with BGP ASN: {bgp_asn}")
        else:
            print(f"[Fabric] iBGP Peer-Template Config file not found: {ibgp_template_path}")
        
        print(f"[Fabric] Processing Leaf Border iBGP Peer-Template Config path: {leaf_border_template_path}")
        # Process Leaf Border iBGP Peer-Template Config
        if validate_file_exists(str(leaf_border_template_path)):
            template_content = read_freeform_config(str(leaf_border_template_path))
            # Replace $BGP_ASN with actual ASN value
            processed_content = template_content.replace('$BGP_ASN', str(bgp_asn))
            payload_data["IBGP_PEER_TEMPLATE_LEAF"] = processed_content
            print(f"[Fabric] Added Leaf Border iBGP Peer-Template Config with BGP ASN: {bgp_asn}")
        else:
            print(f"[Fabric] Leaf Border iBGP Peer-Template Config file not found: {leaf_border_template_path}")
    
    def _build_complete_payload(self, fabric_name: str, use_freeform: bool = True) -> Tuple[Dict[str, Any], str, str]:
        """Build complete fabric payload for API operations."""
        # Determine fabric type
        fabric_type = self._determine_fabric_type_from_file(fabric_name)
        if not fabric_type:
            raise ValueError(f"Could not determine fabric type for '{fabric_name}'")
        
        # Get configuration paths based on fabric type
        if fabric_type == FabricType.VXLAN_EVPN:
            config_path = str(self.fabric_paths['fabric'] / f"{fabric_name}.yaml")
            defaults_path = str(self.fabric_paths['defaults'] / "cisco_vxlan.yaml")
            field_mapping_path = str(self.fabric_paths['field_mapping'] / "cisco_vxlan.yaml")
        elif fabric_type == FabricType.MULTI_SITE_DOMAIN:
            config_path = str(self.fabric_paths['multisite'] / f"{fabric_name}.yaml")
            defaults_path = str(self.fabric_paths['defaults'] / "cisco_multi-site.yaml")
            field_mapping_path = str(self.fabric_paths['field_mapping'] / "cisco_multi-site.yaml")
        elif fabric_type == FabricType.INTER_SITE_NETWORK:
            config_path = str(self.fabric_paths['inter_site'] / f"{fabric_name}.yaml")
            defaults_path = str(self.fabric_paths['defaults'] / "cisco_inter-site.yaml")
            field_mapping_path = str(self.fabric_paths['field_mapping'] / "cisco_inter-site.yaml")
        
        # Validate required files for VXLAN EVPN
        if fabric_type == FabricType.VXLAN_EVPN:
            required_files = [config_path, defaults_path, field_mapping_path]
            files_exist, missing_files = validate_configuration_files(required_files)
            if not files_exist:
                raise ValueError(f"Missing required configuration files: {missing_files}")
        
        # Load configurations
        fabric_config = load_yaml_file(config_path)
        defaults_config = load_yaml_file(defaults_path)
        field_mapping = load_yaml_file(field_mapping_path)
        
        if not all([fabric_config, defaults_config, field_mapping]):
            raise ValueError("Could not load required configurations or mappings")
        
        # Build payload
        payload_data = self._build_fabric_payload(
            fabric_config, defaults_config, field_mapping, fabric_name, fabric_type
        )
        # Add freeform content for supported fabric types
        if fabric_type in [FabricType.VXLAN_EVPN, FabricType.INTER_SITE_NETWORK]:
            freeform_paths = self._get_freeform_paths(fabric_name, fabric_type, fabric_config)
            
            # Log the freeform config paths being used
            if freeform_paths and use_freeform:
                print("[Fabric] Using freeform config files:")
                for config_type, path in freeform_paths.items():
                    if path:
                        print(f"  {config_type.title()}: {path}")
            
                self._add_freeform_content_to_payload(payload_data, fabric_type, freeform_paths, fabric_config)
        # Get template name from fabric type
        template_name = fabric_type.value
        
        return payload_data, template_name, fabric_name
    
    # --- Fabric CRUD Operations ---
    
    def create_fabric(self, fabric_name: str) -> bool:
        """Create a fabric using YAML configuration."""
        print(f"[Fabric] {self.GREEN}{self.BOLD}Creating fabric '{fabric_name}'{self.END}")

        try:
            fabric_data = fabric_api.get_fabrics()
            for fabric in fabric_data:
                if fabric['fabricName'] == fabric_name:
                    print(f"[Fabric] {self.YELLOW}Fabric '{fabric_name}' already exists.{self.END}")
                    return True

            payload_data, template_name, fabric_name_resolved = self._build_complete_payload(fabric_name)
            # Determine config file path for logging
            fabric_type = self._determine_fabric_type_from_file(fabric_name)
            if fabric_type == FabricType.VXLAN_EVPN:
                config_path = str(self.fabric_paths['fabric'] / f"{fabric_name}.yaml")
            elif fabric_type == FabricType.MULTI_SITE_DOMAIN:
                config_path = str(self.fabric_paths['multisite'] / f"{fabric_name}.yaml")
            elif fabric_type == FabricType.INTER_SITE_NETWORK:
                config_path = str(self.fabric_paths['inter_site'] / f"{fabric_name}.yaml")
            
            print(f"[Fabric] Using config file: {config_path}")
            
            return fabric_api.create_fabric(
                fabric_name=fabric_name_resolved,
                template_name=template_name,
                payload_data=payload_data
            )
        except Exception as e:
            print(f"[Fabric] Error creating fabric '{fabric_name}': {e}")
            return False
    
    def update_fabric(self, fabric_name: str) -> bool:
        """Update a fabric using YAML configuration."""
        print(f"[Fabric] {self.GREEN}{self.BOLD}Updating fabric '{fabric_name}'{self.END}")
        try:
            payload_data, template_name, fabric_name_resolved = self._build_complete_payload(fabric_name, True)
            # Determine config file path for logging
            fabric_type = self._determine_fabric_type_from_file(fabric_name)
            if fabric_type == FabricType.VXLAN_EVPN:
                config_path = str(self.fabric_paths['fabric'] / f"{fabric_name}.yaml")
            elif fabric_type == FabricType.MULTI_SITE_DOMAIN:
                config_path = str(self.fabric_paths['multisite'] / f"{fabric_name}.yaml")
            elif fabric_type == FabricType.INTER_SITE_NETWORK:
                config_path = str(self.fabric_paths['inter_site'] / f"{fabric_name}.yaml")
            
            print(f"[Fabric] Using config file: {config_path}")
            return fabric_api.update_fabric(
                fabric_name=fabric_name_resolved,
                template_name=template_name,
                payload_data=payload_data
            )
        except Exception as e:
            print(f"[Fabric] Error updating fabric '{fabric_name}': {e}")
            return False
    
    def delete_fabric(self, fabric_name: str) -> bool:
        """Delete a fabric."""
        print(f"[Fabric] {self.YELLOW}{self.BOLD}Deleting fabric '{fabric_name}'{self.END}")
        return fabric_api.delete_fabric(fabric_name)
    
    # --- Configuration Operations ---
    
    def recalculate_config(self, fabric_name: str) -> bool:
        """Recalculate fabric configuration."""
        print(f"[Fabric] {self.GREEN}{self.BOLD}Recalculating configuration for fabric '{fabric_name}'{self.END}")
        return fabric_api.recalculate_config(fabric_name)
    
    def get_pending_config(self, fabric_name: str) -> Optional[Dict[str, Any]]:
        """Get pending configuration with formatted output."""
        print(f"[Fabric] {self.GREEN}{self.BOLD}Getting pending configuration for fabric '{fabric_name}'{self.END}")
        return fabric_api.get_pending_config(fabric_name, save_files=True)

    def deploy_fabric(self, fabric_name: str) -> bool:
        """Deploy fabric configuration."""
        print(f"[Fabric] {self.GREEN}{self.BOLD}Deploying configuration for fabric '{fabric_name}'{self.END}")
        return fabric_api.deploy_fabric_config(fabric_name)
    
    # --- Multi-Site Domain Operations ---
    
    def add_to_msd(self, parent_fabric: str, child_fabric: str) -> bool:
        """Add a child fabric to a Multi-Site Domain."""
        print(f"[Fabric] {self.GREEN}{self.BOLD}Adding fabric '{child_fabric}' to MSD '{parent_fabric}'{self.END}")
        return fabric_api.add_MSD(parent_fabric, child_fabric)
    
    def remove_from_msd(self, parent_fabric: str, child_fabric: str, force: bool = False) -> bool:
        """Remove a child fabric from a Multi-Site Domain."""
        print(f"[Fabric] {self.YELLOW}{self.BOLD}Removing fabric '{child_fabric}' from MSD '{parent_fabric}'{self.END}")
        return fabric_api.remove_MSD(parent_fabric, child_fabric)