  template peer iBGP-PEER-Template
    remote-as $BGP_ASN
    log-neighbor-changes
    update-source loopback1
    address-family l2vpn evpn
      send-community
      send-community extended