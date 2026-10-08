# Findings — Anyka AK3918AV130 / YYOS (TuyaOS 6.3.0)

## Hardware / boot
- SoC Anyka AK3918AV130_B, ARM926EJ-S (ARMv5TEJ), 64MB DDR2, Linux 4.4.302.
- Flash: 8MiB SPI NOR. `mtdparts=spi-nor:256K(uboot),1536K(kernel),1344K(rootfs squashfs),4672K(appfs squashfs),256K(config jffs2),128K(factory)`.
- U-Boot 2019.10. Console **password-locked** (`### Please input uboot password: ###`)
  and has **secure-boot/sig-verify** (`Signature FAILED!`, `bootsecure`, `fit-images`).
  `env_platform=anycloud_ak3918av130`. No CH341A => treat u-boot (mtd0) as untouchable.
- `/config` (mtd4, jffs2) and the SD are the only persistent writable spots from Linux.
  `flashcp` is on-box; `/dev/mtd0..5` are root-writable (don't write mtd0).

## Boot chain (how the SD root works)
- `init.sh` reads `/mnt/sdcard/yy_debug.ini` -> `mode` (normal/debug/factory) + `start_sh`.
  `mode=debug` + `start_sh=/mnt/sdcard/hack.sh` -> init runs hack.sh (not start.sh).
- `init.sh` reboots the box if `mode` changes between reads — expect a reboot after editing.
- `/appfs/script/start.sh`: `[ -f /mnt/sdcard/yy_telnet_start ] && /mnt/sdcard/telnetd &`.
- `yy_cam` (the one big app: Tuya cloud + video pipeline + ONVIF + RTSP + PTZ) starts only
  if `nvram get STATUS == active`.

## Network services
| port | proto | what |
|---|---|---|
| 6668 | tcp | Tuya LAN protocol (local control, always on) |
| 7000 | udp | Tuya P2P/media |
| 8554 | tcp | RTSP (after enable) — `rtsp://IP:8554/stream0` (H264+G711), `/stream1` |
| 5000 | tcp | ONVIF (after enable) — `/onvif/device_service`, `admin` / empty pass |
| 3702 | udp | ONVIF WS-Discovery |
- Only `yy_cam` makes outbound/internet connections (Tuya cloud, MQTT 8886). Nothing else.

## Enable RTSP + ONVIF
- Master switch = **Tuya DP 237** (bool). Setting it true makes yy_cam write
  `/config/param.conf` `[rtsp] rtsp_on_off=1` + `[onvif] onvif_on_off=1` (persists).
- ONVIF PTZ is a **non-working stub** here (GetNodes/GetConfigurations empty, moves fault).
  Use the Tuya PTZ DPs instead.

## Tuya DP map (dpid -> handler, confirmed from firmware log `yy_cloud_tuya_dp.cpp`)
- 101 basic_indicator · 103 basic_flip · 104 basic_osd · 105 basic_nightvision
- 106 motion_sensitivity · 108 night_mode · 134 motion_switch · 140 decibel_sensitivity
- 150 record_switch · 151 record_mode · 160 ? · 188 anti_flicker_mode
- **119 ptz_control** (enum "0".."7": 0=up,1=up-right,2=right,3=down-right,4=down,5=down-left,6=left,7=up-left)
- **116 ptz_stop** · 132 ptz_calibration · 141 ptz home/recalibrate
- zoom_control / zoom_stop · memory_point_add/del/set + preset_point_set (presets)
- siren_onoff / audible_alarm_onoff / siren_volume / speaker_volume (canned sounds only)
- **237 = ONVIF+RTSP master switch** · onvif_switch / onvif_change_pwd / onvif_ip_addr
- DANGER DPs (don't poke blind): `format_sd_card`, `device_restart`, 111/115 (sd).
- To map any DP yourself: set it over Tuya LAN and watch the UART log — yy_cam prints
  `dpid = N` then `yy_cloud_tuya_dp_response_<name>`.

## Local-only (no cloud, no internet)
- No iptables/netfilter userspace, but `/sbin/ip` exists. Blackhole both /1 halves:
  `ip route add blackhole 0.0.0.0/1 ; ip route add blackhole 128.0.0.0/1`.
  LAN /24 stays; routes survive DHCP renew; reversible with `del`. See tools/local_only.sh.

## Audio
- Mic -> stream audio is G711/PCMU (track1 in the RTSP SDP). Listening works.
- Speaker `/dev/pcmC0D0p` driven by Anyka `ak_ao_*` inside yy_cam, **exclusive**
  (parallel open = EPERM). No ALSA/aplay. `talk` is Tuya-P2P only, not a DP.
- => **full-duplex two-way audio is not reachable** on stock fw via standard means.
  Siren/alarm WAVs (`/appfs/resource/audio/*.wav`, PCM mono 8kHz 16-bit) are played by
  `ty_dsp_audio_play_wav`; bind-mounting a custom WAV + triggering the siren DP is the
  only local HA->speaker path (announce/TTS, not duplex).

## Alt firmware
- OpenIPC/Thingino **do not** support AK3918 (no installable build; Thingino is Ingenic-only).
- Only community AK3918 project: `github.com/piotr-go/GNCC_GC2_ak3918ev300_RTSP`
  (vendor-SDK build, RTSP only; mic/ONVIF/PTZ unsolved). Anyka media SDK is closed.
- Combined with the locked+secure-boot u-boot and no SPI programmer: not worth the brick risk.
