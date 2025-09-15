"""
API Utilities - Low-level HTTP communication utilities for Cisco NDFC API
Contains authentication, URL building, and HTTP response handling.
Used exclusively by API modules for network communication.
"""
from dotenv import load_dotenv
import os
import sys
import requests
import yaml
from typing import Dict, Optional, Any

def _load_fabric_builder_config() -> str:
    """
    Load NDFC IP from fabric_builder.yaml configuration file.
    
    Returns:
        NDFC management IP URL with https:// prefix
    """
    try:
        # Get the path to fabric_builder.yaml relative to this file
        current_dir = os.path.dirname(__file__)
        config_path = os.path.join(current_dir, '..', '..', '..', '..', 'network_configs', 'fabric_builder.yaml')
        config_path = os.path.normpath(config_path)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        ndfc_ip = config['Cisco']['NDFC']['ip']
        return f'https://{ndfc_ip}'
        
    except (FileNotFoundError, KeyError, yaml.YAMLError) as e:
        print(f"Warning: Could not load fabric_builder.yaml config: {e}")
        print("Falling back to default IP: 10.192.195.20")
        return 'https://10.192.195.20'
    except Exception as e:
        print(f"Unexpected error loading fabric config: {e}")
        print("Falling back to default IP: 10.192.195.20")
        return 'https://10.192.195.20'

# NDFC management IP - loaded from fabric_builder.yaml
DEFAULT_MANAGEMENT_IP = _load_fabric_builder_config()

def get_management_ip() -> str:
    """
    Get NDFC management IP from environment variable or use default.
    
    Returns:
        Complete NDFC management URL
    """
    load_dotenv()
    return os.getenv('NDFC_MANAGEMENT_IP', DEFAULT_MANAGEMENT_IP)

def get_url(api_endpoint: str) -> str:
    """
    Constructs the full URL for NDFC API endpoints.
    
    Args:
        api_endpoint: The API endpoint path
        
    Returns:
        Complete URL for the NDFC API endpoint
    """
    return f"{get_management_ip()}{api_endpoint}"

def get_api_key_header() -> Dict[str, str]:
    """
    Get the API key from environment variable and format it as a header.
    
    Returns:
        Dictionary with authorization header for API requests
        
    Raises:
        SystemExit: If NDFC_API_KEY environment variable is not set
    """
    load_dotenv()
    api_key = os.getenv("NDFC_API_KEY")
    
    if not api_key:
        print("Error: NDFC_API_KEY environment variable not set.")
        print("Please set your API key in your .env file or environment variables.")
        sys.exit(1)

    return {
        'X-Nd-Apikey': api_key,
        'X-Nd-Username': 'admin',
        'Content-Type': 'application/json'
    }

def check_status_code(response: requests.Response, operation_name: str = "API operation") -> bool:
    """
    Check HTTP response status and handle errors.
    
    Args:
        response: HTTP response object from requests
        operation_name: Descriptive name of the operation for error messages
        
    Returns:
        True if successful (status 200), False otherwise
    """
    RED = '\033[91m'
    END = '\033[0m'
    if response.status_code == 200:
        # print(f"[+] Success: {operation_name}")
        return True
    else:
        print(f"{RED}[-] Fail: {operation_name}{END}")
        print(f"{RED}[*] Status Code: {response.status_code}{END}")
        print(f"{RED}[*] Message: {response.text}{END}")
        return False

def get_api_timeout() -> int:
    """
    Get API timeout value from environment variable or return default.
    
    Returns:
        Timeout value in seconds (default: 30)
    """
    load_dotenv()
    try:
        return int(os.getenv('NDFC_API_TIMEOUT', '30'))
    except ValueError:
        return 30

def validate_response_format(response: requests.Response, expected_format: str = 'json') -> bool:
    """
    Validate that the response is in the expected format.
    
    Args:
        response: HTTP response object
        expected_format: Expected response format ('json' or 'text')
        
    Returns:
        True if response format is valid
    """
    if expected_format == 'json':
        try:
            response.json()
            return True
        except Exception:
            return False
    elif expected_format == 'text':
        return isinstance(response.text, str)
    else:
        return False

def prepare_api_payload(data: Dict[str, Any]) -> str:
    """
    Prepare data for API request by converting to JSON string.
    
    Args:
        data: Dictionary to convert to JSON
        
    Returns:
        JSON string representation of the data
        
    Raises:
        ValueError: If data cannot be serialized to JSON
    """
    try:
        import json
        return json.dumps(data)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Failed to serialize data to JSON: {e}")

def handle_api_error(response: requests.Response, context: str = "API operation") -> None:
    """
    Enhanced error handling for API responses with detailed context.
    
    Args:
        response: HTTP response object
        context: Additional context about the failed operation
    """
    print(f"❌ {context} failed")
    print(f"Status Code: {response.status_code}")
    print(f"URL: {response.url}")
    
    # Try to extract detailed error information
    try:
        error_data = response.json()
        if isinstance(error_data, dict):
            error_message = error_data.get('message', error_data.get('error', 'Unknown error'))
            print(f"Error Message: {error_message}")
            
            # Print additional error details if available
            if 'details' in error_data:
                print(f"Error Details: {error_data['details']}")
        else:
            print(f"Response: {error_data}")
    except Exception:
        print(f"Response: {response.text}")

def verify_connectivity() -> bool:
    """
    Verify basic connectivity to NDFC management interface.
    
    Returns:
        True if NDFC is reachable, False otherwise
    """
    try:
        # Simple connectivity test to the management IP
        response = requests.get(
            get_management_ip(),
            timeout=get_api_timeout(),
            verify=False  # Disable SSL verification for self-signed certificates
        )
        return response.status_code in [200, 401, 403]  # Any response indicates connectivity
    except requests.exceptions.RequestException:
        return False

def get_base_headers() -> Dict[str, str]:
    """
    Get base headers required for all API requests.
    
    Returns:
        Dictionary with standard headers for NDFC API
    """
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'NDFC-Fabric-Builder/1.0'
    }
 
def parse_template_config(template_config_file: str) -> str:
    """
    Parse a JSON template configuration file and return its JSON string.
    Used by API modules for embedding template config in payloads.
    """
    try:
        import json
        with open(template_config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return json.dumps(data)
    except FileNotFoundError:
        print(f"Warning: Template config file not found at {template_config_file}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON config {template_config_file}: {e}")
    except Exception as e:
        print(f"Error reading template config {template_config_file}: {e}")
    return ""