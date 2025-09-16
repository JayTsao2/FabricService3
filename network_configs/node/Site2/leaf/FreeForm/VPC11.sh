router bgp $BGP_ASN
  vrf vpc11
    neighbor Ethernet1/25
      inherit peer ebgp-peer-template-node
    neighbor Ethernet1/26
      inherit peer ebgp-peer-template-node
