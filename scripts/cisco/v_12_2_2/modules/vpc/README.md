# VPCManager
- `create_vpc_pairs(fabric_name: str)` - 建立指定 fabric 的所有 VPC 配對
  - 自動掃描 VPC 配置目錄中的所有 YAML 檔案
  - 解析 VPC 配對資訊和政策配置
  - 建立 VPC 配對並套用政策設定
  - 支援多個 VPC 配對的批次處理
- `delete_vpc_pairs(fabric_name: str, switch_name: str)` - 刪除指定交換器的 VPC 配對
  - 解析交換器名稱並找出對應的 VPC 配對
  - 自動刪除相關的 VPC 政策
  - 移除 VPC 配對關係

## VPCManager 配置檔案結構
VPCManager 使用 YAML 配置檔案來管理 VPC 配對：
- **VPC 配置路徑**: `network_configs/3_node/{fabric_name}/vpc/{switch1}={switch2}={vpc_name}.yaml`
- **檔案命名格式**: `{Peer1_Name}={Peer2_Name}={VPC_Name}.yaml`

### VPC 配置檔案格式
```yaml
Peer-1 Serial Number: "9ABCDEFGHIJ"
Peer-2 Serial Number: "9KLMNOPQRST"

Policy:
  Name: "int_vpc_trunk_host"
  Policy Options:
    Peer-1 Port-Channel ID: 1
    Peer-2 Port-Channel ID: 1
    Port Channel Mode: "active"
    Peer-1 Member Interfaces: "Ethernet1/1,Ethernet1/2"
    Peer-2 Member Interfaces: "Ethernet1/1,Ethernet1/2"
    Peer-1 Trunk Allowed Vlans: "100,200,300"
    Peer-2 Trunk Allowed Vlans: "100,200,300"
    Enable BPDU Guard: false
    Port Channel Mode: "active"
    INTF Description: "VPC between leaf switches"
```

## VPCManager 特色功能
- **YAML 驅動配置**: 所有 VPC 操作基於結構化 YAML 配置檔案
- **批次 VPC 處理**: 自動處理 fabric 中的所有 VPC 配對
- **政策整合**: 建立 VPC 配對的同時自動套用介面政策
- **檔案命名解析**: 從檔案名稱自動解析 VPC 名稱和配對資訊
- **錯誤處理**: 完善的配置驗證和錯誤訊息
- **序號驗證**: 驗證交換器序號的有效性
- **靈活配置**: 支援不同的 VPC 政策選項

## VPC 建立流程
1. 掃描指定 fabric 的 VPC 配置目錄
2. 載入所有 YAML 配置檔案
3. 驗證配置檔案格式和必要欄位
4. 按檔案順序處理每個 VPC 配對：
   - 解析交換器序號
   - 建立 VPC 配對
   - 建構政策 payload
   - 套用 VPC 介面政策
5. 記錄處理結果和錯誤

## VPC 政策配置選項

### 基本政策欄位
- **Name**: VPC 政策名稱（通常為 `int_vpc_trunk_host`）
- **Peer-1/2 Port-Channel ID**: 各自的 Port-Channel ID
- **Port Channel Mode**: LACP 模式（active/passive/on）
- **Member Interfaces**: 各 peer 的成員介面清單

### Trunk 相關選項
- **Peer-1/2 Trunk Allowed Vlans**: 允許的 VLAN 清單
- **Native VLAN**: 原生 VLAN ID
- **Trunk Mode**: Trunk 模式設定

### 安全和管理選項
- **Enable BPDU Guard**: 啟用 BPDU 防護
- **INTF Description**: 介面描述
- **Enable Fast Convergence**: 啟用快速收斂

## 檔案命名慣例
VPC 配置檔案遵循特定的命名格式：
- **格式**: `{Switch1_Name}={Switch2_Name}={VPC_Name}.yaml`
- **範例**: `Site1-L1=Site1-L2=vPC6.yaml`
- **解析**: 系統會自動從檔案名稱提取 VPC 名稱

