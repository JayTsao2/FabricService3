#!/usr/bin/env python3
"""
Fabric Management CLI

This script provides a simple command-line interface to the fabric module.
It demonstrates how to use the separated create, update, delete, and MSD functionality.

Usage:
    python fabric_cli.py create <fabric_name>
    python fabric_cli.py update <fabric_name>
    python fabric_cli.py delete <fabric_name>
    python fabric_cli.py recalculate <fabric_name>
    python fabric_cli.py get-pending <fabric_name>
    python fabric_cli.py deploy <fabric_name>
    python fabric_cli.py add-msd <parent_msd> <child_fabric>
    python fabric_cli.py remove-msd <parent_msd> <child_fabric>
"""

import sys
from pathlib import Path

# Add current directory to path to access modules
sys.path.append(str(Path(__file__).parent.absolute()))

import argparse
from modules.fabric import FabricManager

# Initialize the fabric manager (singleton pattern)
fabric_manager = FabricManager()

def create_fabric_command(fabric_name: str):
    """Handle fabric creation command."""
    success = fabric_manager.create_fabric(fabric_name)
    return 0 if success else 1

def update_fabric_command(fabric_name: str):
    """Handle fabric update command."""
    success = fabric_manager.update_fabric(fabric_name)
    return 0 if success else 1

def delete_fabric_command(fabric_name: str):
    """Handle fabric deletion command."""
    success = fabric_manager.delete_fabric(fabric_name)
    return 0 if success else 1

def recalculate_fabric_command(fabric_name: str):
    """Handle fabric recalculation command."""
    success = fabric_manager.recalculate_config(fabric_name)
    return 0 if success else 1

def deploy_fabric_command(fabric_name: str):
    """Handle fabric deployment command."""
    success = fabric_manager.deploy_fabric(fabric_name)
    return 0 if success else 1

def get_pending_fabric_command(fabric_name: str):
    """Handle getting pending configuration command."""
    result = fabric_manager.get_pending_config(fabric_name)
    return 0 if result is not None else 1

def add_msd_command(parent_fabric: str, child_fabric: str):
    """Handle adding child fabric to MSD command."""
    success = fabric_manager.add_to_msd(parent_fabric, child_fabric)
    return 0 if success else 1

def remove_msd_command(parent_fabric: str, child_fabric: str):
    """Handle removing specific child fabric from MSD command."""
    success = fabric_manager.remove_from_msd(parent_fabric, child_fabric)
    return 0 if success else 1

def main():
    parser = argparse.ArgumentParser(
        description="Fabric Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fabric_cli.py create <fabric_name>                  # Create a specific fabric
  python fabric_cli.py update <fabric_name>                  # Update a specific fabric
  python fabric_cli.py delete <fabric_name>                  # Delete a specific fabric
  python fabric_cli.py recalculate <fabric_name>             # Recalculate fabric configuration
  python fabric_cli.py get-pending <fabric_name>             # Get pending configuration (saves to pending.txt)
  python fabric_cli.py deploy <fabric_name>                  # Deploy fabric configuration
  python fabric_cli.py add-msd <parent_msd> <child_fabric>   # Add child fabric to MSD
  python fabric_cli.py remove-msd <parent_msd> <child_fabric> # Remove specific child fabric from MSD
"""
    )
    
    parser.add_argument('command', 
                       choices=['create', 'update', 'delete', 'recalculate', 'get-pending', 'deploy', 'add-msd', 'remove-msd'],
                       help='Command to execute')
    
    # Handle different argument patterns for different commands
    if len(sys.argv) > 1 and sys.argv[1] in ['add-msd', 'remove-msd']:
        parser.add_argument('parent_fabric', 
                           help='Parent MSD fabric name')
        parser.add_argument('child_fabric',
                           help='Child fabric name to add/remove to/from MSD')
    else:
        parser.add_argument('fabric_name', 
                           help='Name of the fabric to create/update/delete')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'create':
            return create_fabric_command(args.fabric_name)
            
        elif args.command == 'update':
            return update_fabric_command(args.fabric_name)
            
        elif args.command == 'delete':
            return delete_fabric_command(args.fabric_name)
            
        elif args.command == 'recalculate':
            return recalculate_fabric_command(args.fabric_name)
            
        elif args.command == 'get-pending':
            return get_pending_fabric_command(args.fabric_name)
            
        elif args.command == 'deploy':
            return deploy_fabric_command(args.fabric_name)
            
        elif args.command == 'add-msd':
            return add_msd_command(args.parent_fabric, args.child_fabric)
            
        elif args.command == 'remove-msd':
            return remove_msd_command(args.parent_fabric, args.child_fabric)
            
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
