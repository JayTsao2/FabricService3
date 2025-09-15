feature telnet
clock timezone Taiwan 8 0
no ip domain-lookup
ip domain-name tsmc.com.tw
ip access-list ACL-Telnet
  statistics per-entry
  10 permit ip 10.67.0.0/16 any
  20 permit ip 10.72.81.0/24 any
  30 permit ip 10.70.32.0/24 any
  40 permit ip 10.218.32.0/24 any
  50 permit ip 10.151.141.41/32 any
  60 permit ip 10.73.148.140/32 any
  70 permit ip 10.151.141.42/32 any
  80 permit ip 10.79.236.0/24 any
  90 permit ip 10.223.236.0/24 any
  100 deny ip any any

snmp-server source-interface traps mgmt0
snmp-server host 10.212.32.40 traps version 2c public
snmp-server host 10.212.32.40 use-vrf management
snmp-server host 10.212.33.41 traps version 2c public
snmp-server host 10.212.33.41 use-vrf management
snmp-server enable traps bgp
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
snmp-server community public group network-operator

router ospf 100
  log-adjacency-changes
  timers throttle spf 50 50 5000
  timers lsa-group-pacing 240
  timers lsa-arrival 15
  timers throttle lsa 0 50 5000

line console
  exec-timeout 60

line vty
  session-limit 10
  exec-timeout 60
  access-class ACL-Telnet in

logging logfile messages 6 size 81920
logging source-interface mgmt0