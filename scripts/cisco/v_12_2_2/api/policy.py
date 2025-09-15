import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3
urllib3.disable_warnings(InsecureRequestWarning)
from .utils import *
import json
import random
import time
import os

def save_policy_config(data, policy_dir="policies", switch_name=None):
    # Save the policy config to a file with new naming format: {policy_id}_{switchname}_{serialnumber}.json
    serial_number = data.get("serialNumber", "unknown")
    policy_id = data.get("policyId", "unknown")
    
    # Use new filename format if switch_name is provided
    if switch_name:
        filename = f"{policy_dir}/{policy_id}_{switch_name}_{serial_number}.json"
    else:
        print("Switch name not provided, exiting...")
        return  # Stop processing if switch_name is not provided

    if not os.path.exists(policy_dir):
        os.makedirs(policy_dir)
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
        # print(f"{policy_id} is saved to {filename}")

    # Note: Freeform config is not saved separately as it exists in network_configs

def create_policy(payload):
    """Create a new policy using the provided payload."""
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    url = get_url("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies")
    r = requests.post(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name="Create Policy")

def find_existing_policies_for_switch(switch_name, serial_number, policy_dir="policies"):
    """Find existing policy files for a given switch by parsing filenames."""
    existing_policies = []
    
    if not os.path.exists(policy_dir):
        return existing_policies
    
    # Look for files matching the pattern: {policy_id}_{switchname}_{serialnumber}.json
    for filename in os.listdir(policy_dir):
        if filename.endswith('.json'):
            # Parse filename: POLICY-123456_SwitchName_SerialNumber.json
            parts = filename[:-5].split('_')  # Remove .json extension and split
            if len(parts) >= 3:
                file_switch_name = parts[1] if len(parts) > 1 else ""
                file_serial_number = parts[2] if len(parts) > 2 else ""
                
                if file_switch_name == switch_name and file_serial_number == serial_number:
                    policy_id = parts[0]  # POLICY-123456
                    existing_policies.append({
                        'policy_id': policy_id,
                        'filename': filename,
                        'full_path': os.path.join(policy_dir, filename)
                    })
    
    return existing_policies

def delete_existing_policies_for_switch(switch_name, serial_number, policy_dir="policies"):
    """Delete existing policies for a switch both from NDFC and local files."""
    existing_policies = find_existing_policies_for_switch(switch_name, serial_number, policy_dir)
    
    if not existing_policies:
        print(f"No existing policies found for switch {switch_name} ({serial_number})")
        return True
    
    # print(f"Found {len(existing_policies)} existing policies for switch {switch_name}")
    
    for policy_info in existing_policies:
        policy_id = policy_info['policy_id']
        filename = policy_info['filename']
        full_path = policy_info['full_path']
        
        try:
            # Extract numeric ID from POLICY-123456
            numeric_id = policy_id.split('-')[1]
            
            print(f"[Switch] Deleting policy {policy_id} from NDFC...")
            delete_policy(numeric_id)
            
            # Delete local file
            if os.path.exists(full_path):
                os.remove(full_path)
                print(f"[Switch] Deleted local file: {filename}")
                
        except Exception as e:
            print(f"[Switch] Error deleting policy {policy_id}: {e}")
            return False
    
    return True

def create_policy_with_random_id(switch_name, serial_number, fabric_name, freeform_config, max_attempts=10):
    """Create a policy with a randomly generated ID, trying until successful."""
    
    for attempt in range(max_attempts):
        # Generate random policy number between 100000 and 999999
        policy_id = random.randint(100000, 999999)
        policy_id_str = f"POLICY-{policy_id}"
        
        print(f"[Switch] Attempt {attempt + 1}: Trying policy ID {policy_id_str}")
        
        # Create the payload based on the template
        payload = {
            "id": policy_id,
            "policyId": policy_id_str,
            "description": f"{switch_name} freeform policy",
            "serialNumber": serial_number,
            "entityType": "SWITCH",
            "entityName": "SWITCH",
            "templateName": "switch_freeform",
            "templateContentType": "PYTHON",
            "nvPairs": {
                "SECENTITY": "",
                "PRIORITY": "500",
                "POLICY_DESC": f"{switch_name} freeform policy",
                "CONF": freeform_config,
                "SECENTTYPE": "",
                "FABRIC_NAME": fabric_name,
                "POLICY_ID": policy_id_str
            },
            "generatedConfig": "",
            "autoGenerated": False,
            "deleted": False,
            "source": "",
            "priority": 500,
            "status": "NA"
        }
        
        if create_policy(payload):
            print(f"[Switch] Successfully created policy {policy_id_str}")
            return policy_id_str
            
        # Wait a bit before trying again
        time.sleep(0.5)
    
    print(f"[Switch] Failed to create policy after {max_attempts} attempts")
    return None

def get_policies_by_serial_number(serial_number):
    """Get all policies for a switch by serial number."""
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies/switches/{serial_number}")
    headers = get_api_key_header()
    r = requests.get(url, headers=headers, verify=False)
    
    if not check_status_code(r, operation_name="Get Policies by Serial Number"):
        return None
    
    return r.json()

def update_policy(policy_id, payload):
    """Update an existing policy using the provided payload."""
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies/{policy_id}")
    r = requests.put(url, headers=headers, json=payload, verify=False)

    return check_status_code(r, operation_name="Update Policy")

def get_policy_by_id(id, policy_dir="policies", switch_name=None):
    """Get policy by ID and save with new filename format if switch_name provided."""
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies/{id}")
    headers = get_api_key_header()
    r = requests.get(url, headers=headers, verify=False)
    check_status_code(r, operation_name="Get Policy by ID")
    if not os.path.exists(policy_dir):
        os.makedirs(policy_dir)

    save_policy_config(r.json(), policy_dir, switch_name)

def delete_policy(id):
    """Delete a policy by numeric ID."""
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies/POLICY-{id}")
    headers = get_api_key_header()
    r = requests.delete(url, headers=headers, verify=False)
    return check_status_code(r, operation_name="Delete Policy")
