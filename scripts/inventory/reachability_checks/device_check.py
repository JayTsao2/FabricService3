import os
import constants
import yaml
import sys
from pathlib import Path
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

def parse_inventory_output(output):
    """
    解析show inventory輸出，提取Platform (PID)和Serial Number (SN)
    """
    lines = output.split('\n')
    chassis_found = False
    
    for line in lines:
        line = line.strip()
        
        # 找到"Chassis"行
        if 'NAME: "Chassis"' in line:
            chassis_found = True
            continue
        
        # 在找到Chassis後，尋找包含PID和SN的行
        if chassis_found and 'PID:' in line and 'SN:' in line:
            # 解析PID和SN
            parts = line.split(',')
            platform = None
            serial_number = None
            
            for part in parts:
                part = part.strip()
                if part.startswith('PID:'):
                    platform = part.split('PID:')[1].strip()
                elif part.startswith('SN:'):
                    serial_number = part.split('SN:')[1].strip()
            
            return platform, serial_number
    
    return None, None

def parse_version_output(output):
    """
    解析show version輸出，提取NXOS版本
    """
    lines = output.split('\n')
    
    for line in lines:
        line = line.strip()
        if 'NXOS: version' in line:
            # 提取version後的字串
            version = line.split('NXOS: version')[1].strip()
            return version
    
    return None

def connect_and_check_device(device_info, username, password):
    """
    連接到設備並檢查hostname、Platform、Serial Number和Version
    """
    device = {
        'device_type': 'cisco_nxos',  # 根據需要調整設備類型
        'host': device_info['ip'],
        'username': username,
        'password': password,
        'timeout': 30,
        'session_timeout': 30,
    }
    
    results = {
        'connected': False,
        'hostname_correct': False,
        'platform_correct': False,
        'serial_correct': False,
        'version_correct': False,
        'actual_hostname': '',
        'actual_platform': '',
        'actual_serial': '',
        'actual_version': '',
        'error_message': ''
    }
    
    try:
        # 連接到設備
        connection = ConnectHandler(**device)
        results['connected'] = True
        
        # 執行show hostname命令
        hostname_output = connection.send_command('show hostname')
        actual_hostname = hostname_output.strip()
        if '.' in actual_hostname:
            actual_hostname = actual_hostname.split('.')[0]
        results['actual_hostname'] = actual_hostname
        
        # 比對hostname
        expected_hostname = device_info['hostname']
        results['hostname_correct'] = actual_hostname.lower() == expected_hostname.lower()
        
        # 執行show inventory命令
        inventory_output = connection.send_command('show inventory')
        actual_platform, actual_serial = parse_inventory_output(inventory_output)
        
        results['actual_platform'] = actual_platform or 'Not Found'
        results['actual_serial'] = actual_serial or 'Not Found'
        
        # 比對Platform和Serial Number
        if 'platform' in device_info and actual_platform:
            results['platform_correct'] = actual_platform.strip() == device_info['platform'].strip()
        
        if 'serial_number' in device_info and actual_serial:
            results['serial_correct'] = actual_serial.strip() == device_info['serial_number'].strip()
        
        # 執行show version命令
        version_output = connection.send_command('show version')
        actual_version = parse_version_output(version_output)
        
        results['actual_version'] = actual_version or 'Not Found'
        
        # 比對Version
        if 'version' in device_info and actual_version:
            results['version_correct'] = actual_version.strip() == device_info['version'].strip()
        
        connection.disconnect()
        
    except NetmikoTimeoutException:
        results['error_message'] = "Connection Timeout"
    except NetmikoAuthenticationException:
        results['error_message'] = "Authentication Failed"
    except Exception as e:
        results['error_message'] = f"Error: {str(e)}"
    
    return results

