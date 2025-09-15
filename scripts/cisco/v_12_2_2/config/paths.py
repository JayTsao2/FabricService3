#!/usr/bin/env python3
"""
Project Path Configuration

Centralized path management for the entire project.
Provides consistent path handling across all modules.
"""

import os
from pathlib import Path
from typing import Dict

class ProjectPaths:
    """Centralized project path management."""
    
    def __init__(self):
        # Get project root from environment variable or calculate from current file
        self.project_root = self._get_project_root()
        
        # Core directories
        self.scripts_dir = self.project_root / "scripts" / "cisco" / "12.2.2"
        self.resources_dir = self.scripts_dir / "resources"
        self.network_configs_dir = self.project_root / "network_configs"
        
        # Resource subdirectories
        self.defaults_dir = self.resources_dir / "corp_defaults"
        self.field_mapping_dir = self.resources_dir / "_field_mapping"
        self.freeform_dir = self.resources_dir / "freeform"
        self.template_dir = self.resources_dir / "template"
        self.policy_dir = self.resources_dir / "policy"
        
        # Network config subdirectories
        self.fabric_configs_dir = self.network_configs_dir / "vxlan_evpn" / "fabric"
        self.inter_site_dir = self.network_configs_dir / "vxlan_evpn" / "inter-site_network"
        self.multisite_dir = self.network_configs_dir / "vxlan_evpn" / "multisite_deployment"
        
        self.switch_configs_dir = self.network_configs_dir / "node"
        
        self.network_configs_base_dir = self.network_configs_dir / "segment"
        self.interface_configs_dir = self.network_configs_dir / "5_interface"
        self.vrf_configs_dir = self.network_configs_dir / "segment"
        
        # API modules directory
        self.api_dir = self.scripts_dir / "api"
        self.modules_dir = self.scripts_dir / "modules"
    
    def _get_project_root(self) -> Path:
        """Get project root directory."""
        # Try environment variable first
        env_root = os.getenv('FABRIC_PROJECT_ROOT')
        if env_root:
            return Path(env_root)
        
        # Fallback to calculation from current file
        current_file = Path(__file__).resolve()
        # Assuming this file is at scripts/cisco/12.2.2/config/paths.py
        return current_file.parents[4]
    
    def get_fabric_paths(self) -> Dict[str, Path]:
        """Get all fabric-related paths."""
        return {
            'fabric': self.fabric_configs_dir,
            'defaults': self.defaults_dir,
            'field_mapping': self.field_mapping_dir,
            'freeform': self.freeform_dir,
            'inter_site': self.inter_site_dir,
            'multisite': self.multisite_dir,
            'template': self.template_dir
        }
    
    def get_vrf_paths(self) -> Dict[str, Path]:
        """Get all VRF-related paths."""
        return {
            'configs': self.vrf_configs_dir / "vrf.yaml",
            'defaults': self.defaults_dir / "vrf.yaml",
            'field_mapping': self.field_mapping_dir / "vrf.yaml"
        }
    
    def get_switch_paths(self) -> Dict[str, Path]:
        """Get all switch-related paths."""
        return {
            'configs': self.switch_configs_dir,
            'defaults': self.defaults_dir / "switch.yaml",
            'field_mapping': self.field_mapping_dir / "switch.yaml",
            'policy': self.policy_dir
        }
    
    def get_network_paths(self) -> Dict[str, Path]:
        """Get all network-related paths."""
        return {
            'configs': self.network_configs_base_dir / "network.yaml",
            'defaults': self.defaults_dir / "network.yaml",
            'field_mapping': self.field_mapping_dir / "network.yaml"
        }
    
    def get_interface_paths(self) -> Dict[str, Path]:
        """Get all interface-related paths."""
        return {
            'configs': self.switch_configs_dir,
            'defaults': self.defaults_dir / "interface.yaml",
            'field_mapping': self.field_mapping_dir / "interface.yaml"
        }
    
    def get_vpc_paths(self) -> Dict[str, Path]:
        """Get all VPC-related paths."""
        return {
            'configs': self.switch_configs_dir,
            'defaults': self.defaults_dir / "vpc.yaml",
            'field_mapping': self.field_mapping_dir / "vpc.yaml"
        }
    
    def validate_paths(self) -> bool:
        """Validate that all required paths exist."""
        required_paths = [
            self.project_root,
            self.scripts_dir,
            self.resources_dir,
            self.network_configs_dir
        ]
        
        missing_paths = []
        for path in required_paths:
            if not path.exists():
                missing_paths.append(str(path))
        
        if missing_paths:
            print("Missing required directories:")
            for path in missing_paths:
                print(f"  - {path}")
            return False
        
        return True
    
    def create_missing_directories(self) -> None:
        """Create missing directories if they don't exist."""
        directories = [
            self.vrf_configs_dir,
            self.fabric_configs_dir,
            self.switch_configs_dir,
            self.network_configs_base_dir,
            self.interface_configs_dir,
            self.defaults_dir,
            self.field_mapping_dir,
            self.freeform_dir,
            self.template_dir,
            self.policy_dir
        ]
        
        for directory in directories:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {directory}")

# Global instance for easy access
project_paths = ProjectPaths()
