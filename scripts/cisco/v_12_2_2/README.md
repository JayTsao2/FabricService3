# 資料夾用途說明

* **`/api`**
    * 用途: Cisco NDFC 12.2.2 版本的 API 操作模組。
    
* **`/modules`**
    * 用途: 模組化功能組織，包含 fabric、VRF、network、interface、switch 等模組。
    
    * **`/modules/fabric`**
        * 用途: Fabric 管理模組，包含建立、更新、刪除功能以及統一管理介面 (FabricManager)。
        
    * **`/modules/vrf`**
        * 用途: VRF 管理模組，包含建立、更新、刪除、附加、分離、同步功能以及統一管理介面 (VRFManager)。
        
    * **`/modules/network`**
        * 用途: Network 管理模組，提供統一的網路 CRUD 操作與交換器附加功能。
        
    * **`/modules/interface`**
        * 用途: Interface 管理模組，提供 YAML 驅動的介面配置更新功能。
        
    * **`/modules/switch`**
        * 用途: Switch 管理模組，提供交換器發現、刪除、角色設定、IP 變更等功能。
    
    * **`/modules/vpc`**
        * 用途: VPC 管理模組，提供 VPC 配對建立、刪除、政策配置等功能。
    
    * **`/modules/config_utils.py`**
        * 用途: 配置工具函數模組，提供 YAML 載入與驗證功能。
    
* **`/resources`**
    * 用途: 配置檔案、模板、欄位映射等資源檔案。
    
* **`/fabric_cli.py`**
    * 用途: Fabric 管理命令列介面工具，使用 FabricManager 提供統一的操作介面。
    
* **`/vrf_cli.py`**
    * 用途: VRF 管理命令列介面工具，使用 VRFManager 提供統一的操作介面。
    
* **`/network_cli.py`**
    * 用途: Network 管理命令列介面工具。
    
* **`/interface_cli.py`**
    * 用途: Interface 管理命令列介面工具。

* **`/switch_cli.py`**
    * 用途: Switch 管理命令列介面工具。

# 用法:
- 記得要將 `.env.example` 檔案名稱改變成 `.env`，並填入裡面的東西
```txt
NDFC_API_KEY=<your_api_key>
LOGIN_USERNAME=<your_NDFC_username>
LOGIN_PASSWORD=<your_NDFC_password>
SWITCH_PASSWORD=<your_switch_password>
```
- API key 可以透過 `scripts/cisco/12.2.2/api/key.py` 生成
```bash
python scripts/cisco/12.2.2/api/key.py
```

# API Interfaces
- Check [API DOCS](api/README.md)

# Manager 可使用功能
- Check Managers Overview [here](modules/README.md)

# CLI Tools

## [Fabric CLI](fabric_cli.py)

**使用方式 (Usage):**
```bash
# 在 /scripts/cisco/12.2.2/ 目錄下執行
python fabric_cli.py create <fabric_name>      # 建立特定 fabric
python fabric_cli.py update <fabric_name>      # 更新特定 fabric
python fabric_cli.py delete <fabric_name>      # 刪除特定 fabric (需確認)
python fabric_cli.py recalculate <fabric_name> # 重新計算 fabric 配置
python fabric_cli.py get-pending <fabric_name> # 獲取待部署配置 (儲存至 pending.txt)
python fabric_cli.py deploy <fabric_name>      # 部署 fabric 配置
python fabric_cli.py add-msd <parent> <child>  # 將子 fabric 加入 MSD
python fabric_cli.py remove-msd <parent> <child> # 從 MSD 移除子 fabric

# 顯示幫助資訊
python fabric_cli.py --help
```

## [VRF CLI](vrf_cli.py)

**使用方式 (Usage):**
```bash
# 在 /scripts/cisco/12.2.2/ 目錄下執行
python vrf_cli.py create <fabric_name> <vrf_name>     # 建立特定 VRF
python vrf_cli.py update <fabric_name> <vrf_name>     # 更新特定 VRF
python vrf_cli.py delete <fabric_name> <vrf_name>     # 刪除特定 VRF
python vrf_cli.py attach <fabric_name> <switch_role> <switch_name>   # 附加 VRF 到交換器
python vrf_cli.py detach <fabric_name> <switch_role> <switch_name>   # 從交換器分離 VRF
python vrf_cli.py sync <fabric_name>                  # 同步所有 VRF (刪除不需要的、更新既存的、建立缺少的)

# 範例
python vrf_cli.py create Site1 bluevrf         # 建立 bluevrf VRF
python vrf_cli.py delete Site1 bluevrf         # 刪除 bluevrf VRF
python vrf_cli.py attach Site1 leaf Site1-L1    # 附加 VRF 到指定 leaf 交換器
python vrf_cli.py detach Site1 leaf Site1-L1    # 從指定 leaf 交換器分離 VRF
python vrf_cli.py sync Site3-Test              # 同步 Site3-Test fabric 的所有 VRF

# 顯示幫助資訊
python vrf_cli.py --help
```

