# VRFManager
- `sync(fabric_name: str)` - 完全同步 VRF（刪除多餘、更新現有、創建缺失的 VRF）
  - 比較 YAML 配置與 fabric 中現有 VRF
  - 自動刪除 fabric 中多餘的 VRF
  - 更新既存 VRF 的配置
  - 創建缺失的 VRF
- `create_vrf(fabric_name: str, vrf_name: str)` - 在指定 fabric 建立 VRF
  - 先檢查 VRF 是否已存在，避免重複創建
  - 自動載入 VRF 配置並建構 API payload
  - 合併企業預設配置與 VRF 特定配置
  - 套用欄位映射轉換為 NDFC API 格式
- `update_vrf(fabric_name: str, vrf_name: str)` - 更新指定 VRF
- `delete_vrf(fabric_name: str, vrf_name: str)` - 刪除指定 VRF
  - 刪除前自動從所有交換器分離 VRF
  - 確保安全刪除，避免依賴衝突
- `sync_attachments(fabric_name: str, role: str, switch_name: str)` - 同步 VRF 附加到指定交換器
  - 先分離不需要的 VRF，再附加需要的 VRF
  - 確保交換器上的 VRF 與交換器介面配置一致
- `attach_vrf(fabric_name: str, role: str, switch_name: str, vrf_name: str)` - 將特定 VRF 附加到交換器
  - 自動載入交換器配置和序列號
  - 解析 VRF VLAN ID 並建構附加 payload
- `attach_vrfs(fabric_name: str, role: str, switch_name: str)` - 將 VRF 附加到指定交換器
  - 自動掃描交換器介面配置中的路由介面 (int_routed_host policy)
  - 提取介面 VRF 配置並執行 VRF 附加
  - 避免重複處理相同的 VRF
- `detach_vrf(fabric_name: str, role: str, switch_name: str, vrf_name: str)` - 從指定交換器分離特定 VRF
- `detach_vrfs(fabric_name: str, role: str, switch_name: str)` - 從指定交換器分離所有 VRF
  - 自動檢測目前附加到交換器的所有 VRF
  - 批次分離已附加的 VRF

## VRFManager 配置檔案結構
VRFManager 使用 YAML 配置檔案來管理 VRF 資訊：
- **VRF 配置路徑**: `network_configs/5_segment/vrf.yaml`
- **企業預設配置**: `resources/corp_defaults/cisco_vrf.yaml`
- **欄位映射配置**: `resources/field_mapping/cisco_vrf.yaml`
- **交換器配置路徑**: `network_configs/3_node/{fabric_name}/{role}/{switch_name}.yaml`

### VRF 配置檔案格式
```yaml
VRF:
  - VRF Name: "bluevrf"
    Fabric: "Site1"
    VRF ID: 50001
    VLAN ID: 2001
    Layer 2 Only: false
    General Parameters:
      VRF Description: "Blue VRF for Site1"
      VRF VLAN Name: "bluevrf_vlan"
      VRF Interface Description: "Blue VRF Interface"
    # Additional VRF-specific configurations
```

- **VRF 附加配置**: 交換器 YAML 檔案中的介面配置區段
  - 支援 `int_routed_host` 政策的介面自動 VRF 附加
  - 從 `Interface VRF` 欄位提取 VRF 資訊

## VRFManager 特色功能
- **YAML 驅動配置**: 所有操作基於結構化 YAML 配置檔案
- **企業預設整合**: 自動合併企業預設配置與 VRF 特定配置
- **欄位映射**: 自動將 YAML 配置轉換為 NDFC API 所需格式
- **智能同步**: 比較現有配置與目標配置，執行增量更新
- **延遲載入**: 配置檔案只在需要時載入，提升效能
- **錯誤處理**: 完善的檔案存在性檢查和配置驗證
- **介面整合**: 自動從交換器介面配置中提取 VRF 附加資訊
- **重複檢查**: 創建前檢查是否已存在，避免重複操作
- **安全刪除**: 刪除 VRF 前自動處理分離作業
- **批次操作**: 支援一次處理多個 VRF 的附加/分離

## VRF 同步流程
1. 獲取 fabric 中現有的所有 VRF
2. 載入 YAML 配置中的目標 VRF 清單
3. 識別需要刪除的 VRF（存在於 fabric 但不在 YAML 中）
4. 識別需要建立的 VRF（存在於 YAML 但不在 fabric 中）
5. 識別需要更新的 VRF（同時存在於兩者中）
6. 按順序執行刪除、更新、建立操作

## VRF 附加流程
1. 載入交換器配置檔案
2. 掃描介面配置尋找 `int_routed_host` 政策的介面
3. 提取介面的 `Interface VRF` 配置
4. 為每個唯一的 VRF 建構附加 payload
5. 呼叫 NDFC API 執行 VRF 附加操作

## 配置檔案範例

### VRF 主配置檔案 (network_configs/5_segment/vrf.yaml)
```yaml
VRF:
  - VRF Name: "bluevrf"
    Fabric: "Site1"
    VRF ID: 50001
    VLAN ID: 2001
    Layer 2 Only: false
    General Parameters:
      VRF Description: "Blue VRF for production traffic"
      VRF VLAN Name: "prod_blue_vlan"
      VRF Interface Description: "Production Blue VRF Interface"
  
  - VRF Name: "redvrf"
    Fabric: "Site1"
    VRF ID: 50002
    VLAN ID: 2002
    Layer 2 Only: false
    General Parameters:
      VRF Description: "Red VRF for test traffic"
      VRF VLAN Name: "test_red_vlan"
      VRF Interface Description: "Test Red VRF Interface"
```

### 交換器介面配置中的 VRF 設定
```yaml
# In switch YAML file: network_configs/node/Site1/leaf/Site1-L1.yaml
Interface:
  - Ethernet1/1:
      policy: "int_routed_host"
      Interface VRF: "bluevrf"
      IPv4 Address: "192.168.1.1/24"
  - Ethernet1/2:
      policy: "int_routed_host"  
      Interface VRF: "redvrf"
      IPv4 Address: "192.168.2.1/24"
```

## 使用範例
```python
from modules.vrf import VRFManager

vrf_manager = VRFManager()

# 同步所有 VRF
vrf_manager.sync("Site1")

# 建立特定 VRF
vrf_manager.create_vrf("Site1", "bluevrf")

# 更新 VRF
vrf_manager.update_vrf("Site1", "bluevrf")

# 同步 VRF 附加到交換器（分離不需要的，附加需要的）
vrf_manager.sync_attachments("Site1", "leaf", "Site1-L1")

# 附加特定 VRF 到交換器
vrf_manager.attach_vrf("Site1", "leaf", "Site1-L1", "bluevrf")

# 附加所有相關 VRF 到交換器（基於介面配置）
vrf_manager.attach_vrfs("Site1", "leaf", "Site1-L1")

# 從交換器分離特定 VRF
vrf_manager.detach_vrf("Site1", "leaf", "Site1-L1", "bluevrf")

# 從交換器分離所有已附加的 VRF
vrf_manager.detach_vrfs("Site1", "leaf", "Site1-L1")
```
