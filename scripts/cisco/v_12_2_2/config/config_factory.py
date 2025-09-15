#!/usr/bin/env python3
"""
Configuration Factory

Provides configuration objects for different modules.
Centralizes configuration creation and management.
"""

from .paths import project_paths

class ConfigFactory:
    """Factory for creating configuration objects."""
    
    @staticmethod
    def create_vrf_config():
        """Create VRF configuration."""
        paths = project_paths.get_vrf_paths()
        # Return simple configuration object instead of importing VRFConfig
        class VRFConfig:
            def __init__(self, config_path, defaults_path, field_mapping_path):
                self.config_path = config_path
                self.defaults_path = defaults_path
                self.field_mapping_path = field_mapping_path
        
        return VRFConfig(
            config_path=str(paths['configs']),
            defaults_path=str(paths['defaults']),
            field_mapping_path=str(paths['field_mapping'])
        )
    
    @staticmethod
    def create_switch_config():
        """Create switch configuration."""
        paths = project_paths.get_switch_paths()
        # Return a dictionary since switch module doesn't have a specific config class
        return {
            'configs_dir': paths['configs'],
            'defaults_path': paths['defaults'],
            'field_mapping_path': paths['field_mapping'],
            'policy_dir': paths['policy']
        }
    
    @staticmethod
    def create_network_config():
        """Create network configuration."""
        paths = project_paths.get_network_paths()
        return {
            'config_path': paths['configs'],
            'defaults_path': paths['defaults'],
            'field_mapping_path': paths['field_mapping']
        }
    
    @staticmethod
    def create_interface_config():
        """Create interface configuration."""
        paths = project_paths.get_interface_paths()
        return {
            'configs_dir': paths['configs'],
            'defaults_path': paths['defaults'],
            'field_mapping_path': paths['field_mapping']
        }
    
    @staticmethod
    def create_vpc_config():
        """Create VPC configuration."""
        paths = project_paths.get_vpc_paths()
        return {
            'configs_dir': paths['configs'],
            'defaults_path': paths['defaults'],
            'field_mapping_path': paths['field_mapping']
        }
    
    @staticmethod
    def get_fabric_paths():
        """Get fabric-related paths."""
        return project_paths.get_fabric_paths()
    
# Global factory instance
config_factory = ConfigFactory()
