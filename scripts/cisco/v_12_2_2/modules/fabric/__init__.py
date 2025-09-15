#!/usr/bin/env python3
"""
Fabric Management Module

This module provides unified fabric management functionality:
- Fabric Creation, Update, and Deletion
- Multi-Site Domain (MSD) operations
- Inter-Site Network (ISN) operations
- YAML-based configuration management
- Template payload generation with field mapping
- Freeform configuration support

The module follows the same clean architecture as the network and VRF modules,
with a single FabricManager class that handles all fabric operations.
"""

# Import the unified fabric manager and types
from .fabric import FabricManager
from .fabric import FabricType

# Export the fabric manager and types for external use
__all__ = ['FabricManager', 'FabricType']