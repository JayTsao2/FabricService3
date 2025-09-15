import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3
urllib3.disable_warnings(InsecureRequestWarning)
from .utils import *
import json
from typing import Dict, Any, Optional

def get_fabrics(save_files: bool = False) -> Optional[Dict[str, Any]]:
    """Get all fabrics from NDFC."""
    url = get_url("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics")
    headers = get_api_key_header()

    r = requests.get(url=url, headers=headers, verify=False)
    success = check_status_code(r, operation_name="Get Fabrics")
    
    if success:
        fabrics = r.json()
        if save_files:
            with open("fabrics.json", "w") as f:
                json.dump(fabrics, f, indent=4)
        return fabrics
    else:
        return None

def get_fabric(fabric_name: str, save_files: bool = False) -> Optional[Dict[str, Any]]:
    """Get specific fabric configuration from NDFC."""
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric_name}")
    
    headers = get_api_key_header()

    r = requests.get(url=url, headers=headers, verify=False)
    success = check_status_code(r, f"Get Fabric {fabric_name}")
    
    if success:
        fabric_data = r.json()
        if save_files:
            with open(f"{fabric_name}.json", "w") as f:
                json.dump(fabric_data, f, indent=4)
        return fabric_data
    else:
        return None

def delete_fabric(fabric_name: str) -> bool:
    """Delete a fabric from NDFC."""
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric_name}")

    headers = get_api_key_header()
    r = requests.delete(url=url, headers=headers, verify=False)

    return check_status_code(r, operation_name=f"Delete Fabric {fabric_name}")

def create_fabric(fabric_name: str, template_name: str, payload_data: Dict[str, Any]) -> bool:
    """
    Create a fabric using provided payload data.
    
    Args:
        fabric_name: Name of the fabric to create
        template_name: Template type (Easy_Fabric, External_Fabric, MSD_Fabric, etc.)
        payload_data: Complete nvPairs payload data
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Clean payload by removing invalid fields
    invalid_fields = ["USE_LINK_LOCAL", "ISIS_OVERLOAD_ENABLE", "ISIS_P2P_ENABLE", 
                    "PNP_ENABLE_INTERNAL", "DOMAIN_NAME_INTERNAL"]
    cleaned_payload = {k: v for k, v in payload_data.items() if k not in invalid_fields}
    
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric_name}/{template_name}")
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    r = requests.post(url, headers=headers, data=json.dumps(cleaned_payload), verify=False)

    return check_status_code(r, operation_name=f"Create Fabric {fabric_name}")

def update_fabric(fabric_name: str, template_name: str, payload_data: Dict[str, Any]) -> bool:
    """
    Update a fabric using provided payload data.
    
    Args:
        fabric_name: Name of the fabric to update
        template_name: Template type (Easy_Fabric, External_Fabric, MSD_Fabric, etc.)
        payload_data: Complete nvPairs payload data
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Clean payload by removing invalid fields
    invalid_fields = ["USE_LINK_LOCAL", "ISIS_OVERLOAD_ENABLE", "ISIS_P2P_ENABLE", 
                        "PNP_ENABLE_INTERNAL", "DOMAIN_NAME_INTERNAL"]
    cleaned_payload = {k: v for k, v in payload_data.items() if k not in invalid_fields}
    
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric_name}/{template_name}")
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    r = requests.put(url, headers=headers, data=json.dumps(cleaned_payload), verify=False)

    return check_status_code(r, operation_name=f"Update Fabric {fabric_name}")

def recalculate_config(fabric_name: str) -> bool:
    """Recalculate fabric configuration."""
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric_name}/config-save")
    headers = get_api_key_header()
    r = requests.post(url, headers=headers, verify=False)

    return check_status_code(r, operation_name=f"Recalculate Config for {fabric_name}")

def deploy_fabric_config(fabric_name: str) -> bool:
    """Deploy fabric configuration."""
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric_name}/config-deploy")
    headers = get_api_key_header()
    r = requests.post(url, headers=headers, verify=False)

    return check_status_code(r, operation_name=f"Deploy Fabric Config for {fabric_name}")

def get_pending_config(fabric_name: str, save_files: bool = False) -> Optional[Dict[str, Any]]:
    """Get pending configuration for a fabric and save in formatted text file."""
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric_name}/config-preview")
    headers = get_api_key_header()
    
    r = requests.get(url=url, headers=headers, verify=False)
    
    if not check_status_code(r, operation_name=f"Get Pending Config for {fabric_name}"):
        return None
    
    data = r.json()
    
    if save_files:
        txt_filename = f"{fabric_name}_pending.txt"
        with open(txt_filename, "w") as f:
            for switch_data in data:
                switch_name = switch_data.get("switchName", "Unknown")
                pending_config = switch_data.get("pendingConfig", [])
                
                f.write(f"- {switch_name}\n")
                for command in pending_config:
                    f.write(f"{command}\n")
                f.write("===\n")
        
        print(f"Formatted pending configuration for fabric {fabric_name} saved to {txt_filename}")
    return data

def add_MSD(parent_fabric_name: str, child_fabric_name: str) -> bool:
    """Add a child fabric to a Multi-Site Domain."""
    url = get_url("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/msdAdd")
    headers = get_api_key_header()
    payload = {
        "destFabric": parent_fabric_name,
        "sourceFabric": child_fabric_name
    }
    r = requests.post(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name=f"Add MSD for {parent_fabric_name} to {child_fabric_name}")

def remove_MSD(parent_fabric_name: str, child_fabric_name: str) -> bool:
    """Remove a child fabric from a Multi-Site Domain."""
    url = get_url("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/msdExit")
    headers = get_api_key_header()
    payload = {
        "destFabric": parent_fabric_name,
        "sourceFabric": child_fabric_name
    }
    r = requests.post(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name=f"Remove MSD for {parent_fabric_name} from {child_fabric_name}")
