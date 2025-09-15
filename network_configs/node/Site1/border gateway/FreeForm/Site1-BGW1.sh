route-map bdl_core permit 10
  match ip address prefix-list ms

router bgp 4240650100
  rd dual id 1
  template peer EBGP-PEER-TEMPLATE-CORE
    bfd
    log-neighbor-changes
    address-family ipv4 unicast
      route-map bdl_core out
      soft-reconfiguration inbound always
    address-family ipv6 unicast
      soft-reconfiguration inbound always
  vrf Z01
    router-id 100.86.255.21
    neighbor Ethernet1/34
      inherit peer EBGP-PEER-TEMPLATE-CORE
      remote-as 4240600101
    neighbor Ethernet1/35
      inherit peer EBGP-PEER-TEMPLATE-CORE
      remote-as 4240600101
    neighbor Ethernet1/36
      inherit peer EBGP-PEER-TEMPLATE-CORE
      remote-as 4240600101