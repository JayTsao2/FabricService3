import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3
urllib3.disable_warnings(InsecureRequestWarning)
from .utils import *
import json
from dotenv import load_dotenv
from typing import Dict, Any, List

def get_switches(fabric, save_files: bool = False) -> List[Dict[str, Any]]:
    # range = show the switches from 0 to {range}
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/inventory/switchesByFabric")
    headers = get_api_key_header()
    r = requests.get(url, headers=headers, verify=False)
    check_status_code(r, f"Get Switches for fabric {fabric}")

    switches = r.json()
    if save_files:
        if not switches:
            print(f"No switches found for fabric {fabric}.")
            return
        
        # Create a directory for the fabric if it doesn't exist
        fabric_dir = f"switches/{fabric}"
        if not os.path.exists(fabric_dir):
            os.makedirs(fabric_dir)
        
        # Save each switch to a separate file
        for switch in switches:
            serial_number = switch.get("serialNumber", "unknown")
            hostname = switch.get("logicalName", "unknown")
            filename = f"{fabric_dir}/{serial_number}_{hostname}.json"
            with open(filename, "w") as f:
                json.dump(switch, f, indent=4)
                print(f"Switch config for {hostname} (ID: {serial_number}) is saved to {filename}")
    return switches

def delete_switch(fabric, serial_number):
    headers = get_api_key_header()
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/switches/{serial_number}")
    r = requests.delete(url, headers=headers, verify=False)
    return check_status_code(r, operation_name="Delete Switch")

def discover_switch(fabric, payload):
    """Discover switch using provided payload data."""
    load_dotenv()
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/inventory/discover")
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    # Set password from environment
    payload["password"] = os.getenv("SWITCH_PASSWORD") 
    
    r = requests.post(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name="Discover Switch")

def change_discovery_ip(fabric, serial_number, new_ip):
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/inventory/discoveryIP")
    payload = [
        {
            "serialNumber": serial_number,
            "ipAddress": new_ip
        }
    ]
    r = requests.put(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name="Change Discovery IP")

def rediscover_device(fabric, serial_number):
    headers = get_api_key_header()
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/inventory/rediscover/{serial_number}")

    r = requests.post(url, headers=headers, verify=False)
    return check_status_code(r, operation_name="Rediscover Device")

def deploy_switch_config(fabric, serial_number):
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/config-deploy/{serial_number}")
    headers = get_api_key_header()
    r = requests.post(url, headers=headers, verify=False)
    return check_status_code(r, operation_name="Deploy Switch Config")

def set_switch_role(serial_number, role):
    """Set switch role using the switches/roles API endpoint."""
    url = get_url("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/switches/roles")
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    payload = [
        {
            "serialNumber": serial_number,
            "role": role
        }
    ]
    
    r = requests.post(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name="Set Switch Role")
