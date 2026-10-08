#!/usr/bin/env python3
# Run a shell command over the camera's root telnet (no deps).
# telnetd -l /bin/sh gives a PTY that echoes input, so we bracket output with a
# split marker that can't appear verbatim in the echoed command line.
#   CAM_HOST=192.168.1.x ./tsh.py 'uname -a; netstat -ltn'
import socket, sys, os, time
HOST = os.environ.get("CAM_HOST", "192.168.1.50")
PORT = int(os.environ.get("CAM_PORT", "23"))

def _iac(d):
    out=bytearray(); rep=bytearray(); i=0
    while i < len(d):
        if d[i]==255 and i+2 < len(d):
            c,o=d[i+1],d[i+2]
            rep += bytes([255, {253:252,251:254,254:252,252:254}.get(c,252), o]); i+=3; continue
        out.append(d[i]); i+=1
    return bytes(out), bytes(rep)

def run(s, cmd, timeout):
    tag=str(int(time.time()*1000)%1000000); a,b=f"ZS{tag}SZ",f"ZE{tag}EZ"
    s.sendall(f'echo Z""S{tag}SZ; {cmd}; echo Z""E{tag}EZ$?\n'.encode())
    buf=bytearray(); end=time.time()+timeout; s.settimeout(0.5)
    while time.time()<end:
        try: d=s.recv(4096)
        except socket.timeout: d=b""
        if d:
            o,r=_iac(d); buf+=o
            if r: s.sendall(r)
            if b.encode() in buf: break
    t=buf.decode("utf-8","replace"); i,j=t.find(a),t.find(b)
    if i!=-1 and j!=-1 and j>i:
        body=t[i+len(a):j].lstrip("\r\n"); rc="".join(ch for ch in t[j+len(b):j+len(b)+4] if ch.isdigit())
        return body.rstrip("\r\n"), rc or "?"
    return None,"?"

def main():
    if len(sys.argv)<2: print("usage: CAM_HOST=ip tsh.py 'command' [timeout]"); return 2
    s=socket.create_connection((HOST,PORT),6); s.settimeout(1.0)
    end=time.time()+3
    while time.time()<end:
        try: d=s.recv(4096)
        except socket.timeout: break
        if d:
            _,r=_iac(d)
            if r: s.sendall(r)
    body,rc=run(s, sys.argv[1], float(sys.argv[2]) if len(sys.argv)>2 else 15.0)
    try: s.sendall(b"exit\n")
    except OSError: pass
    s.close()
    if body is None: print("[no marker captured]"); return 1
    print(body); print(f"[rc={rc}]"); return 0

if __name__=="__main__": sys.exit(main())
