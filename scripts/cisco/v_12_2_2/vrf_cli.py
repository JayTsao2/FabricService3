#!/usr/bin/env python3
"""
VRF Management CLI

This script provides a unified command-line interface for VRF operations.
Uses VRFManager for clean, consistent VRF management.

Example usage:
    python vrf_cli.py create <fabric_name> <vrf_name>
    python vrf_cli.py update <fabric_name> <vrf_name>
    python vrf_cli.py delete <fabric_name> <vrf_name>
    python vrf_cli.py attach <fabric_name> <switch_role> <switch_name>
    python vrf_cli.py detach <fabric_name> <switch_role> <switch_name>
    python vrf_cli.py sync <fabric_name>
"""

import argparse
import sys
import os

# Add the modules directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

from modules.vrf import VRFManager


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='VRF Management CLI - Unified VRF operations using VRFManager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python vrf_cli.py sync <fabric_name>                                          # Synchronize all VRFs for a fabric
  python vrf_cli.py sync-attachments <fabric_name> <switch_role> <switch_name>  # Sync attachments for a switch
  python vrf_cli.py create <fabric_name> <vrf_name>                             # Create a VRF in specified fabric
  python vrf_cli.py update <fabric_name> <vrf_name>                             # Update a VRF in specified fabric
  python vrf_cli.py delete <fabric_name> <vrf_name>                             # Delete a VRF from specified fabric
  python vrf_cli.py attach <fabric_name> <switch_role> <switch_name>            # Attach VRF to a specific switch
  python vrf_cli.py detach <fabric_name> <switch_role> <switch_name>            # Detach VRF from a specific switch
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create VRF command
    create_parser = subparsers.add_parser('create', help='Create a VRF')
    create_parser.add_argument('fabric_name', help='Name of the fabric to create VRF in')
    create_parser.add_argument('vrf_name', help='Name of the VRF to create')
    
    # Update VRF command
    update_parser = subparsers.add_parser('update', help='Update a VRF')
    update_parser.add_argument('fabric_name', help='Name of the fabric to update VRF in')
    update_parser.add_argument('vrf_name', help='Name of the VRF to update')
    
    # Delete VRF command
    delete_parser = subparsers.add_parser('delete', help='Delete a VRF')
    delete_parser.add_argument('fabric_name', help='Name of the fabric to delete VRF from')
    delete_parser.add_argument('vrf_name', help='Name of the VRF to delete')
    
    # Attach VRF command
    attach_parser = subparsers.add_parser('attach', help='Attach VRF to a specific switch')
    attach_parser.add_argument('fabric_name', help='Name of the fabric')
    attach_parser.add_argument('switch_role', help='Role of the switch (leaf, spine, border_gateway)')
    attach_parser.add_argument('switch_name', help='Name of the switch')
    attach_parser.add_argument('vrf_name', help='Name of the VRF to attach')
    
    # Detach VRF command
    detach_parser = subparsers.add_parser('detach', help='Detach VRF from a specific switch')
    detach_parser.add_argument('fabric_name', help='Name of the fabric')
    detach_parser.add_argument('switch_role', help='Role of the switch (leaf, spine, border_gateway)')
    detach_parser.add_argument('switch_name', help='Name of the switch')
    detach_parser.add_argument('vrf_name', help='Name of the VRF to detach')
    
    # Sync VRFs command
    sync_parser = subparsers.add_parser('sync', help='Synchronize all VRFs for a fabric (delete unwanted, update existing, create missing)')
    sync_parser.add_argument('fabric_name', help='Name of the fabric to synchronize VRFs for')

    # Sync attachments command
    sync_attachments_parser = subparsers.add_parser('sync-attachments', help='Sync attachments for a switch')
    sync_attachments_parser.add_argument('fabric_name', help='Name of the fabric')
    sync_attachments_parser.add_argument('switch_role', help='Role of the switch (leaf, spine, border_gateway)')
    sync_attachments_parser.add_argument('switch_name', help='Name of the switch')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize VRF Manager
    vrf_manager = VRFManager()
    
    try:
        success = False
        
        if args.command == 'create':
            success = vrf_manager.create_vrf(args.fabric_name, args.vrf_name)
            
        elif args.command == 'update':
            success = vrf_manager.update_vrf(args.fabric_name, args.vrf_name)
            
        elif args.command == 'delete':
            success = vrf_manager.delete_vrf(args.fabric_name, args.vrf_name)
            
        elif args.command == 'attach':
            success = vrf_manager.attach_vrf(args.fabric_name, args.switch_role, args.switch_name, args.vrf_name)

        elif args.command == 'detach':
            success = vrf_manager.detach_vrf(args.fabric_name, args.switch_role, args.switch_name, args.vrf_name)

        elif args.command == 'sync':
            success = vrf_manager.sync(args.fabric_name)
        
        elif args.command == 'sync-attachments':
            success = vrf_manager.sync_attachments(args.fabric_name, args.switch_role, args.switch_name)
            
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
            success = False
        
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
