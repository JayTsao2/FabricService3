#!/usr/bin/env python3
"""
Configuration Package

Centralized configuration management for the fabric automation project.
"""

from .paths import project_paths
from .config_factory import config_factory

__all__ = ['project_paths', 'config_factory']
