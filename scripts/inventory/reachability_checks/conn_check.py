import os
import constants
import yaml
import sys
import re
from pathlib import Path
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

def parse_interface_status_output(output):
    """
    解析show interface status輸出，返回interface狀態映射
    """
    interface_status = {}
    
    # 分割輸出為行並找到interface條目
    lines = output.split('\n')
    
    for line in lines:
        # 匹配以Eth或mgmt開頭的行（interface條目）
        if re.match(r'^(Eth\d+/\d+|mgmt\d+)', line.strip()):
            parts = line.split()
            if len(parts) >= 3:
                interface = parts[0]
                status = parts[2] if len(parts) > 2 else 'unknown'
                interface_status[interface] = status
    
    return interface_status

def get_interfaces_without_policy(yaml_file_path):
    """
    從YAML文件中提取沒有Policy的interface
    """
    try:
        with open(yaml_file_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        
        interfaces_without_policy = []
        
        # 檢查是否有Interface配置
        if 'Interface' in config and isinstance(config['Interface'], list):
            for interface in config['Interface']:
                if isinstance(interface, dict) and 'Policy' not in interface:
                    interfaces_without_policy.append({
                        'name': interface.get('Name', ''),
                        'description': interface.get('Interface Description', '')
                    })
        
        return interfaces_without_policy
    except Exception as e:
        print(f"Error parsing interfaces from {yaml_file_path}: {e}")
        return []

def check_device_interface_connectivity(device_info, username, password):
    """
    連接到設備並檢查沒有Policy的interface連接狀態
    """
    device = {
        'device_type': 'cisco_nxos',
        'host': device_info['ip'],
        'username': username,
        'password': password,
        'timeout': 30,
        'session_timeout': 30,
    }
    
    results = {
        'connected': False,
        'hostname': device_info.get('hostname', 'Unknown'),
        'interface_results': [],
        'error_message': ''
    }
    
    try:
        # 連接到設備
        connection = ConnectHandler(**device)
        results['connected'] = True
        
        # 獲取沒有Policy的interface列表
        if 'filepath' in device_info:
            interfaces_without_policy = get_interfaces_without_policy(device_info['filepath'])
            
            if interfaces_without_policy:
                # 執行show interface status命令
                status_output = connection.send_command('show interface status')
                interface_status_map = parse_interface_status_output(status_output)
                
                # 檢查每個沒有policy的interface
                for interface in interfaces_without_policy:
                    interface_name = interface['name']
                    description = interface['description']
                    
                    # 轉換interface名稱格式 (Ethernet1/1 -> Eth1/1)
                    eth_name = interface_name.replace('Ethernet', 'Eth')
                    
                    status = interface_status_map.get(eth_name, 'not found')
                    
                    results['interface_results'].append({
                        'name': interface_name,
                        'description': description,
                        'status': status,
                        'connected': status == 'connected'
                    })
        
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

def check():
    """
    主要執行函數
    """
    # 設定參數
    username = "admin"
    password = "C1sco12345!"
    yaml_directory = constants.NETWORK_CONFIGS_PATH
    
    print("Starting interface connectivity check...")
    print("=" * 60)
    print(f"Searching for YAML files in: {yaml_directory}")
    print()
    
    # 提取設備清單
    device_list = extract_devices_from_yaml(yaml_directory)
    
    if not device_list:
        print("No devices with IP addresses found in YAML files!")
        return False
    
    print(f"Found {len(device_list)} devices to check:")
    print()
    
    all_interfaces_connected = True  # 追蹤是否所有interface都連接
    
    # 逐一檢查每個設備
    for device in device_list:
        print(f"Checking {device['file']} ({device['hostname']})...")
        
        results = check_device_interface_connectivity(device, username, password)
        
        if results['connected']:
            if results['interface_results']:
                print("Interface Status Check (interfaces without policy):")
                for interface_result in results['interface_results']:
                    name = interface_result['name']
                    description = interface_result['description']
                    status = interface_result['status']
                    
                    if description:
                        status_line = f"  {name} to {description}: {status}"
                    else:
                        status_line = f"  {name}: {status}"
                    
                    print(status_line)
                    
                    # 如果interface不是connected，標記為檢查失敗
                    if not interface_result['connected']:
                        all_interfaces_connected = False
            else:
                print("  No interfaces without policy found for status check")
        else:
            print(f"  Connection failed: {results['error_message']}")
            all_interfaces_connected = False
        
        print()
    
    print("Interface connectivity check completed.")
    print("=" * 60)
    
    if all_interfaces_connected:
        print("✓ All interfaces without policy are connected")
    else:
        print("✗ Some interfaces are not connected or connection issues occurred")

    print(all_interfaces_connected)
    return all_interfaces_connected

if __name__ == "__main__":
    result = check()
    sys.exit(0 if result else 1)
