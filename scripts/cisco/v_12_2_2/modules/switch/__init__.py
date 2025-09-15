#!/usr/bin/env python3
"""
Switch Management Module - Core Components

Provides YAML-based switch management for Cisco NDFC:
- Switch discovery using switch YAML files
- Automatic payload generation from YAML configuration
- Integration with NDFC switch discovery API
"""

# Import the SwitchManager and related components from switch.py
from .switch import SwitchManager, VALID_SWITCH_ROLES

# --- Expose the classes and constants for easy access ---
__all__ = ['SwitchManager', 'VALID_SWITCH_ROLES']
