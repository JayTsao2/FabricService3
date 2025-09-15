## [Fabric](fabric.py)
- `get_fabrics(save_files: bool = False)` - 獲取所有 fabric 列表，可選擇儲存到 fabrics.json
- `get_fabric(fabric_name: str, save_files: bool = False)` - 獲取指定 fabric 配置，可選擇儲存到 {fabric_name}.json
- `create_fabric(fabric_name: str, template_name: str, payload_data: Dict[str, Any])` - 建立 fabric
  - 支援模板類型：Easy_Fabric, External_Fabric, MSD_Fabric
  - 自動清理無效欄位 (USE_LINK_LOCAL, ISIS_OVERLOAD_ENABLE, ISIS_P2P_ENABLE, PNP_ENABLE_INTERNAL, DOMAIN_NAME_INTERNAL)
  - 使用完整 nvPairs payload 資料
- `update_fabric(fabric_name: str, template_name: str, payload_data: Dict[str, Any])` - 更新 fabric
  - 同樣支援模板類型和自動清理無效欄位
  - 使用完整 nvPairs payload 資料
- `delete_fabric(fabric_name: str)` - 刪除 fabric
- `recalculate_config(fabric_name: str)` - 重新計算 fabric 配置
- `deploy_fabric_config(fabric_name: str)` - 部署 fabric 配置
- `get_pending_config(fabric_name: str, save_files: bool = False)` - 獲取待部署配置
  - 可選擇儲存格式化輸出至 pending.txt
  - 按交換器分組顯示待部署命令
- `add_MSD(parent_fabric_name: str, child_fabric_name: str)` - 將子 fabric 添加到 Multi-Site Domain
- `remove_MSD(parent_fabric_name: str, child_fabric_name: str)` - 從 Multi-Site Domain 移除子 fabric

### 無效欄位自動清理
以下欄位會在 create 和 update 操作中自動移除：
- USE_LINK_LOCAL
- ISIS_OVERLOAD_ENABLE
- ISIS_P2P_ENABLE
- PNP_ENABLE_INTERNAL
- DOMAIN_NAME_INTERNAL

## [Switch](api/switch.py)
- `get_switches(fabric, save_files: bool = False)` - 獲取指定 fabric 中的所有交換器，可選擇儲存到檔案
- `delete_switch(fabric, serial_number)` - 根據序號刪除交換器
- `discover_switch(fabric, payload)` - 使用 payload 發現交換器
- `change_discovery_ip(fabric, serial_number, new_ip)` - 變更交換器發現 IP
- `rediscover_device(fabric, serial_number)` - 重新發現設備
- `deploy_switch_config(fabric, serial_number)` - 部署交換器配置
- `set_switch_role(serial_number, role)` - 設定交換器角色

## [VPC](api/vpc.py)
- `create_vpc_pair(peer_one_id, peer_two_id, use_virtual_peerlink=False)` - 建立 VPC 配對
- `delete_vpc_pair(serial_number)` - 刪除 VPC 配對
- `delete_vpc_policy(vpc_name, serial_numbers)` - 刪除 VPC 政策
- `set_vpc_policy(policy_data)` - 設定 VPC 政策

## [Interface](api/interface.py)
- `update_interface(fabric_name: str, policy: str, interfaces_payload: List[Dict[str, Any]])` - 使用直接傳遞的 payload 資料更新介面配置
- `get_interfaces(serial_number: str = None, if_name: str = None, template_name: str = None, interface_dir: str = "interfaces", save_by_policy: bool = True)` - 讀取介面配置，支援按政策分組儲存
- `update_admin_status(payload: List[Dict[str, Any]])` - 更新介面管理狀態 (enable/disable)，用於沒有政策的介面

## [Network](api/network.py)
- `get_networks(fabric, network_dir="networks", network_template_config_dir="networks/network_templates", network_filter="", range=0)` - 獲取網路列表
- `get_network(fabric, network_name, network_dir="networks", network_template_config_dir="networks/network_templates")` - 獲取指定網路配置
- `create_network(fabric_name: str, network_payload: Dict[str, Any], template_payload: Dict[str, Any])` - 建立網路
- `update_network(fabric_name: str, network_payload: Dict[str, Any], template_payload: Dict[str, Any])` - 更新網路
- `delete_network(fabric_name: str, network_name: str)` - 刪除網路
- `attach_network(payload: List[Dict[str, Any]])` - 將網路附加到設備
- `detach_network(fabric_name: str, payload: List[Dict[str, Any]])` - 從設備分離網路
- `get_network_attachment(fabric, network_dir="networks", networkname="")` - 獲取網路附加狀態
- `preview_networks(fabric, network_names)` - 預覽網路配置 (生成待部署配置)
- `deploy_networks(fabric, network_names)` - 部署網路配置

## [VRF](api/vrf.py)
- `get_VRFs(fabric, vrf_dir="vrfs", vrf_template_config_dir="vrf_template_config_dirs", vrf_filter="", range=0)` - 獲取 VRF 列表
- `create_vrf(fabric_name: str, vrf_payload: Dict[str, Any], template_payload: Dict[str, Any])` - 建立 VRF
- `update_vrf(fabric_name: str, vrf_name: str, vrf_payload: Dict[str, Any], template_payload: Dict[str, Any])` - 更新 VRF
- `delete_vrf(fabric_name: str, vrf_name: str)` - 刪除 VRF
- `update_vrf_attachment(fabric_name: str, attachment_payload: Dict[str, Any])` - 更新 VRF 附加配置
- `attach_vrf_to_switches(fabric_name: str, vrf_name: str, attachment_payload: List[Dict[str, Any]])` - 將 VRF 附加到交換器
- `detach_vrf_from_switches(fabric_name: str, vrf_name: str, attachment_payload: List[Dict[str, Any]])` - 從交換器分離 VRF

## [Policy](api/policy.py)
- `save_policy_config(data, policy_dir="policies", switch_name=None)` - 儲存政策配置
- `create_policy(payload)` - 建立政策
- `find_existing_policies_for_switch(switch_name, serial_number, policy_dir="policies")` - 尋找交換器的現有政策
- `delete_existing_policies_for_switch(switch_name, serial_number, policy_dir="policies")` - 刪除交換器的現有政策
- `create_policy_with_random_id(switch_name, serial_number, fabric_name, freeform_config, max_attempts=10)` - 建立具有隨機 ID 的政策
- `get_policies_by_serial_number(serial_number)` - 根據序號獲取政策
- `update_policy(policy_id, payload)` - 更新政策
- `get_policy_by_id(id, policy_dir="policies", switch_name=None)` - 根據 ID 獲取政策
- `delete_policy(id)` - 刪除政策

## [Key/Authentication](api/key.py)
- `login()` - 登入 NDFC 並獲取認證 token
- `add_api_key(token)` - 添加 API key
- `get_api_key(token)` - 獲取 API key
- `generate_api_key()` - 生成新的 API key
- Note: 記得要將環境變數放在 .env 裡面

## [Utils](api/utils.py)
- 提供 HTTP 通訊工具函數 (get_url, get_api_key_header, check_status_code 等)
- 環境變數管理和 NDFC 管理 IP 配置