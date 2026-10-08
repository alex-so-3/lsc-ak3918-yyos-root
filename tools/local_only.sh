#!/bin/sh
# Run ON the camera (root). Cut ALL internet, keep LAN. No iptables needed.
# Blackhole both /1 halves: more specific than the default route, survive DHCP
# renew, and the LAN /24 stays. Reversible with `del`. hack.sh does this at boot
# when /mnt/sdcard/yy_local_only exists.
#   ./local_only.sh on    |    ./local_only.sh off    |    ./local_only.sh status
case "${1:-on}" in
  on)
    /sbin/ip route add blackhole 0.0.0.0/1   2>/dev/null
    /sbin/ip route add blackhole 128.0.0.0/1 2>/dev/null
    echo "WAN blocked; LAN kept."
    ;;
  off)
    /sbin/ip route del blackhole 0.0.0.0/1   2>/dev/null
    /sbin/ip route del blackhole 128.0.0.0/1 2>/dev/null
    echo "WAN restored."
    ;;
  status)
    /sbin/ip route | grep -c blackhole
    ping -c1 -W2 8.8.8.8 >/dev/null 2>&1 && echo "INET=OPEN" || echo "INET=BLOCKED"
    ;;
esac
