import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3
urllib3.disable_warnings(InsecureRequestWarning)
from .utils import *
import json
import os
from typing import Dict, Any, List

def get_VRFs(fabric):
    # range = show the vrfs from 0 to 9999
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/vrfs")
    headers = get_api_key_header()
    headers["range"] = f"0-9999"
    r = requests.get(url, headers=headers, verify=False)
    check_status_code(r, f"Get VRFs for fabric {fabric}")
    return r.json()

def create_vrf(fabric_name: str, vrf_payload: Dict[str, Any], template_payload: Dict[str, Any]) -> bool:
    """
    Create a VRF using direct payload data.
    
    Args:
        fabric_name: Name of the fabric
        vrf_payload: Main VRF configuration payload
        template_payload: VRF template configuration payload
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        headers = get_api_key_header()
        headers['Content-Type'] = 'application/json'
        
        # Convert template payload to JSON string
        vrf_payload["vrfTemplateConfig"] = json.dumps(template_payload)
        
        url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs")
        r = requests.post(url, headers=headers, json=vrf_payload, verify=False)
        return check_status_code(r, operation_name=f"Create VRF {vrf_payload.get('vrfName', 'unknown')}")
    except Exception as e:
        print(f"Error creating VRF {vrf_payload.get('vrfName', 'unknown')}: {e}")
        return False

def update_vrf(fabric_name: str, vrf_name: str, vrf_payload: Dict[str, Any], template_payload: Dict[str, Any]) -> bool:
    """
    Update a VRF using direct payload data.
    
    Args:
        fabric_name: Name of the fabric
        vrf_name: Name of the VRF to update
        vrf_payload: Main VRF configuration payload
        template_payload: VRF template configuration payload
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        headers = get_api_key_header()
        headers['Content-Type'] = 'application/json'
        
        # Convert template payload to JSON string
        vrf_payload["vrfTemplateConfig"] = json.dumps(template_payload)
        
        url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs/{vrf_name}")
        
        r = requests.put(url, headers=headers, json=vrf_payload, verify=False)
        return check_status_code(r, operation_name=f"Update VRF {vrf_name}")

    except Exception as e:
        print(f"Error updating VRF {vrf_name}: {e}")
        return False

def delete_vrf(fabric_name: str, vrf_name: str) -> bool:
    """
    Delete a VRF from a fabric.
    
    Args:
        fabric_name: Name of the fabric
        vrf_name: Name of the VRF to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs/{vrf_name}")
        headers = get_api_key_header()
        
        r = requests.delete(url, headers=headers, verify=False)
        return check_status_code(r, operation_name=f"Delete VRF {vrf_name}")
        
    except Exception as e:
        print(f"Error deleting VRF {vrf_name}: {e}")
        return False

def get_vrf_attachment(fabric: str, vrf_dir: str = "vrfs", save_files: bool = True) -> List[Dict[str, Any]]:
    """
    Get VRF attachment details.
    
    Args:
        fabric: Name of the fabric
        vrf_dir: Directory to save attachment files (default: "vrfs")
        vrfname: Name of the VRF
        save_files: Whether to save attachment files to disk (default: True)
        
    Returns:
        List[Dict[str, Any]]: List of VRF attachment data
    """
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/vrfs/attachments")
    headers = get_api_key_header()
    r = requests.get(url, headers=headers, verify=False)
    check_status_code(r, f"Get VRF Attachments for fabric {fabric}")

    attachments = r.json()
    
    # Only save files if requested
    if save_files:
        if not os.path.exists(vrf_dir):
            os.makedirs(vrf_dir)
        if not os.path.exists(f"{vrf_dir}/attachments"):
            os.makedirs(f"{vrf_dir}/attachments")
        filename = f"{vrf_dir}/attachments/{fabric}.json"
        with open(filename, "w") as f:
            json.dump(attachments, f, indent=4)
            print(f"VRF attachments for fabric {fabric} are saved to {filename}")

    # Return the attachments data for programmatic use
    return attachments

def update_vrf_attachment(fabric_name: str, attachment_payload: Dict[str, Any]) -> bool:
    """
    Update VRF attachment using direct payload data.
    
    Args:
        fabric_name: Name of the fabric
        attachment_payload: VRF attachment configuration payload
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        headers = get_api_key_header()
        headers['Content-Type'] = 'application/json'
        
        url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs/attachments")
        
        r = requests.post(url, headers=headers, json=attachment_payload, verify=False)
        return check_status_code(r, operation_name=f"Update VRF Attachment")

    except Exception as e:
        print(f"Error updating VRF attachment: {e}")
        return False
