feature telnet
feature lldp
clock timezone Taiwan 8 0
no ip domain-lookup
ip domain-name tsmc.com.tw

ip name-server 10.10.1.1 10.10.2.2
ip access-list NETWORK_ADMIN
  10 remark TW Admin Zone
  20 permit ip 10.66.0.0/16 any
  30 permit ip 10.67.0.0/16 any
  40 permit ip 10.68.0.0/16 any
  50 remark HQ ENT Admin Zone 1.5
  60 permit ip 10.164.137.0/24 any log
  70 permit ip 10.164.134.0/24 any log
  80 permit ip 10.164.139.0/24 any log
  90 remark TW Break Glass servers
  100 permit ip 10.228.94.227/32 any log
  110 permit ip 10.228.94.228/32 any log
  120 permit ip 10.79.236.32/32 any log
  130 permit ip 10.223.236.32/32 any log
  140 permit ip 10.164.89.31/32 any log
  150 permit ip 10.164.90.31/32 any log
  160 remark Ent/Infra TKS Automation service
  170 permit ip 10.225.248.0/24 any
  180 permit ip 10.225.60.0/24 any
  250 remark H-site office service and algosec
  260 permit ip 10.228.91.0/24 any
  270 permit ip 11.63.52.0/22 any
  500 remark edge TKS Automation service
  510 permit ip 10.20.137.0/24 any
  520 permit ip 10.20.138.0/24 any
  530 permit ip 10.20.213.0/24 any
  540 permit ip 10.20.245.0/24 any
  550 permit ip 10.21.21.0/24 any
  560 permit ip 10.21.53.0/24 any
  570 permit ip 10.22.138.0/24 any
  580 permit ip 10.21.85.0/24 any
  590 permit ip 10.21.117.0/24 any
  600 permit ip 10.22.170.0/24 any
  610 permit ip 10.21.149.0/24 any
  620 permit ip 10.21.181.0/24 any
  630 permit ip 10.22.154.0/24 any
  640 permit ip 10.23.21.0/24 any
  650 permit ip 10.23.53.0/24 any
  660 permit ip 10.21.213.0/24 any
  670 permit ip 10.21.245.0/24 any
  680 permit ip 10.21.186.0/24 any
  690 permit ip 10.23.85.0/24 any
  700 permit ip 10.23.117.0/24 any
  710 permit ip 10.22.202.0/24 any
  720 permit ip 10.23.245.0/24 any
  730 permit ip 10.22.85.0/24 any
  740 permit ip 10.22.117.0/24 any
  750 permit ip 10.23.149.0/24 any
  760 permit ip 10.23.181.0/24 any
  970 deny tcp any any eq telnet log
  980 deny tcp any any eq 22 log
  990 permit ip any any
snmp-server source-interface traps mgmt0
snmp-server host 10.228.90.84 traps version 2c public
snmp-server host 10.228.90.84 use-vrf management
snmp-server host 10.228.90.85 traps version 2c public
snmp-server host 10.228.90.85 use-vrf management
snmp-server host 10.11.116.100 traps version 2c public
snmp-server host 10.11.116.100 use-vrf management
snmp-server host 10.11.117.100 traps version 2c public
snmp-server host 10.11.117.100 use-vrf management
snmp-server enable traps callhome event-notify
snmp-server enable traps callhome smtp-send-fail
snmp-server enable traps cfs state-change-notif
snmp-server enable traps lldp lldpRemTablesChange
snmp-server enable traps cfs merge-failure
snmp-server enable traps aaa server-state-change
snmp-server enable traps feature-control FeatureOpStatusChange
snmp-server enable traps sysmgr cseFailSwCoreNotifyExtended
snmp-server enable traps config ccmCLIRunningConfigChanged
snmp-server enable traps snmp authentication
snmp-server enable traps link cisco-xcvr-mon-status-chg
snmp-server enable traps vtp notifs
snmp-server enable traps vtp vlancreate
snmp-server enable traps vtp vlandelete
snmp-server enable traps bridge newroot
snmp-server enable traps bridge topologychange
snmp-server enable traps stpx inconsistency
snmp-server enable traps stpx root-inconsistency
snmp-server enable traps stpx loop-inconsistency
snmp-server enable traps system Clock-change-notification
snmp-server enable traps feature-control ciscoFeatOpStatusChange
snmp-server enable traps mmode cseNormalModeChangeNotify
snmp-server enable traps mmode cseMaintModeChangeNotify
snmp-server enable traps syslog message-generated
snmp-server community public group network-operator
ntp server 10.11.82.31 use-vrf management
ntp server 10.11.83.31 use-vrf management
ntp source-interface mgmt0
ip igmp snooping vxlan
system vlan long-name
spanning-tree pathcost method long
spanning-tree port type edge bpduguard default
spanning-tree port type edge bpdufilter default
spanning-tree vlan 1-3967 priority 8192
line console
  exec-timeout 60
line vty
  session-limit 10
  exec-timeout 60
  access-class NETWORK_ADMIN in
logging logfile messages 6 size 81920
logging server 10.228.90.42 6 use-vrf management
logging server 10.228.90.43 6 use-vrf management
logging server 10.11.116.100 6 use-vrf management
logging server 10.11.117.100 6 use-vrf management
logging source-interface mgmt0
logging level local7 6
logging origin-id hostname