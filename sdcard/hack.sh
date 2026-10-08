#!/bin/sh
# /mnt/sdcard/hack.sh  — run by YYOS init.sh when yy_debug.ini has mode=debug.
# Goal: known root password + telnet, keep the camera running, optional WAN block.
SD=/mnt/sdcard
LOG=$SD/hack_log.txt
echo "$(date) - hack.sh start" > $LOG

# 1) Known root password (root/root). $1$ hash below == "root".
#    (/etc/shadow is on a read-only rootfs -> bind-mount a tmpfs copy over it.)
mkdir -p /tmp/etc
echo 'root:$1$hack$26ZSPRIJi4E4euNXpW7mr1:10933:0:99999:7:::' > /tmp/etc/shadow
mount --bind /tmp/etc/shadow /etc/shadow
echo "$(date) - shadow patched (root/root)" >> $LOG

# 2) Telnet (uses the static busybox you placed on the card).
if $SD/busybox telnetd -l /bin/sh -p 23 2>/dev/null; then
    echo "$(date) - telnetd on :23" >> $LOG
fi

# 3) OPTIONAL one-time flash backup to the SD (keep these for recovery).
if [ ! -d "$SD/flash_backup" ]; then
    mkdir -p "$SD/flash_backup"
    for i in 0 1 2 3 4 5; do
        [ -e /dev/mtdblock$i ] && dd if=/dev/mtdblock$i of=$SD/flash_backup/mtd${i}.bin bs=4096 2>/dev/null
    done
    echo "$(date) - flash backup done" >> $LOG
fi

# 4) Hand off to the normal camera boot (required: in debug mode init runs us, not start.sh).
/appfs/script/start.sh &

# 5) OPTIONAL local-only mode: block ALL WAN egress, keep LAN. Toggle with the flag file.
#    No iptables on the box, but /sbin/ip + blackhole /1 routes survive DHCP renew and
#    override the default route while keeping the LAN /24. Reversible: rm the flag + reboot.
if [ -f "$SD/yy_local_only" ]; then
    ( n=0; while [ $n -lt 60 ]; do /sbin/ip addr show wlan0 2>/dev/null | grep -q "inet " && break; sleep 1; n=$((n+1)); done
      /sbin/ip route add blackhole 0.0.0.0/1   2>/dev/null
      /sbin/ip route add blackhole 128.0.0.0/1 2>/dev/null
      echo "$(date) - local-only: WAN blackholed" >> $LOG ) &
fi

echo "$(date) - hack.sh done (UART/telnet login: root/root)" >> $LOG