## [Network CLI](network_cli.py)

**使用方式 (Usage):**
```bash
# 在 /scripts/cisco/12.2.2/ 目錄下執行
python network_cli.py create <fabric_name> <network_name>     # 建立特定 Network
python network_cli.py update <fabric_name> <network_name>     # 更新特定 Network
python network_cli.py delete <fabric_name> <network_name>     # 刪除特定 Network
python network_cli.py attach <fabric_name> <switch_role> <switch_name>   # 附加 Network 到交換器
python network_cli.py detach <fabric_name> <switch_role> <switch_name>   # 從交換器分離 Network

# 範例
python network_cli.py create Site1 bluenet1        # 建立 bluenet1 Network
python network_cli.py attach Site1 leaf Site1-L1   # 附加 Network 到指定 leaf 交換器
python network_cli.py detach Site1 leaf Site1-L1   # 從指定 leaf 交換器分離 Network

# 顯示幫助資訊
python network_cli.py --help
```


## [Interface CLI](interface_cli.py)
**使用方式 (Usage):**
```bash
# 在 /scripts/cisco/12.2.2/ 目錄下執行
python interface_cli.py update <fabric_name> <role> <switch_name>   # 更新指定交換器的介面配置
python interface_cli.py deploy <fabric_name> <role> <switch_name>   # 部署介面配置到實體交換器
python interface_cli.py check <fabric_name> <role> <switch_name>    # 檢查介面操作狀態

# 範例
python interface_cli.py update Site1 leaf Site1-L1    # 更新 Site1-L1 交換器的介面配置
python interface_cli.py deploy Site1 leaf Site1-L1    # 部署介面配置到 Site1-L1 交換器
python interface_cli.py check Site1 leaf Site1-L1     # 檢查 Site1-L1 交換器的介面狀態

# 顯示幫助資訊
python interface_cli.py --help
python interface_cli.py update --help    # 查看 update 命令的詳細說明
python interface_cli.py deploy --help    # 查看 deploy 命令的詳細說明
python interface_cli.py check --help     # 查看 check 命令的詳細說明
```

## [Switch CLI](switch_cli.py)

**使用方式 (Usage):**
```bash
# 在 /scripts/cisco/12.2.2/ 目錄下執行
python switch_cli.py discover <fabric_name> <role> <switch_name> [--preserve]   # 發現交換器
python switch_cli.py delete <fabric_name> <role> <switch_name>                  # 刪除交換器
python switch_cli.py set-role <fabric_name> <role> <switch_name>                # 設定交換器角色
python switch_cli.py change-ip <fabric_name> <role> <switch_name> <original-ip>/<mask> <new-ip>/<mask>  # 變更管理 IP
python switch_cli.py set-freeform <fabric_name> <role> <switch_name>            # 執行 freeform 配置
python switch_cli.py hostname <fabric_name> <role> <switch_name> <new_hostname> # 變更交換器主機名稱
python switch_cli.py create-vpc <fabric_name>                                   # 建立 VPC 配對並設定政策
python switch_cli.py delete-vpc <fabric_name> <switch_name>                     # 刪除指定交換器的 VPC 配對

# 範例
python switch_cli.py discover Site1 leaf Site1-L1 --preserve                    # 發現交換器並保留配置
python switch_cli.py delete Site1 leaf Site1-L1                                 # 從 fabric 移除交換器
python switch_cli.py set-role Site1 leaf Site1-L1                               # 設定 Site1-L1 的角色
python switch_cli.py change-ip Site1 leaf Site1-L1 10.192.195.73/24 10.192.195.74/24  # 變更管理 IP
python switch_cli.py set-freeform Site1 border_gateway Site1-BGW2               # 執行 freeform 配置
python switch_cli.py hostname Site1 leaf Site1-L1 Site1-L1-NEW                  # 變更主機名稱
python switch_cli.py create-vpc Site1                                           # 建立 Site1 fabric 所有 VPC 配對
python switch_cli.py delete-vpc Site1 Site1-L1                                  # 刪除 Site1-L1 交換器的 VPC 配對

# 顯示幫助資訊
python switch_cli.py --help
python switch_cli.py <command> --help
```