ip prefix-list share_route seq 5 permit 100.118.0.0/16
ip prefix-list share_route seq 10 permit 10.23.192.0/19
ip prefix-list share_route seq 15 permit 10.253.192.0/19

ip prefix-list vpc10 seq 5 permit 100.120.0.0/16 le 32
ip prefix-list vpc11 seq 5 permit 100.121.0.0/16 le 32

route-map vpc_to_sharevrf permit 10
  match ip address prefix-list share_route vpc10 vcp11

route-map share_to_vpc permit 10
  match ip address prefix-list share_route

route-map share_to_vpc_10 permit 10
  match ip address prefix-list share_route vpc10

route-map vpc10_to_shareVRF permit 10
  match ip address prefix-list vpc10

route-map share_to_vpc_11 permit 10
  match ip address prefix-list share_route vpc11

route-map vpc11_to_shareVRF permit 10
  match ip address prefix-list vpc11

vrf context Z01
  address-family ipv4 unicast
    route-target import 23456:33910
    route-target import 23456:33910 evpn
    route-target import 23456:33911
    route-target import 23456:33911 evpn
    export map share_to_vpc
    import map vpc_to_sharevrf

vrf context VPC10
  address-family ipv4 unicast
    route-target import 23456:33901
    route-target import 23456:33901 evpn
    export map vpc10_to_shareVRF
    import map share_to_vpc_10

vrf context VPC11
  address-family ipv4 unicast
    route-target import 23456:33901
    route-target import 23456:33901 evpn
    export map vpc11_to_shareVRF
    import map share_to_vpc_11

router bgp $BGP_ASN
  template peer ebgp-peer-template-node
    bfd
    remote-as $BGP_ASN
    address-family ipv4 unicast
      as-override
      disable-peer-as-check
      soft-reconfiguration inbound always


