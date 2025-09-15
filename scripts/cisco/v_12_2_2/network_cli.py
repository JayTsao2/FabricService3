#!/usr/bin/env python3
"""
Network CLI - Command Line Interface for Network Operations

This script provides command-line access to network management functionality
using the unified NetworkManager class.
"""

import argparse
import sys
from pathlib import Path

# Setup module path
sys.path.append(str(Path(__file__).parent.absolute()))

from modules.network import NetworkManager

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Network Management CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python network_cli.py sync <fabric_name>                                   # Sync the network for the fabric with the yaml file
  python network_cli.py sync-attachments <fabric_name> <role> <switch_name>  # Sync attachments for a switch
  python network_cli.py create <fabric_name> <network_name>                  # Create a network
  python network_cli.py update <fabric_name> <network_name>                  # Update a network
  python network_cli.py delete <fabric_name> <network_name>                  # Delete a network
  python network_cli.py attach <fabric_name> <role> <switch_name>            # Attach networks to a switch
  python network_cli.py detach <fabric_name> <role> <switch_name>            # Detach networks from a switch
        """
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a network')
    create_parser.add_argument('fabric_name', help='Name of the fabric')
    create_parser.add_argument('network_name', help='Name of the network')
    
    # sync all command
    sync_all_parser = subparsers.add_parser('sync', help='Sync the network for the fabric with the yaml file')
    sync_all_parser.add_argument('fabric_name', help='Name of the fabric')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update a network')
    update_parser.add_argument('fabric_name', help='Name of the fabric')
    update_parser.add_argument('network_name', help='Name of the network')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a network')
    delete_parser.add_argument('fabric_name', help='Name of the fabric')
    delete_parser.add_argument('network_name', help='Name of the network')
    
    # Attach command
    attach_parser = subparsers.add_parser('attach', help='Attach networks to a switch')
    attach_parser.add_argument('fabric_name', help='Name of the fabric')
    attach_parser.add_argument('role', help='Role of the switch (leaf, spine, etc.)')
    attach_parser.add_argument('switch_name', help='Name of the switch')
    
    # Detach command
    detach_parser = subparsers.add_parser('detach', help='Detach networks from a switch')
    detach_parser.add_argument('fabric_name', help='Name of the fabric')
    detach_parser.add_argument('role', help='Role of the switch (leaf, spine, etc.)')
    detach_parser.add_argument('switch_name', help='Name of the switch')

    # Sync attachments command
    sync_attachments_parser = subparsers.add_parser('sync-attachments', help='Sync attachments for a switch')
    sync_attachments_parser.add_argument('fabric_name', help='Name of the fabric')
    sync_attachments_parser.add_argument('role', help='Role of the switch (leaf, spine, etc.)')
    sync_attachments_parser.add_argument('switch_name', help='Name of the switch')

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        # Create a single NetworkManager instance for all operations
        network_manager = NetworkManager()
        
        if args.command == 'create':
            success = network_manager.create_network(args.fabric_name, args.network_name)
            sys.exit(0 if success else 1)
            
        elif args.command == 'sync':
            success = network_manager.sync(args.fabric_name)
            sys.exit(0 if success else 1)
            
        elif args.command == 'update':
            success = network_manager.update_network(args.fabric_name, args.network_name)
            sys.exit(0 if success else 1)
            
        elif args.command == 'delete':
            success = network_manager.delete_network(args.fabric_name, args.network_name)
            sys.exit(0 if success else 1)
            
        elif args.command == 'attach':
            success = network_manager.attach_networks(args.fabric_name, args.role, args.switch_name)
            sys.exit(0 if success else 1)
            
        elif args.command == 'detach':
            success = network_manager.detach_networks(args.fabric_name, args.role, args.switch_name)
            sys.exit(0 if success else 1)
        
        elif args.command == 'sync-attachments':
            success = network_manager.sync_attachments(args.fabric_name, args.role, args.switch_name)
            sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
