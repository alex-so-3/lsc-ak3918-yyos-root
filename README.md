# LSC / Anyka AK3918 "YYOS" (TuyaOS) — SD-card root

Root an Anyka **AK3918AV130** YYOS/TuyaOS camera with **only an SD card**.
No CH341A, no soldering, no case opening, no UART needed for the root itself.

You get: root telnet over LAN, a working static BusyBox (telnetd/nc/wget/httpd),
local **RTSP + ONVIF**, **PTZ over Tuya LAN**, and a **kill-switch for all cloud/WAN**.

<img src="img/lsc-3225722.png" alt="LSC Smart Connect Smart Rotatable Camera 2K" width="420">

**Tested on:** LSC Smart Connect *Smart Rotatable Camera 2K* (dual-band WiFi) —
Action art. no. **LSC 3225722**. SoC Anyka AK3918AV130_B, YYOS = TuyaOS 6.3.0,
Linux 4.4.302 (ARM926EJ-S / ARMv5TEJ), BusyBox rootfs, SPI-NOR boot.
Other AK3918 YYOS cams very likely behave the same.

## TL;DR

```
# 1. FAT32 SD card
# 2. copy the repo's sdcard/ files to the card root:
cp sdcard/yy_debug.ini sdcard/hack.sh sdcard/telnetd  /Volumes/SDCARD/
# 3. build a compatible static busybox (see busybox/) and drop it on the card:
cp busybox/out/busybox /Volumes/SDCARD/busybox
# 4. arm the telnet autostart:
touch /Volumes/SDCARD/yy_telnet_start
# 5. insert, power on, wait ~40s:
telnet <CAMERA_IP>        # login: root / root
```

## Mechanism

YYOS `init.sh` reads `/mnt/sdcard/yy_debug.ini` on every boot:

```
mode=debug
start_sh=/mnt/sdcard/hack.sh
```

`mode=debug` makes init run **your** `hack.sh` instead of the normal boot script.
`hack.sh`:
- bind-mounts a tmpfs `/etc/shadow` with a known root password (**root/root**),
- starts `busybox telnetd`,
- (optional) backs up all flash partitions to the SD,
- (optional) blocks all WAN egress (local-only mode),
- hands off to `/appfs/script/start.sh` so the camera still works normally.

Independently, `/appfs/script/start.sh` runs `/mnt/sdcard/telnetd` if
`/mnt/sdcard/yy_telnet_start` exists — so telnet comes up two ways.

## BusyBox (the one real gotcha)

Stock BusyBox has **no telnetd**. Prebuilt `busybox-armv5l`/`armv4l` binaries
**SIGILL** on ARM926EJ-S (they use Thumb-2 / OABI the core doesn't implement).

**Shortcut:** grab the prebuilt static binary from
[Releases](../../releases/tag/busybox-v1.36.1) (`busybox-1.36.1-ak3918-armv5te-static`,
sha256 `367d142bf8d25751e4d8c63442ee99779865a10e2073a28b28795510a3091290`) and skip to step 4.

Or build a **static EABI5, ARM-mode, ARMv5TE** binary yourself:

```
cd busybox
docker build -t bbx .
docker run --rm -v "$PWD/out:/out" bbx
file out/busybox        # ELF 32-bit ARM, EABI5, statically linked
# flags baked in: -march=armv5te -mtune=arm926ej-s -marm -mfloat-abi=soft + CONFIG_STATIC
```

FAT can't store the +x bit but YYOS mounts the card `0777`, so it runs as-is.

## After root

- **Shell:** `telnet <IP>` (root/root), or UART `root/root` @115200 8N1.
- **RTSP + ONVIF:** Tuya LAN **DP 237 = true** (`tools/enable_rtsp_onvif.py`), or set
  `/config/param.conf` `[rtsp] rtsp_on_off=1` + `[onvif] onvif_on_off=1` and restart `yy_cam`.
  - RTSP: `rtsp://<IP>:8554/stream0` (H264 + G711), `/stream1` = 2nd profile, no auth.
  - ONVIF: `http://<IP>:5000/onvif/device_service`, user `admin`, **empty** password.
- **PTZ:** Tuya LAN **DP 119** (direction `"0"`–`"7"`) + **DP 116** (stop). `tools/ptz.py`.
  (ONVIF PTZ is a non-working stub on this firmware — use the DP.)
- **Local-only (cut cloud/WAN, keep LAN):** `tools/local_only.sh`, or the block in
  `hack.sh` toggled by `/mnt/sdcard/yy_local_only`.

See `docs/FINDINGS.md` for the full Tuya DP map, ports, and internals.

## Revert / recovery

- Pull the SD card, or set `mode=normal` in `yy_debug.ini` → stock behavior returns.
- `hack.sh` dumps all MTD partitions to `/mnt/sdcard/flash_backup/` on boot — keep them.
- **Do NOT write `mtd0` (u-boot):** console is password-locked + secure-boot is present;
  with no SPI programmer a bad u-boot/kernel write is an unrecoverable brick.

## Disclaimer

For devices you own. Telnet here is root with weak/no auth — keep it on a trusted LAN,
never port-forward it. No warranty; you can brick hardware.
