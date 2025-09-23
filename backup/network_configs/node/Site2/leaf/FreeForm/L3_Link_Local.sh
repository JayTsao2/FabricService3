  bfd interval 500 min_rx 500 multiplier 6
  no bfd echo
  no bfd ipv6 echo
  no ip redirects
  ip forward
  ipv6 address use-link-local-only
  ipv6 nd ra-interval 4 min 3
  ipv6 nd ra-lifetime 10
  no ipv6 redirects