## VPC 刪除流程
1. 根據交換器名稱找出相關的 VPC 配置檔案
2. 解析配對的另一台交換器
3. 刪除 VPC 相關的介面政策
4. 移除 VPC 配對關係

## 配置檔案範例

### VPC 配對配置檔案
```yaml
# File: network_configs/node/Site1/vpc/Site1-L1=Site1-L2=vPC6.yaml
Peer-1 Serial Number: "9A1B2C3D4E5"
Peer-2 Serial Number: "9F6G7H8I9J0"

Policy:
  Name: "int_vpc_trunk_host"
  Policy Options:
    Peer-1 Port-Channel ID: 6
    Peer-2 Port-Channel ID: 6
    Port Channel Mode: "active"
    Peer-1 Member Interfaces: "Ethernet1/47,Ethernet1/48"
    Peer-2 Member Interfaces: "Ethernet1/47,Ethernet1/48"
    Peer-1 Trunk Allowed Vlans: "100,200,300-350"
    Peer-2 Trunk Allowed Vlans: "100,200,300-350"
    Enable BPDU Guard: true
    INTF Description: "VPC6 between Site1-L1 and Site1-L2"
```

### Access VPC 配置
```yaml
# File: network_configs/node/Site1/vpc/Site1-L1=Site1-L2=vPC7.yaml
Peer-1 Serial Number: "9A1B2C3D4E5"
Peer-2 Serial Number: "9F6G7H8I9J0"

Policy:
  Name: "int_vpc_access_host"
  Policy Options:
    Peer-1 Port-Channel ID: 7
    Peer-2 Port-Channel ID: 7
    Port Channel Mode: "active"
    Peer-1 Member Interfaces: "Ethernet1/10"
    Peer-2 Member Interfaces: "Ethernet1/10"
    Access VLAN: 100
    Enable BPDU Guard: true
    INTF Description: "Server VPC7 access port"
```

## 使用範例
```python
from modules.vpc import VPCManager

vpc_manager = VPCManager()

# 建立 fabric 中所有的 VPC 配對
vpc_manager.create_vpc_pairs("Site1")

# 刪除特定交換器的 VPC 配對
vpc_manager.delete_vpc_pairs("Site1", "Site1-L1")
```

## 錯誤處理和驗證
- **配置檔案驗證**: 檢查必要欄位（序號、政策選項）
- **序號格式驗證**: 確保交換器序號格式正確
- **成員介面驗證**: 檢查成員介面格式和重複性
- **VLAN 範圍檢查**: 驗證 VLAN ID 和範圍的有效性
- **Port-Channel ID 檢查**: 避免 Port-Channel ID 衝突

## 與其他模組的整合
- **Switch Module**: 驗證交換器序號和基本資訊
- **Interface Module**: 整合 Port-Channel 介面配置
- **Policy Module**: 建立和管理 VPC 相關政策
- **Fabric Module**: 確保 VPC 在正確的 fabric 中建立

## 政策模板支援
VPCManager 支援多種 VPC 政策模板：
- **int_vpc_trunk_host**: Trunk 模式 VPC
- **int_vpc_access_host**: Access 模式 VPC
- **自定義政策**: 支援使用者定義的政策模板

## 批次處理優化
- **並行處理**: 支援多個 VPC 配對的並行建立
- **錯誤隔離**: 單一 VPC 失敗不影響其他 VPC 的處理
- **結果統計**: 提供詳細的處理結果統計
- **回滾機制**: 支援部分成功情況下的狀態管理

## 監控和日誌
- **詳細日誌**: 記錄每個步驟的執行狀況
- **錯誤追蹤**: 提供具體的錯誤位置和原因
- **成功統計**: 統計成功建立的 VPC 數量
- **效能監控**: 記錄每個操作的執行時間
