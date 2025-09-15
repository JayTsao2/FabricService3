# InterfaceManager
- `update_switch_interfaces(fabric_name: str, role: str, switch_name: str)` - 更新指定交換器的所有介面配置
  - 自動載入交換器 YAML 配置檔案
  - 支援 Access、Trunk、Routed 介面政策配置
  - 支援 Port-Channel 介面配置和成員介面管理
  - 處理介面啟用/停用狀態
- `deploy_switch_interfaces(fabric_name: str, role: str, switch_name: str)` - 部署介面配置到實體交換器
  - 將 NDFC 中的介面配置推送到實體交換器硬體
  - 執行配置部署並驗證結果
- `check_interface_operation_status(fabric_name: str, role: str, switch_name: str)` - 檢查介面操作狀態
  - 驗證介面操作狀態與管理狀態是否一致
  - 用於故障排除和連線問題診斷

## InterfaceManager 配置檔案結構
InterfaceManager 使用交換器 YAML 配置檔案來管理介面：
- **交換器配置路徑**: `network_configs/3_node/{fabric_name}/{role}/{switch_name}.yaml`
- **Freeform 配置支援**: 可透過 freeform 檔案進行額外介面配置

### 交換器介面配置格式
```yaml
Interface:
  Access:
    - Interface: "Ethernet1/1"
      Mode: access
      Description: "Access port for VLAN 100"
      Access VLAN: 100
      Admin Status: true
  
  Trunk:
    - Interface: "Ethernet1/2-5"
      Mode: trunk
      Description: "Trunk port"
      Allowed VLANs: "100,200,300"
      Native VLAN: 1
      Admin Status: true
  
  Routed:
    - Interface: "Ethernet1/10"
      Mode: routed
      Description: "Layer 3 interface"
      IP Address: "192.168.1.1/24"
      Admin Status: true
  
  Port-Channel:
    - Interface: "port-channel10"
      Mode: trunk
      Description: "Port-channel trunk"
      Member Interfaces: "Ethernet1/20,Ethernet1/21"
      Allowed VLANs: "100-200"
      Admin Status: true
```

## InterfaceManager 特色功能
- **YAML 驅動配置**: 所有介面操作基於結構化 YAML 配置檔案
- **多介面類型支援**: 支援 Access、Trunk、Routed、Port-Channel 介面
- **範圍解析**: 支援介面範圍表示法（如 Ethernet1/1-10）
- **政策自動分類**: 自動將介面分配到對應的 NDFC 政策模板
- **智能狀態管理**: 自動處理介面的啟用/停用狀態
- **Port-Channel 管理**: 完整的 Port-Channel 建立和成員介面管理
- **增量更新**: 只更新有變更的介面配置
- **錯誤處理**: 詳細的錯誤訊息和配置驗證
- **Context 管理**: 使用 DataClass 管理複雜的處理流程

## 介面處理流程
1. 載入交換器 YAML 配置檔案
2. 獲取 NDFC 中現有的介面配置
3. 建立介面映射和 Port-Channel 映射
4. 按優先順序處理介面：
   - Port-Channel 介面（優先處理）
   - 一般介面（Access、Trunk、Routed）
   - 未指定的現有介面（設定為停用）
5. 處理需要刪除的 Port-Channel
6. 呼叫相應的 NDFC API 更新介面配置

## 支援的介面類型

### Access 介面
- **用途**: 單一 VLAN 存取埠
- **必要欄位**: Interface, Mode, Access VLAN
- **選用欄位**: Description, Admin Status
- **對應政策**: `int_access_host`

### Trunk 介面
- **用途**: 多 VLAN 中繼埠
- **必要欄位**: Interface, Mode
- **選用欄位**: Description, Allowed VLANs, Native VLAN, Admin Status
- **對應政策**: `int_trunk_host`

### Routed 介面
- **用途**: Layer 3 路由介面
- **必要欄位**: Interface, Mode
- **選用欄位**: Description, IP Address, Admin Status
- **對應政策**: `int_routed_host`

