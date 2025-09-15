#!/usr/bin/env python3
"""
Interface Management Module - Core Components

Provides YAML-based interface management for Cisco NDFC:
- Interface configuration updates using switch YAML files
- Freeform configuration integration
- Policy-based interface management (access, trunk, routed)
"""

# Import the InterfaceManager and related components from interface.py
from .interface import InterfaceManager

# --- Expose the InterfaceManager class ---
__all__ = ['InterfaceManager']
