#!/bin/bash
# Build static BusyBox for ARM926EJ-S. Output -> /out/busybox (+ /out/busybox.config).
set -euxo pipefail
BBX_VER="${BBX_VER:-1.36.1}"
CROSS="arm-linux-gnueabi-"
cd /build
[ -f "busybox-${BBX_VER}.tar.bz2" ] || wget -q "https://busybox.net/downloads/busybox-${BBX_VER}.tar.bz2"
rm -rf "busybox-${BBX_VER}"; tar xf "busybox-${BBX_VER}.tar.bz2"; cd "busybox-${BBX_VER}"

make ARCH=arm CROSS_COMPILE="${CROSS}" defconfig   # busybox defconfig = almost everything on

# .config edits (busybox has no scripts/config helper)
set_y()   { sed -i -E "s|^# CONFIG_$1 is not set|CONFIG_$1=y|; s|^CONFIG_$1=.*|CONFIG_$1=y|" .config; grep -q "^CONFIG_$1=y" .config || echo "CONFIG_$1=y" >> .config; }
set_n()   { sed -i -E "s|^CONFIG_$1=.*|# CONFIG_$1 is not set|" .config; }
set_str() { sed -i -E "s|^# CONFIG_$1 is not set|CONFIG_$1=\"$2\"|; s|^CONFIG_$1=.*|CONFIG_$1=\"$2\"|" .config; grep -q "^CONFIG_$1=" .config || echo "CONFIG_$1=\"$2\"" >> .config; }

set_y STATIC
set_y TELNETD; set_y FEATURE_TELNETD_STANDALONE; set_y ASH; set_y SH_IS_ASH; set_y NC
set_y WGET; set_y HTTPD; set_y FTPGET; set_y FTPPUT; set_y VI
set_n TC; set_n PAM                                   # break on modern headers / static glibc
set_str EXTRA_CFLAGS "-march=armv5te -mtune=arm926ej-s -marm -mfloat-abi=soft"

set +e +o pipefail; yes "" | make ARCH=arm CROSS_COMPILE="${CROSS}" oldconfig >/dev/null 2>&1; set -e -o pipefail
make -j"$(nproc)" ARCH=arm CROSS_COMPILE="${CROSS}" busybox

file busybox
"${CROSS}readelf" -h busybox | grep -iE 'class|machine|flags'
"${CROSS}readelf" -A busybox | grep -iE 'Tag_CPU_arch|Tag_THUMB' || true
"${CROSS}strip" busybox

# ARM926 emulation smoke test — catches the exact SIGILL class the prebuilts hit
echo "== qemu arm926 smoke =="; Q="qemu-arm -cpu arm926"
$Q ./busybox echo ok; $Q ./busybox sh -c 'echo x | cat | tr a-z A-Z'; $Q ./busybox telnetd --help 2>&1 | head -1

mkdir -p /out; cp busybox /out/busybox; cp .config /out/busybox.config
echo "OK -> /out/busybox"
