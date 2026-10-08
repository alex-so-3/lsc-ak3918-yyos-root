#!/usr/bin/env python3
# PTZ over Tuya LAN (ONVIF PTZ is a non-working stub on this firmware).
#   pip install tinytuya
#   get device id + local key:  python -m tinytuya wizard   (or LAN scan: python -m tinytuya scan)
#   export TUYA_ID=...  TUYA_KEY=...  CAM_HOST=192.168.1.x
#   ./ptz.py left        ./ptz.py stop       ./ptz.py move 2 0.8
#
# DP 119 = ptz_control (enum "0".."7", 8 directions). DP 116 = ptz_stop.
# DP 132 = calibration, DP 141 = home. zoom via zoom_control/zoom_stop DPs.
import os, sys, time, tinytuya

ID   = os.environ.get("TUYA_ID",  "YOUR_DEVICE_ID")
KEY  = os.environ.get("TUYA_KEY", "YOUR_LOCAL_KEY")
HOST = os.environ.get("CAM_HOST", "192.168.1.50")
VER  = float(os.environ.get("TUYA_VER", "3.5"))

DIR = {"up":"0","upright":"1","right":"2","downright":"3",
       "down":"4","downleft":"5","left":"6","upleft":"7"}

def dev():
    d = tinytuya.Device(ID, HOST, KEY, version=VER); d.set_socketTimeout(5); return d

def main():
    if ID.startswith("YOUR_") or KEY.startswith("YOUR_"):
        print("set TUYA_ID / TUYA_KEY (see header)"); return 2
    a = sys.argv[1] if len(sys.argv) > 1 else "stop"
    d = dev()
    if a == "stop":
        print(d.set_value(116, "1")); return 0
    if a == "move":                      # ./ptz.py move <0-7> <seconds>
        v = sys.argv[2]; secs = float(sys.argv[3]) if len(sys.argv) > 3 else 0.6
        d.set_value(119, v); time.sleep(secs); d.set_value(116, "1"); return 0
    if a in DIR:                         # named direction, brief nudge
        d.set_value(119, DIR[a]); time.sleep(0.6); d.set_value(116, "1"); return 0
    if a == "calibrate": print(d.set_value(132, "1")); return 0
    if a == "home":      print(d.set_value(141, "1")); return 0
    print("usage: ptz.py up|down|left|right|upleft|...|stop|home|calibrate | move <0-7> <sec>")
    return 2

if __name__ == "__main__": sys.exit(main())
