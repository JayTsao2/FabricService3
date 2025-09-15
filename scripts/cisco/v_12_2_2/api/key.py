import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3
urllib3.disable_warnings(InsecureRequestWarning)

from utils import *

from dotenv import load_dotenv

def login():
    load_dotenv()
    USERNAME = os.getenv("LOGIN_USERNAME")
    PASSWORD = os.getenv("LOGIN_PASSWORD")
    url = get_url("/login")

    payload = {
        "userName" : USERNAME,
        "userPasswd": PASSWORD,
        "domain": "DefaultAuth"
    }

    r = requests.post(url=url, json=payload, verify=False)

    check_status_code(r, "Login to NDFC")
    json_data = r.json()
    jwttoken = json_data.get("jwttoken")

    return jwttoken

def add_api_key(token):
    headers = {
        'Cookie': f'AuthCookie={token}'
    }

    payload = {}
    url = get_url("/api/config/addapikey")
    r = requests.post(url, headers=headers, json=payload, verify=False)

    check_status_code(r, "Add API Key")
    print(r.json())

def get_api_key(token):
    url = get_url("/api/config/dn/userapikey/local-admin?showPassword=yes")
    headers = {
        'Cookie': f'AuthCookie={token}'
    }
    r = requests.get(url, headers=headers, verify=False)

    check_status_code(r, "Get API Key")

    response_json = r.json()
    api_keys = response_json.get("apiKeys", [])
    if api_keys:
        return api_keys[0].get("key", "")
    else:
        print("No api keys")

def generate_api_key():
    token = login()
    # add_api_key(token)
    return get_api_key(token)

if __name__ == "__main__":
    print(f"Generated API key: {generate_api_key()}")
