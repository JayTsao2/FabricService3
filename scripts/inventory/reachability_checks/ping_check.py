import os
import yaml
import subprocess
import sys
import constants
from pathlib import Path


def extract_ip_addresses_from_yaml(yaml_dir):
    """
    遍歷指定目錄及其所有子目錄中的YAML檔案，提取hostname和IP address
    """
    ip_list = []
    yaml_path = Path(yaml_dir)
    seen_ips = set()  # 用於去重複
    
    if not yaml_path.exists():
        print(f"Directory {yaml_dir} does not exist!")
        return ip_list
    
    # 遞歸搜尋所有子目錄中的YAML檔案
    for yaml_file in yaml_path.rglob("*.yaml"):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                
            # 遞歸搜尋YAML中的IP address
            def find_ip_addresses(obj, hostname_key=None):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key.lower() == 'ip address' or key.lower() == 'ip_address':
                            # 尋找對應的hostname
                            hostname = hostname_key
                            if not hostname:
                                # 嘗試在同一層級找hostname
                                for k, v in obj.items():
                                    if 'hostname' in k.lower() or 'name' in k.lower():
                                        hostname = v
                                        break
                            if not hostname:
                                hostname = yaml_file.stem  # 使用檔名作為hostname
                            
                            # 檢查是否重複
                            ip_key = f"{hostname}_{value}"
                            if ip_key not in seen_ips:
                                seen_ips.add(ip_key)
                                ip_list.append({'hostname': hostname, 'ip': value, 'file': str(yaml_file)})
                        elif isinstance(value, (dict, list)):
                            find_ip_addresses(value, key if isinstance(value, dict) else hostname_key)
                elif isinstance(obj, list):
                    for item in obj:
                        find_ip_addresses(item, hostname_key)
            
            find_ip_addresses(data)
            
        except Exception as e:
            print(f"Error reading {yaml_file}: {e}")
    
    return ip_list

def ping_host(hostname, ip_address, max_unreachable=3):
    """
    Ping指定的主機，如果destination unreachable超過3次就算失敗
    """
    unreachable_count = 0
    
    try:
        # 使用ping命令，Windows系統
        result = subprocess.run(
            ['ping', '-n', '1', ip_address], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        # 檢查ping結果
        if result.returncode == 0:
            # 即使returncode為0，也要檢查是否有unreachable訊息
            if "destination host unreachable" in result.stdout.lower():
                unreachable_count += 1
            else:
                return True, "Successful"
        
        # 檢查是否為destination unreachable
        if "destination host unreachable" in result.stdout.lower() or \
           "destination unreachable" in result.stdout.lower():
            unreachable_count += 1
        
        # 再試幾次以確認unreachable狀態
        for _ in range(max_unreachable - 1):
            result = subprocess.run(
                ['ping', '-n', '1', ip_address], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0 and "destination host unreachable" not in result.stdout.lower():
                return True, "Successful"
            
            if "destination host unreachable" in result.stdout.lower() or \
               "destination unreachable" in result.stdout.lower():
                unreachable_count += 1
        
        if unreachable_count >= max_unreachable:
            return False, "Failed (Destination Unreachable)"
        else:
            return False, "Failed (Timeout/Other)"
                
    except subprocess.TimeoutExpired:
        return False, "Failed (Timeout)"
    except Exception as e:
        return False, f"Failed (Error: {e})"

def check():
    """
    主要執行函數
    """
    # 設定YAML檔案目錄路徑
    yaml_directory = constants.NETWORK_CONFIGS_PATH
    
    # 如果路徑不存在，嘗試絕對路徑
    print("Starting ping check...")
    print("=" * 50)
    print(f"Searching for YAML files in: {yaml_directory}")
    print()
    
    # 提取IP地址清單
    ip_list = extract_ip_addresses_from_yaml(yaml_directory)
    
    if not ip_list:
        print("No IP addresses found in YAML files!")
        return False
    
    print(f"Found {len(ip_list)} IP addresses to ping:")
    print()
    
    all_successful = True  # 追蹤是否所有ping都成功
    
    # 逐一ping每個IP
    for item in ip_list:
        hostname = item['hostname']
        ip = item['ip']
        
        success, status = ping_host(hostname, ip)
        
        if success:
            print(f"PING : {hostname} ({ip}) : Successful")
        else:
            print(f"PING : {hostname} ({ip}) : {status}")
            all_successful = False  # 有失敗的ping
    
    print()
    print("Ping check completed.")
    
    print(all_successful)
    return all_successful

if __name__ == "__main__":
    result = check()
    print(f"Overall result: {'All pings successful' if result else 'Some pings failed'}")
