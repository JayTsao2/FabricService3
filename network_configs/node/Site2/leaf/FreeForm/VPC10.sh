router bgp $BGP_ASN
  vrf vpc10
    neighbor Ethernet1/21
      inherit peer ebgp-peer-template-node
    neighbor Ethernet1/22
      inherit peer ebgp-peer-template-node