def extract_devices_from_yaml(yaml_dir):
    """
    遍歷指定目錄及其所有子目錄中的YAML檔案，提取有IP address的設備資訊
    """
    device_list = []
    yaml_path = Path(yaml_dir)
    seen_devices = set()  # 用於去重複
    
    if not yaml_path.exists():
        print(f"Directory {yaml_dir} does not exist!")
        return device_list
    
    # 遞歸搜尋所有子目錄中的YAML檔案
    for yaml_file in yaml_path.rglob("*.yaml"):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
            
            device_info = {'file': yaml_file.name, 'filepath': str(yaml_file)}
            
            # 搜尋設備資訊
            def find_device_info(obj):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key.lower() == 'ip address' or key.lower() == 'ip_address':
                            device_info['ip'] = value
                        elif key.lower() == 'hostname':
                            device_info['hostname'] = value
                        elif key.lower() == 'platform':
                            device_info['platform'] = value
                        elif key.lower() == 'serial number':
                            device_info['serial_number'] = value
                        elif key.lower() == 'version':
                            device_info['version'] = value
                        elif isinstance(value, (dict, list)):
                            find_device_info(value)
                elif isinstance(obj, list):
                    for item in obj:
                        find_device_info(item)
            
            find_device_info(data)
            
            # 只有當設備有IP address和hostname時才加入清單
            if 'ip' in device_info and 'hostname' in device_info:
                device_key = f"{device_info['hostname']}_{device_info['ip']}"
                if device_key not in seen_devices:
                    seen_devices.add(device_key)
                    device_list.append(device_info)
            
        except Exception as e:
            print(f"Error reading {yaml_file}: {e}")
    
    return device_list

def connect_and_check_hostname(device_info, username, password):
    """
    連接到設備並檢查hostname
    """
    device = {
        'device_type': 'cisco_nxos',  # 根據需要調整設備類型
        'host': device_info['ip'],
        'username': username,
        'password': password,
        'timeout': 30,
        'session_timeout': 30,
    }
    
    try:
        # 連接到設備
        connection = ConnectHandler(**device)
        
        # 執行show hostname命令
        output = connection.send_command('show hostname')
        connection.disconnect()
        
        # 提取hostname（取第一個"."前的字串）
        actual_hostname = output.strip()
        if '.' in actual_hostname:
            actual_hostname = actual_hostname.split('.')[0]
        
        # 比對hostname
        expected_hostname = device_info['hostname']
        is_correct = actual_hostname.lower() == expected_hostname.lower()
        
        return True, actual_hostname, is_correct
        
    except NetmikoTimeoutException:
        return False, "Connection Timeout", False
    except NetmikoAuthenticationException:
        return False, "Authentication Failed", False
    except Exception as e:
        return False, f"Error: {str(e)}", False

def check():
    """
    主要執行函數
    """
    # 設定參數
    username = "admin"
    password = "C1sco12345!"
    # 設定YAML檔案目錄路徑
    yaml_directory = constants.NETWORK_CONFIGS_PATH
    
    print("Starting device inventory check...")
    print("=" * 50)
    print(f"Searching for YAML files in: {yaml_directory}")
    print()
    
    # 提取設備清單
    device_list = extract_devices_from_yaml(yaml_directory)
    
    if not device_list:
        print("No devices with IP addresses found in YAML files!")
        return False
    
    print(f"Found {len(device_list)} devices to check:")
    print()
    
    all_correct = True  # 追蹤是否所有檢查都正確
    
    # 逐一檢查每個設備
    for device in device_list:
        print(f"Checking {device['file']} ...")
        
        results = connect_and_check_device(device, username, password)
        
        if results['connected']:
            # 檢查hostname
            if results['hostname_correct']:
                print(f"hostname : {device['hostname']} ... Correct")
            else:
                print(f"hostname : Expected '{device['hostname']}', Got '{results['actual_hostname']}' ... Incorrect")
                all_correct = False
            
            # 檢查Platform
            if 'platform' in device:
                if results['platform_correct']:
                    print(f"platform : {device['platform']} ... Correct")
                else:
                    print(f"platform : Expected '{device['platform']}', Got '{results['actual_platform']}' ... Incorrect")
                    all_correct = False
            else:
                print(f"platform : Not specified in YAML")
            
            # 檢查Serial Number
            if 'serial_number' in device:
                if results['serial_correct']:
                    print(f"serial number : {device['serial_number']} ... Correct")
                else:
                    print(f"serial number : Expected '{device['serial_number']}', Got '{results['actual_serial']}' ... Incorrect")
                    all_correct = False
            else:
                print(f"serial number : Not specified in YAML")
            
            # 檢查Version
            if 'version' in device:
                if results['version_correct']:
                    print(f"version : {device['version']} ... Correct")
                else:
                    print(f"version : Expected '{device['version']}', Got '{results['actual_version']}' ... Incorrect")
                    all_correct = False
            else:
                print(f"version : Not specified in YAML")
                
        else:
            print(f"Connection failed : {results['error_message']}")
            all_correct = False
        
        print()
    
    print("Device inventory check completed.")
    print (all_correct)
    return all_correct


if __name__ == "__main__":
    result = check()
    print(f"Overall result: {'All checks passed' if result else 'Some checks failed or connection issues'}")
