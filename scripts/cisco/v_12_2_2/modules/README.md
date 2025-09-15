
## [FabricManager](fabric/README.md)
- `create_fabric(fabric_name: str)` - 建立指定的 fabric，自動識別類型並載入 YAML 配置
  - 支援 VXLAN EVPN、Multi-Site Domain、Inter-Site Network 三種 fabric 類型
  - 自動合併預設配置、套用欄位映射、處理 freeform 配置
  - 支援 AAA、Leaf、Spine、Intra-fabric Links、Banner 等 freeform 配置
  - 自動處理 iBGP Peer-Template 配置並替換 BGP ASN
- `update_fabric(fabric_name: str)` - 更新指定的 fabric，使用相同的 YAML 驅動流程
- `delete_fabric(fabric_name: str)` - 刪除指定的 fabric
- `recalculate_config(fabric_name: str)` - 重新計算 fabric 配置
- `get_pending_config(fabric_name: str)` - 獲取待部署配置
- `deploy_fabric(fabric_name: str)` - 部署 fabric 配置
- `add_to_msd(parent_fabric: str, child_fabric: str)` - 將子 fabric 添加到 Multi-Site Domain
- `remove_from_msd(parent_fabric: str, child_fabric: str, force: bool = False)` - 從 Multi-Site Domain 移除子 fabric


## [VRFManager](vrf/README.md)
- `sync(fabric_name: str)` - 完全同步 VRF（刪除多餘、更新現有、創建缺失的 VRF）
- `create_vrf(fabric_name: str, vrf_name: str)` - 在指定 fabric 建立 VRF（先檢查是否已存在）
- `update_vrf(fabric_name: str, vrf_name: str)` - 更新指定 VRF
- `delete_vrf(fabric_name: str, vrf_name: str)` - 刪除指定 VRF（自動分離後刪除）
- `sync_attachments(fabric_name: str, role: str, switch_name: str)` - 同步 VRF 附加到指定交換器
- `attach_vrf(fabric_name: str, role: str, switch_name: str, vrf_name: str)` - 將特定 VRF 附加到交換器
- `attach_vrfs(fabric_name: str, role: str, switch_name: str)` - 將所有相關 VRF 附加到交換器（基於介面配置）
- `detach_vrf(fabric_name: str, role: str, switch_name: str, vrf_name: str)` - 從交換器分離特定 VRF
- `detach_vrfs(fabric_name: str, role: str, switch_name: str)` - 從交換器分離所有 VRF

## [NetworkManager](network/README.md)
- `sync(fabric_name: str)` - 完全同步 Network（刪除多餘、更新現有、創建缺失的 Network）
- `create_network(fabric_name: str, network_name: str)` - 建立網路（先檢查是否已存在）
- `update_network(fabric_name: str, network_name: str)` - 更新網路
- `delete_network(fabric_name: str, network_name: str)` - 刪除網路（自動分離後刪除）
- `sync_attachments(fabric_name: str, role: str, switch_name: str)` - 同步 Network 附加到交換器
- `attach_networks(fabric_name: str, role: str, switch_name: str)` - 將所有 fabric Network 附加到交換器
- `detach_networks(fabric_name: str, role: str, switch_name: str)` - 從交換器分離所有 Network

## [InterfaceManager](interface/README.md)
- `update_switch_interfaces(fabric_name: str, role: str, switch_name: str)` - 更新指定交換器的所有介面配置
  - 自動載入交換器 YAML 配置檔案
  - 支援 Access、Trunk、Routed 介面政策配置
  - 支援 Port-Channel 介面配置和成員介面管理
  - 處理介面啟用/停用狀態
  - 智能處理未在 YAML 中指定的現有介面

## [SwitchManager](switch/README.md)
- `discover_switch(fabric_name: str, role: str, switch_name: str, preserve_config: bool = False)` - 新增交換器
- `delete_switch(fabric_name: str, role: str, switch_name: str)` - 刪除交換器
- `set_switch_role(fabric_name: str, role: str, switch_name: str)` - 設定交換器角色
- `change_switch_ip(fabric_name: str, role: str, switch_name: str, original_ip_with_mask: str, new_ip_with_mask: str)` - 變更交換器管理 IP
- `set_switch_freeform(fabric_name: str, role: str, switch_name: str)` - 執行 freeform 配置
    - 注意: 這個會將 Policy 的 JSON 檔案存下來，以便之後能夠透過 API 讀取並執行
    - 因為在設定的時候實際上是創造出一個 freeform policy，如果之後沒有這個 JSON 檔案就無法知道正確的 policy ID 並做修改
- `change_switch_hostname(fabric_name: str, role: str, switch_name: str, new_hostname: str)` - 變更交換器主機名稱

## [VPCManager](vpc/README.md)
- `create_vpc_pairs(fabric_name: str)` - 建立指定 fabric 的所有 VPC 配對
  - 自動掃描 VPC 配置目錄中的所有 YAML 檔案
  - 解析 VPC 配對資訊和政策配置
  - 建立 VPC 配對並套用政策設定
  - 支援多個 VPC 配對的批次處理
- `delete_vpc_pairs(fabric_name: str, switch_name: str)` - 刪除指定交換器的 VPC 配對
  - 解析交換器名稱並找出對應的 VPC 配對
  - 自動刪除相關的 VPC 政策
  - 移除 VPC 配對關係