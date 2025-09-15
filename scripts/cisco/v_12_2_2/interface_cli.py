#!/usr/bin/env python3
"""
Interface CLI - Command Line Interface for Interface Operations

This script provides command-line access to interface management functionality
using the unified InterfaceManager class.
"""

import argparse
import sys
from pathlib import Path

# Setup module path
sys.path.append(str(Path(__file__).parent.absolute()))

from modules.interface import InterfaceManager

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Interface Management CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python interface_cli.py update Site1 leaf Site1-L1    # Update switch interfaces
  python interface_cli.py deploy Site1 leaf Site1-L1    # Deploy switch interfaces  
  python interface_cli.py check Site1 leaf Site1-L1     # Check interface operation status
        """
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    subparsers.required = True
    
    # Update subcommand
    update_parser = subparsers.add_parser('update', help='Update switch interfaces from YAML configuration')
    update_parser.add_argument('fabric_name', help='Name of the fabric')
    update_parser.add_argument('role', help='Role of the switch (leaf, spine, etc.)')
    update_parser.add_argument('switch_name', help='Name of the switch')
    
    # Deploy subcommand
    deploy_parser = subparsers.add_parser('deploy', help='Deploy switch interface configuration')
    deploy_parser.add_argument('fabric_name', help='Name of the fabric')
    deploy_parser.add_argument('role', help='Role of the switch (leaf, spine, etc.)')
    deploy_parser.add_argument('switch_name', help='Name of the switch')
    
    # Check subcommand
    check_parser = subparsers.add_parser('check', help='Check interface operation status')
    check_parser.add_argument('fabric_name', help='Name of the fabric')
    check_parser.add_argument('role', help='Role of the switch (leaf, spine, etc.)')
    check_parser.add_argument('switch_name', help='Name of the switch')
    
    args = parser.parse_args()
    
    try:
        # Call the appropriate handler function
        interface_manager = InterfaceManager()
        if args.command == 'update':
            success = interface_manager.update_switch_interfaces(
                args.fabric_name,
                args.role,
                args.switch_name
            )

        elif args.command == 'deploy':
            success = interface_manager.deploy_switch_interfaces(
                args.fabric_name,
                args.role,
                args.switch_name
            )
        elif args.command == 'check':
            success = interface_manager.check_interface_operation_status(
                args.fabric_name,
                args.role,
                args.switch_name
            )

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
