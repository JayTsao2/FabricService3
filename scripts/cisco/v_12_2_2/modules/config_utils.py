"""
Configuration Utilities - High-level utilities for fabric configuration management
Contains YAML processing, config merging, and build-specific functions.
Used by build_fabric.py for configuration processing.
"""
import json
import yaml
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

def load_yaml_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Load a YAML file and return its content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: YAML file not found at {filepath}")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file {filepath}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error loading YAML file {filepath}: {e}")
        return None

def load_text_file(filepath: str) -> Optional[str]:
    """Load a text file and return its content as a string."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Error: Text file not found at {filepath}")
        return None
    except Exception as e:
        print(f"Error loading text file {filepath}: {e}")
        return None

def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two configurations with override taking precedence.
    Used for merging default configs with specific fabric configurations.
    """
    if not isinstance(base_config, dict) or not isinstance(override_config, dict):
        return override_config if override_config else base_config
    
    merged = base_config.copy()
    for key, value in override_config.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value
    return merged

def flatten_config(nested_config: Dict[str, Any], parent_key: str = '', separator: str = '_') -> Dict[str, Any]:
    """
    Flatten a nested dictionary into a single-level dictionary.
    Used for converting hierarchical YAML configs to API-ready format.
    """
    if not isinstance(nested_config, dict):
        return {parent_key: nested_config} if parent_key else {}
    
    items = []
    for key, value in nested_config.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_config(value, new_key, separator).items())
        else:
            items.append((new_key, value))
    return dict(items)

def apply_field_mapping(config: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply field mapping to transform configuration keys to API format.
    Maps YAML configuration keys to NDFC API field names.
    """
    if not isinstance(mapping, dict):
        return config
    
    mapped_config = {}
    for key, value in config.items():
        if key in mapping and mapping[key] is not None:
            if isinstance(value, str) and (".sh" in value or "Banner" in value):
                continue
            mapped_config[mapping[key]] = value
        elif key not in mapping:
            # Keep unmapped fields as-is
            mapped_config[key] = value
    return mapped_config

def get_nested_value(config_dict: Dict[str, Any], keys: Tuple[str, ...]) -> Any:
    """
    Get a nested value from a dictionary using a tuple of keys.
    Safely traverses nested dictionary structures.
    """
    if not isinstance(config_dict, dict) or not keys:
        return None
    
    value = config_dict
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value

def validate_file_exists(filepath: str) -> bool:
    """Check if a file exists."""
    return Path(filepath).exists()

def validate_configuration_files(file_paths: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that all required configuration files exist.
    Returns tuple of (all_exist, missing_files).
    """
    missing_files = [f for f in file_paths if not Path(f).exists()]
    return len(missing_files) == 0, missing_files

def read_freeform_config(file_path: str) -> str:
    """
    Read the content of a freeform configuration file.
    Handles special formatting for banner configurations.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return content
    except FileNotFoundError:
        print(f"Warning: Freeform config file not found at {file_path}")
        return ""
    except Exception as e:
        print(f"Error reading freeform config {file_path}: {e}")
        return ""
