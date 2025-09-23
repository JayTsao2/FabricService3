router bgp $BGP_ASN
  vrf Z01
    neighbor Ethernet1/15
      inherit peer ebgp-peer-template-node
    neighbor Ethernet1/16
      inherit peer ebgp-peer-template-node
