#!/usr/bin/env python3
# UART root-shell helper (fallback if you don't have network yet, or to watch boot).
# 115200 8N1 on the camera's TX/RX pads. On macOS the CH9102/CH340 needs the
# IOSSIOSPEED ioctl (pyserial often mis-sets the baud) -> raw fd here.
# Auto-logs in root/root. Firmware spams the console; markers tolerate it.
#   CAM_PORT=/dev/cu.usbserial-XXXX ./serial_console.py 'uname -a'
#   CAM_PORT=/dev/ttyUSB0           ./serial_console.py 'cat /proc/mtd'   # Linux
import os, sys, time, termios, tty, fcntl, struct, select
PORT = os.environ.get("CAM_PORT", "/dev/ttyUSB0")
BAUD = int(os.environ.get("CAM_BAUD", "115200"))

def open_port():
    fd=os.open(PORT, os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK); tty.setraw(fd)
    a=termios.tcgetattr(fd)
    a[2]|=(termios.CLOCAL|termios.CREAD|termios.CS8); a[2]&=~(termios.PARENB|termios.CSTOPB|termios.CSIZE); a[2]|=termios.CS8
    termios.tcsetattr(fd, termios.TCSANOW, a)
    # macOS IOSSIOSPEED: _IOW('T',2,speed_t) — try 8-byte (64-bit) then 4-byte.
    for const,pk in ((0x80085402,struct.pack("Q",BAUD)),(0x80045402,struct.pack("I",BAUD))):
        try: fcntl.ioctl(fd,const,pk); break
        except OSError: pass
    try: termios.tcflush(fd, termios.TCIOFLUSH)
    except OSError: pass
    return fd

def w(fd,b):
    b=b.encode() if isinstance(b,str) else b; n=0
    while n<len(b):
        _,ww,_=select.select([],[fd],[],2.0)
        if ww: n+=os.write(fd,b[n:n+256])

def read_until(fd, toks, t):
    if isinstance(toks,str): toks=[toks]
    buf=bytearray(); end=time.time()+t
    while time.time()<end:
        r,_,_=select.select([fd],[],[],0.1)
        if r:
            try: c=os.read(fd,4096)
            except OSError: c=b""
            if c:
                buf.extend(c)
                if any(x in buf.decode("utf-8","replace") for x in toks): break
    return buf.decode("utf-8","replace")

def ensure_shell(fd):
    for _ in range(5):
        w(fd,"\x03\r")                       # Ctrl-C (kill stuck reader) + newline; never Ctrl-D (logs out)
        t=read_until(fd,["login:","#","Password:"],3.0)
        if "#" in t and "login:" not in t.rsplit("#",1)[-1]: return True
        if "login:" in t: w(fd,"root\r"); t=read_until(fd,["Password:","#"],4.0)
        if "Password:" in t: w(fd,"root\r");
        if "#" in read_until(fd,["#","login:"],6.0): return True
        time.sleep(0.4)
    return False

def cmd(fd, c, t=15.0):
    tag=str(int(time.time()*1000)%1000000); a,b=f"ZS{tag}SZ",f"ZE{tag}EZ"
    termios.tcflush(fd, termios.TCIFLUSH)
    w(fd, f'\recho Z""S{tag}SZ; {c}; echo Z""E{tag}EZ$?\r')
    txt=read_until(fd,[b],t); i,j=txt.find(a),txt.find(b)
    if i!=-1 and j!=-1 and j>i: return txt[i+len(a):j].lstrip("\r\n").rstrip("\r\n")
    return None

if __name__=="__main__":
    if len(sys.argv)<2: print("usage: CAM_PORT=/dev/ttyUSB0 serial_console.py 'command'"); sys.exit(2)
    fd=open_port()
    try:
        if not ensure_shell(fd): print("no shell prompt"); sys.exit(2)
        out=cmd(fd, sys.argv[1], float(sys.argv[2]) if len(sys.argv)>2 else 15.0)
        print(out if out is not None else "[no marker captured]")
    finally: os.close(fd)
