#!/usr/bin/env python3
# Turn on the built-in RTSP + ONVIF servers via Tuya LAN (DP 237 = master switch).
# Persists: yy_cam writes /config/param.conf [rtsp]rtsp_on_off=1 + [onvif]onvif_on_off=1.
# Opens: RTSP :8554 (rtsp://IP:8554/stream0), ONVIF :5000 (admin / empty), WS-Discovery udp :3702.
#   pip install tinytuya ; export TUYA_ID=... TUYA_KEY=... CAM_HOST=192.168.1.x
#   ./enable_rtsp_onvif.py        # enable
#   ./enable_rtsp_onvif.py off    # disable
import os, sys, time, tinytuya
ID=os.environ.get("TUYA_ID","YOUR_DEVICE_ID"); KEY=os.environ.get("TUYA_KEY","YOUR_LOCAL_KEY")
HOST=os.environ.get("CAM_HOST","192.168.1.50"); VER=float(os.environ.get("TUYA_VER","3.5"))
if ID.startswith("YOUR_") or KEY.startswith("YOUR_"): sys.exit("set TUYA_ID / TUYA_KEY")
on = not (len(sys.argv)>1 and sys.argv[1]=="off")
d=tinytuya.Device(ID,HOST,KEY,version=VER); d.set_socketTimeout(5)
print("set 237 ->", on, ":", d.set_value(237, on)); time.sleep(3)
print("dp237 now:", d.status().get("dps",{}).get("237"))
print("RTSP:  rtsp://%s:8554/stream0   ONVIF: http://%s:5000  (admin / empty)" % (HOST,HOST) if on else "disabled")
