import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3
urllib3.disable_warnings(InsecureRequestWarning)
from .utils import *
import json
import os
from typing import Dict, Any, List

def update_interface(policy: str, interfaces_payload: List[Dict[str, Any]]) -> bool:
    """
    Update interface configuration using NDFC API.
    
    Args:
        policy: Interface policy type (e.g., "int_access_host", "int_trunk_host", "int_routed_host")
        interfaces_payload: List of interface configurations
    
    Returns:
        Boolean indicating success
    """
    url = get_url("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface")
    headers = get_api_key_header()
    
    payload = {
        "policy": policy,
        "interfaces": interfaces_payload
    }
    r = requests.put(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name=f"Update Interfaces")

def create_interface(policy: str, interfaces_payload: List[Dict[str, Any]]) -> bool:
    """
    Create interface configuration using NDFC API (POST method).
    
    Args:
        policy: Interface policy type (e.g., "int_port_channel_trunk_host")
        interfaces_payload: List of interface configurations
    
    Returns:
        Boolean indicating success
    """
    url = get_url("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface")
    headers = get_api_key_header()
    
    payload = {
        "policy": policy,
        "interfaces": interfaces_payload
    }
    
    # Add interfaceType for port channel interfaces
    if "port_channel" in policy.lower():
        payload["interfaceType"] = "INTERFACE_PORT_CHANNEL"
    
    r = requests.post(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name=f"Create Interfaces")

def delete_interfaces(interfaces_payload: List[Dict[str, Any]]) -> bool:
    """
    Delete interfaces using NDFC API (DELETE method).
    
    Args:
        interfaces_payload: List of interfaces to delete. Format: [{"ifName":"Port-channel1","serialNumber":"SAL2008ZAXX"}]
    
    Returns:
        Boolean indicating success
    """
    url = get_url("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface")
    headers = get_api_key_header()
    
    r = requests.delete(url, headers=headers, json=interfaces_payload, verify=False)
    return check_status_code(r, operation_name=f"Delete Interfaces")

def get_interfaces(serial_number: str = None, if_name: str = None, template_name: str = None, 
                  save_files: bool = False) -> List[Dict[str, Any]]:
    """
    Get interfaces from NDFC API with optional filtering.
    
    Args:
        serial_number: Filter by device serial number
        if_name: Filter by specific interface name (e.g., "Ethernet1/1")
        template_name: Filter by policy template (e.g., "int_trunk_host", "int_access_host", "int_routed_host")
        save_files: If True, save the interface data to files in the current directory
    
    Returns:
        List of interface data from the API
    """
    url = get_url("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface")
    headers = get_api_key_header()
    
    # Build query parameters
    query_params = {}
    if serial_number:
        query_params["serialNumber"] = serial_number
    if if_name:
        query_params["ifName"] = if_name
    if template_name:
        query_params["templateName"] = template_name
    r = requests.get(url, headers=headers, params=query_params, verify=False)
    check_status_code(r, operation_name="Get Interfaces")
    
    if save_files:
        # Create directory for interface files
        interface_dir = "interfaces"
        os.makedirs(interface_dir, exist_ok=True)
        
        interfaces_data = r.json()
        with open(os.path.join(interface_dir, "interfaces.json"), 'w', encoding='utf-8') as f:
            json.dump(interfaces_data, f, indent=2, ensure_ascii=False)
        print(f"Interfaces data saved to {interface_dir}/interfaces.json")
    
    return r.json()

def change_interface_admin_status(serial_number: str, if_name: str, payload: Dict[str, Any], admin_status: bool) -> bool:
    """
    Change the administrative status of an interface using NDFC API (POST method).

    Args:
        serial_number: Device serial number
        if_name: Interface name (e.g., "Ethernet1/1")
        admin_status: New administrative status (e.g., True or False)

    Returns:
        Boolean indicating success
    """
    status = "Noshut"
    if admin_status == True:
        status = "shut"
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface/adminstatus/{status}/onlySave")
    headers = get_api_key_header()

    payload = [{
        "serialNumber": serial_number,
        "ifName": if_name,
        "adminStatus": admin_status
    }]

    r = requests.post(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name=f"Change Interface Admin Status")

def get_interface_details(serial_number: str, if_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific interface using NDFC API (GET method).

    Args:
        serial_number: Device serial number
        if_name: Interface name (e.g., "Ethernet1/1")

    Returns:
        Dictionary containing interface details
    """
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface/detail/filter")
    headers = get_api_key_header()
    query_params = {
        "serialNumber": serial_number,
        "ifName": if_name
    }

    r = requests.get(url, headers=headers, params=query_params, verify=False)
    check_status_code(r, operation_name="Get Interface Details")

    return r.json()

def deploy_interface(serial_number: str, if_name: str) -> bool:
    """
    Deploy the interface configuration using NDFC API (POST method).

    Args:
        serial_number: Device serial number
        if_name: Interface name (e.g., "Ethernet1/1")

    Returns:
        Boolean indicating success
    """
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface/deploy")
    headers = get_api_key_header()
    payload = [{
        "serialNumber": serial_number,
        "ifName": if_name
    }]

    r = requests.post(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name=f"Deploy Interface")