### Port-Channel 介面
- **用途**: 鏈路聚合介面
- **必要欄位**: Interface, Mode, Member Interfaces
- **選用欄位**: Description, Allowed VLANs, Native VLAN, Admin Status
- **對應政策**: `int_port_channel_trunk_host`

## 範圍表示法支援
InterfaceManager 支援多種介面範圍表示法：
- **單一介面**: `Ethernet1/1`
- **介面清單**: `Ethernet1/1,Ethernet1/3,Ethernet1/5`
- **介面範圍**: `Ethernet1/1-10`
- **混合格式**: `Ethernet1/1-5,Ethernet1/10,Ethernet1/15-20`

## Port-Channel 特殊處理
1. **優先處理**: Port-Channel 介面會在一般介面之前處理
2. **成員介面管理**: 自動處理成員介面的加入和移除
3. **映射建立**: 建立成員介面到 Port-Channel 的映射關係
4. **刪除處理**: 自動處理不再需要的 Port-Channel

## 介面狀態管理
- **Admin Status**: 控制介面的啟用/停用狀態
- **預設行為**: 未在 YAML 中指定的介面會被設定為停用
- **智能處理**: 只有狀態有變更的介面才會被更新
- **批次更新**: 使用批次 API 提升效能

## 配置檔案範例

### 完整交換器介面配置
```yaml
# In switch YAML file: network_configs/node/Site1/leaf/Site1-L1.yaml
Interface:
  Access:
    - Interface: "Ethernet1/1"
      Mode: access
      Description: "Server connection VLAN 100"
      Access VLAN: 100
      Admin Status: true
    
    - Interface: "Ethernet1/2-5"
      Mode: access
      Description: "Access ports for VLAN 200"
      Access VLAN: 200
      Admin Status: true
  
  Trunk:
    - Interface: "Ethernet1/10-15"
      Mode: trunk
      Description: "Uplink trunk ports"
      Allowed VLANs: "100,200,300-350"
      Native VLAN: 1
      Admin Status: true
  
  Routed:
    - Interface: "Ethernet1/48"
      Mode: routed
      Description: "Layer 3 uplink"
      IP Address: "10.1.1.1/30"
      Admin Status: true
  
  Port-Channel:
    - Interface: "port-channel10"
      Mode: trunk
      Description: "LAG to spine switches"
      Member Interfaces: "Ethernet1/49,Ethernet1/50"
      Allowed VLANs: "all"
      Admin Status: true
    
    - Interface: "port-channel20"
      Mode: access
      Description: "Server LAG"
      Member Interfaces: "Ethernet1/20,Ethernet1/21"
      Access VLAN: 100
      Admin Status: true
```

## 使用範例
```python
from modules.interface import InterfaceManager

interface_manager = InterfaceManager()

# 更新交換器的所有介面配置
interface_manager.update_switch_interfaces("Site1", "leaf", "Site1-L1")
```

## 錯誤處理和驗證
- **配置檔案驗證**: 檢查必要欄位是否存在
- **介面名稱驗證**: 驗證介面名稱格式是否正確
- **VLAN 範圍檢查**: 驗證 VLAN ID 是否在有效範圍內
- **Port-Channel 成員檢查**: 確保成員介面未被其他 Port-Channel 使用
- **API 錯誤處理**: 詳細記錄 NDFC API 呼叫的錯誤資訊

## 效能優化
- **批次處理**: 相同政策的介面會進行批次更新
- **增量更新**: 只處理有變更的介面
- **延遲載入**: 配置檔案只在需要時載入
- **Context 重用**: 使用 Context 物件減少重複計算

## 與其他模組的整合
- **Switch Module**: 獲取交換器序號和基本資訊
- **Network Module**: 處理 VLAN 和網路相關配置
- **VRF Module**: 處理路由介面的 VRF 分配
- **Policy Module**: 建立和管理介面政策
