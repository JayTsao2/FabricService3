"""
VPC API Module

This module handles all VPC-related API operations including:
- Creating VPC pairs between switches
- Deleting VPC pairs
- Setting VPC policies
- Deleting VPC policies
"""

import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3
urllib3.disable_warnings(InsecureRequestWarning)
from .utils import *


def create_vpc_pair(peer_one_id, peer_two_id, use_virtual_peerlink=False):
    """Create a VPC pair using the vpcpair API endpoint.
    Args:
        peer_one_id: Serial number of the first switch
        peer_two_id: Serial number of the second switch
        use_virtual_peerlink: Whether to use a virtual peer link (default is False)
    """
    url = get_url("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/vpcpair")
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    payload = {
        "peerOneId": peer_one_id,
        "peerTwoId": peer_two_id,
        "useVirtualPeerlink": use_virtual_peerlink
    }
    
    r = requests.post(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name=f"Create VPC Pair for {peer_one_id} and {peer_two_id}")


def delete_vpc_pair(serial_number):
    """Delete VPC pair using the vpcpair API endpoint with serial number.
    Args:
        serial_number: Serial number of the switch to delete the VPC pair for
    """
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/vpcpair?serialNumber={serial_number}")
    headers = get_api_key_header()
    
    r = requests.delete(url, headers=headers, verify=False)
    return check_status_code(r, operation_name="Delete VPC Pair")

