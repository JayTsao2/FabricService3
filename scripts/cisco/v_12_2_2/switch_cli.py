#!/usr/bin/env python3
"""
Switch CLI - Command Line Interface for Switch Operations

This script provides command-line access to switch management functionality
using the unified SwitchManager class.

Usage:
    python switch_cli.py discover {fabric} {role} {switch} [--preserve]
    python switch_cli.py delete {fabric} {role} {switch}
    python switch_cli.py set-role {switch}
    python switch_cli.py change-ip {fabric} {role} {switch} {original-ip}/{mask} {new-ip}/{mask}
    python switch_cli.py set-freeform {fabric} {role} {switch}
    python switch_cli.py hostname {fabric} {role} {switch} {new-hostname}
    python switch_cli.py create-vpc {fabric}
    python switch_cli.py delete-vpc {fabric} {switchname}
    
Note: set-freeform creates a freeform policy for the switch using NDFC Policy API
Note: create-vpc creates VPC pairs and sets VPC policies for all switches in the fabric using NDFC APIs
Note: delete-vpc deletes VPC pairs for a specific switch in the fabric using NDFC VPC API
Note: set-vpc-policy configures VPC interface policies for all VPC pairs in the fabric
"""

import argparse
import sys
from pathlib import Path

# Setup module path
sys.path.append(str(Path(__file__).parent.absolute()))

from modules.switch import SwitchManager
from modules.vpc import VPCManager

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Switch Management CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python switch_cli.py discover <fabric_name> <role> <switch_name> [--preserve]  # Discover a switch
  python switch_cli.py delete <fabric_name> <role> <switch_name>                 # Delete a switch
  python switch_cli.py set-role <switch_name>                                    # Set switch role
  python switch_cli.py change-ip <fabric_name> <role> <switch_name> <original_ip>/<mask> <new_ip>/<mask>  # Change switch IP
  python switch_cli.py set-freeform <fabric_name> <role> <switch_name>           # Set freeform policy
  python switch_cli.py hostname <fabric_name> <role> <switch_name> <new_hostname>  # Change switch hostname
  python switch_cli.py create-vpc <fabric_name>                                  # Create VPC pairs
  python switch_cli.py delete-vpc <fabric_name> <switch_name>                    # Delete VPC pairs
        """
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Discover command
    discover_parser = subparsers.add_parser('discover', help='Discover a switch')
    discover_parser.add_argument('fabric_name', help='Name of the fabric')
    discover_parser.add_argument('role', help='Role of the switch (leaf, spine, border, etc.)')
    discover_parser.add_argument('switch_name', help='Name of the switch')
    discover_parser.add_argument('--preserve', action='store_true', 
                                help='Preserve existing configuration (default: False)')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a switch')
    delete_parser.add_argument('fabric_name', help='Name of the fabric')
    delete_parser.add_argument('role', help='Role of the switch (leaf, spine, border, etc.)')
    delete_parser.add_argument('switch_name', help='Name of the switch')
    
    # Set-role command
    setrole_parser = subparsers.add_parser('set-role', help='Set switch role')
    setrole_parser.add_argument('fabric_name', help='Name of the fabric')
    setrole_parser.add_argument('role', help='Role of the switch (leaf, spine, border, etc.)')
    setrole_parser.add_argument('switch_name', help='Name of the switch')
    
    # Change-ip command
    changeip_parser = subparsers.add_parser('change-ip', help='Change switch management IP')
    changeip_parser.add_argument('fabric_name', help='Name of the fabric')
    changeip_parser.add_argument('role', help='Role of the switch (leaf, spine, border, etc.)')
    changeip_parser.add_argument('switch_name', help='Name of the switch')
    changeip_parser.add_argument('original_ip', help='Original IP address with mask (e.g., 192.168.1.1/24)')
    changeip_parser.add_argument('new_ip', help='New IP address with mask (e.g., 192.168.1.2/24)')
    
    # Set-freeform command
    setfreeform_parser = subparsers.add_parser('set-freeform', help='Create freeform policy for switch')
    setfreeform_parser.add_argument('fabric_name', help='Name of the fabric')
    setfreeform_parser.add_argument('role', help='Role of the switch (leaf, spine, border, etc.)')
    setfreeform_parser.add_argument('switch_name', help='Name of the switch')
    
    # Hostname command
    hostname_parser = subparsers.add_parser('hostname', help='Change switch hostname')
    hostname_parser.add_argument('fabric_name', help='Name of the fabric')
    hostname_parser.add_argument('role', help='Role of the switch (leaf, spine, border, etc.)')
    hostname_parser.add_argument('switch_name', help='Name of the switch')
    hostname_parser.add_argument('new_hostname', help='New hostname for the switch')
    
    # Create VPC command
    createvpc_parser = subparsers.add_parser('create-vpc', help='Create VPC pairs and set policies for switches in a fabric')
    createvpc_parser.add_argument('fabric_name', help='Name of the fabric')
    
    # Delete VPC command
    deletevpc_parser = subparsers.add_parser('delete-vpc', help='Delete VPC pairs for a specific switch in a fabric')
    deletevpc_parser.add_argument('fabric_name', help='Name of the fabric')
    deletevpc_parser.add_argument('switch_name', help='Name of the switch')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        # Create SwitchManager instance
        switch_manager = SwitchManager()
        
        # Create VPCManager instance for VPC operations
        vpc_manager = VPCManager()
        
        if args.command == 'discover':
            # Discover switch with preserve config option
            success = switch_manager.discover_switch(
                args.fabric_name, 
                args.role, 
                args.switch_name,
                preserve_config=args.preserve
            )
        elif args.command == 'delete':
            # Delete switch
            success = switch_manager.delete_switch(
                args.fabric_name, 
                args.role, 
                args.switch_name
            )
        elif args.command == 'set-role':
            # Set switch role
            success = switch_manager.set_switch_role(
                args.fabric_name,
                args.role,
                args.switch_name
            )
        elif args.command == 'change-ip':
            # Change switch IP
            success = switch_manager.change_switch_ip(
                args.fabric_name,
                args.role,
                args.switch_name,
                args.original_ip,
                args.new_ip
            )
        elif args.command == 'set-freeform':
            # Apply freeform configuration
            success = switch_manager.set_switch_freeform(
                args.fabric_name,
                args.role,
                args.switch_name
            )
        elif args.command == 'hostname':
            # Change switch hostname
            success = switch_manager.change_switch_hostname(
                args.fabric_name,
                args.role,
                args.switch_name,
                args.new_hostname
            )
        elif args.command == 'create-vpc':
            # Create VPC pairs
            success = vpc_manager.create_vpc_pairs(args.fabric_name)
        elif args.command == 'delete-vpc':
            # Delete VPC pairs for specific switch
            success = vpc_manager.delete_vpc_pairs(args.fabric_name, args.switch_name)
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
