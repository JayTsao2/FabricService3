# SwitchManager
- `discover_switch(fabric_name: str, role: str, switch_name: str, preserve_config: bool = False)` - 基於 YAML 配置發現交換器
  - 自動載入交換器配置檔案並建構 API payload
  - 支援保留現有配置選項
  - 驗證必要欄位（IP、序號、平台等）
- `delete_switch(fabric_name: str, role: str, switch_name: str)` - 基於 YAML 配置刪除交換器
- `set_switch_role(fabric_name: str, role: str, switch_name: str)` - 基於 YAML 配置設定交換器角色
  - 驗證角色是否在允許的枚舉值內
  - 支援的角色：leaf、spine、super spine、border gateway、border gateway spine、border gateway super spine、core router、edge router、tor
- `change_switch_ip(fabric_name: str, role: str, switch_name: str, original_ip: str, new_ip: str)` - 變更交換器管理 IP
  - 透過 SSH 連線到交換器變更 IP
  - 自動更新 NDFC 的發現 IP
  - 執行重新發現流程
- `set_switch_freeform(fabric_name: str, role: str, switch_name: str)` - 執行 freeform 配置
  - 自動刪除現有的 freeform 政策
  - 解析 freeform 配置檔案內容
  - 建立新的 freeform 政策並儲存 JSON 檔案
  - 支援 CLI 命令配置
- `change_switch_hostname(fabric_name: str, role: str, switch_name: str, new_hostname: str)` - 變更交換器主機名稱
  - 查找並更新 host_11_1 政策
  - 自動更新 nvPairs 中的 SWITCH_NAME 欄位
- `rediscover_switch(fabric_name: str, role: str, switch_name: str)` - 重新發現交換器

## SwitchManager 配置檔案結構
SwitchManager 使用 YAML 配置檔案來管理交換器資訊：
- 配置路徑: `network_configs/3_node/{fabric_name}/{role}/{switch_name}.yaml`
- 必要欄位:
  - `IP Address`: 交換器管理 IP
  - `Serial Number`: 交換器序號
  - `Platform`: 交換器平台型號
  - `Role`: 交換器角色
  - `Version`: NX-OS 版本（預設 9.3(15)）
- 選用欄位:
  - `Switch Freeform Config`: freeform 配置檔案路徑

## SwitchManager 特色功能
- **YAML 驅動配置**: 所有操作基於 YAML 配置檔案
- **自動 payload 建構**: 自動從 YAML 建構 API 所需的 payload 格式
- **角色驗證**: 嚴格驗證交換器角色是否符合 NDFC 規範
- **SSH 整合**: 支援透過 SSH 直接變更交換器設定
- **政策管理**: 整合 freeform 政策的建立、更新、刪除
- **錯誤處理**: 完善的檔案存在性檢查和環境變數驗證
- **模型名稱解析**: 自動從平台字串提取模型名稱
- **環境變數整合**: 自動從 .env 檔案載入密碼資訊

## 支援的交換器角色
- `leaf` - 葉交換器
- `spine` - 脊交換器  
- `super spine` - 超級脊交換器
- `border gateway` - 邊界閘道
- `border gateway spine` - 邊界閘道脊交換器
- `border gateway super spine` - 邊界閘道超級脊交換器
- `core router` - 核心路由器
- `edge router` - 邊緣路由器
- `tor` - Top of Rack 交換器

## SSH 管理 IP 變更流程
1. 透過 SSH 連線到原始 IP
2. 執行 `configure terminal; interface mgmt0; ip address {new_ip}; exit; exit`
3. 更新 NDFC 中的發現 IP
4. 執行重新發現流程
5. 驗證變更完成

## Freeform 政策管理
1. 自動刪除交換器上現有的 freeform 政策
2. 解析 freeform 配置檔案中的 CLI 命令
3. 建立具有隨機 ID 的新政策
4. 儲存政策 JSON 檔案以供後續管理
5. 支援完整的 CLI 命令配置

## 配置檔案範例
```yaml
IP Address: 10.192.195.73
Serial Number: 9ABCDEFGHIJ
Platform: N9K-C9300v
Role: leaf
Version: 9.3(15)
Switch Freeform Config: FreeForm/leaf_config.sh
```

## 使用範例
```python
from modules.switch import SwitchManager

switch_manager = SwitchManager()

# 發現交換器
switch_manager.discover_switch("Site1", "leaf", "Site1-L1")

# 設定角色
switch_manager.set_switch_role("Site1", "leaf", "Site1-L1")

# 變更管理 IP
switch_manager.change_switch_ip("Site1", "leaf", "Site1-L1", "10.1.1.1/24", "10.1.1.2/24")

# 設定 freeform 配置
switch_manager.set_switch_freeform("Site1", "leaf", "Site1-L1")

# 變更主機名稱
switch_manager.change_switch_hostname("Site1", "leaf", "Site1-L1", "NewHostname")
```
