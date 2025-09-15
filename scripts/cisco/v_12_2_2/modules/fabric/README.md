# FabricManager
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

# FabricManager 支援的 Fabric 類型
1. **VXLAN EVPN Fabric** (Easy_Fabric)
   - 配置路徑: `network_configs/1_vxlan_evpn/fabrics/{fabric_name}.yaml`
   - 預設配置: `resources/corp_defaults/cisco_vxlan.yaml`
   - 欄位映射: `resources/field_mapping/cisco_vxlan.yaml`
   - 支援 freeform 配置: AAA、Leaf、Spine、Intra-fabric Links、Banner、iBGP Peer-Template

2. **Multi-Site Domain Fabric** (MSD_Fabric)
   - 配置路徑: `network_configs/1_vxlan_evpn/multisite_deployment/{fabric_name}.yaml`
   - 預設配置: `resources/corp_defaults/cisco_multi-site.yaml`
   - 欄位映射: `resources/field_mapping/cisco_multi-site.yaml`

3. **Inter-Site Network Fabric** (External_Fabric)
   - 配置路徑: `network_configs/1_vxlan_evpn/inter-site_network/{fabric_name}.yaml`
   - 預設配置: `resources/corp_defaults/cisco_inter-site.yaml`
   - 欄位映射: `resources/field_mapping/cisco_inter-site.yaml`
   - 支援 freeform 配置: Fabric Freeform、AAA
