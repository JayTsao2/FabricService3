#!/usr/bin/env python3
"""
VRF Management Module

This module provides unified VRF management functionality:
- VRF Creation, Update, and Deletion
- VRF Attachment/Detachment to switches
- YAML-based configuration management
- Template payload generation with field mapping

The module follows the same clean architecture as the network module,
with a single VRFManager class that handles all VRF operations.
"""

# Import the unified VRF manager
from .vrf import VRFManager

# Export the VRF manager for external use
__all__ = ['VRFManager']
