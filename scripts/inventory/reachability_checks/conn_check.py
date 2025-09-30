import os
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
        # 移除行首空白，檢查是否以 Eth 或 mgmt 開頭
        s = line.lstrip()
        m = re.match(r'^(Eth\d+(?:/\d+){1,2}|mgmt\d+)\b', s, re.IGNORECASE)
        if m:
            interface = m.group(1)
            status = 'unknown'

            # 優先使用 token 掃描法：跳過第一個 interface token，逐個 token 檢查是否為已知狀態字
            tokens = s.split()
            status_keywords = {'connected', 'notconnect', 'not', 'disabled', 'err-disabled', 'err-disabled',
                               'suspended'}
            for t in tokens[1:]:
                tt = t.strip().lower()
                # 直接比對 token（避免匹配到像 connected-to-... 這種描述）
                if tt in status_keywords:
                    # normalize some variants
                    if tt == 'not':
                        status = 'notconnect'
                    else:
                        status = tt
                    break

            if status == 'unknown':
                # 若 token 掃描沒找到，再用原來的關鍵字搜尋或分欄方式備援
                lower = s.lower()
                if re.search(r'\berr-?disabled\b', lower):
                    status = 'err-disabled'
                elif re.search(r'\bdisabled\b', lower):
                    status = 'disabled'
                elif re.search(r'\bnot\s*connect\b|\bnotconnect\b', lower):
                    status = 'notconnect'
                elif re.search(r'\bsuspended\b', lower):
                    status = 'suspended'
                elif re.search(r'\bconnected\b', lower):
                    status = 'connected'
                else:
                    parts = re.split(r'\s{2,}', s)
                    if len(parts) >= 3:
                        status = parts[2].strip().lower()
                    else:
                        parts2 = s.split()
                        if len(parts2) >= 3:
                            status = parts2[2].strip().lower()

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
                    # 讀取 Enable Interface，若不存在預設為 True
                    enable_val = interface.get('Enable Interface', True)
                    # normalize various representations to boolean
                    if isinstance(enable_val, str):
                        enable = enable_val.lower() in ('true', 'yes', '1')
                    else:
                        enable = bool(enable_val)

                    interfaces_without_policy.append({
                        'name': interface.get('Name', ''),
                        'description': interface.get('Interface Description', ''),
                        'enable': enable
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
                    expected_enable = interface.get('enable', True)

                    # Determine whether this interface matches the YAML config:
                    # - If expected_enable is True, actual must be 'connected'
                    # - If expected_enable is False, actual must NOT be 'connected'
                    actual_is_connected = (status == 'connected')
                    matches = (actual_is_connected and expected_enable) or (
                                not actual_is_connected and not expected_enable)

                    results['interface_results'].append({
                        'name': interface_name,
                        'description': description,
                        'status': status,
                        'expected_enable': expected_enable,
                        'matches_config': matches
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

    # 遞歸搜尋 node 資料夾下所有子目錄中的 YAML 檔案 (.yaml, .yml)
    # 注意： 不包含直接位於 node 資料夾根目錄下的 YAML 檔案，只搜尋 node/*/** 的檔案
    for yaml_file in yaml_path.rglob("*"):
        if not yaml_file.is_file():
            continue
        if yaml_file.suffix.lower() not in ('.yaml', '.yml'):
            continue
        # Skip files that are directly under the `node` folder (we only want nested folders)
        try:
            rel_parts = yaml_file.relative_to(yaml_path).parts
        except Exception:
            # If relative_to fails for any reason, skip this file
            continue
        if len(rel_parts) < 2:
            # This means the file is directly under yaml_path (node/) and should be skipped
            # Helpful debug print (kept minimal)
            # print(f"Skipping top-level YAML file: {yaml_file}")
            continue
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
    # 預設使用相對於此檔案所在 repository 根目錄的 network_configs/node
    # conn_check.py 位於: scripts/inventory/reachability_checks/
    # 往上回溯到 repo 根（假設 repo 結構如目前工作區），然後接 network_configs/node
    repo_root = Path(__file__).resolve().parents[3]
    yaml_directory = repo_root / "network_configs" / "node"

    # 如果不存在，再嘗試原先的絕對備援路徑（維持向後相容）
    # 暫時取消絕對路徑做法
    # if not yaml_directory.exists():
    #     yaml_directory = Path("c:/Users/TNDO-ADMIN/Desktop/FabricService/network_configs/node")

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

    interconnects_config_match = True  # 追蹤 switch interface 與 YAML config 是否一致

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

                    expected = interface_result.get('expected_enable', True)
                    matches = interface_result.get('matches_config', False)

                    if description:
                        status_line = f"  {name} to {description}: {status} (expected_enable={expected}) -> match={matches}"
                    else:
                        status_line = f"  {name}: {status} (expected_enable={expected}) -> match={matches}"

                    print(status_line)

                    # 如果與 YAML 設定不一致，標記為檢查失敗
                    if not matches:
                        interconnects_config_match = False
            else:
                print("  No interfaces without policy found for status check")
        else:
            print(f"  Connection failed: {results['error_message']}")
            interconnects_config_match = False

        print()

    print("Interface connectivity check completed.")
    print("=" * 60)

    if interconnects_config_match:
        print("✓ Interconnects match the YAML configuration")
    else:
        print("✗ Interconnects do NOT match the YAML configuration or connection issues occurred")

    print(interconnects_config_match)
    return interconnects_config_match


if __name__ == "__main__":
    result = check()
    sys.exit(0 if result else 1)
