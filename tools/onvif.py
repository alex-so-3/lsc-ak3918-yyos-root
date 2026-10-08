#!/usr/bin/env python3
# Minimal ONVIF client (WS-UsernameToken / PasswordDigest). Default creds admin / "".
#   CAM_HOST=192.168.1.x ./onvif.py                      # GetDeviceInformation + GetStreamUri
import socket, sys, os, hashlib, base64, datetime, urllib.request, urllib.error, re
IP   = os.environ.get("CAM_HOST", "192.168.1.50")
PORT = int(os.environ.get("ONVIF_PORT", "5000"))
USER = os.environ.get("ONVIF_USER", "admin")
PASS = os.environ.get("ONVIF_PASS", "")
BASE = f"http://{IP}:{PORT}/onvif"

def wsse(u,p):
    n=os.urandom(16); c=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    dig=base64.b64encode(hashlib.sha1(n+c.encode()+p.encode()).digest()).decode()
    return (f'<wsse:Security s:mustUnderstand="1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">'
            f'<wsse:UsernameToken><wsse:Username>{u}</wsse:Username>'
            f'<wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordDigest">{dig}</wsse:Password>'
            f'<wsse:Nonce EncodingType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary">{base64.b64encode(n).decode()}</wsse:Nonce>'
            f'<wsu:Created>{c}</wsu:Created></wsse:UsernameToken></wsse:Security>')

def call(svc, body, auth=True, timeout=8):
    url=f"{BASE}/{svc}"
    hdr=wsse(USER,PASS) if auth else ""
    env=(f'<?xml version="1.0"?><s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">'
         f'<s:Header>{hdr}</s:Header><s:Body>{body}</s:Body></s:Envelope>')
    req=urllib.request.Request(url, env.encode(), {"Content-Type":"application/soap+xml; charset=utf-8"})
    try: return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8","replace")
    except urllib.error.HTTPError as e: return e.read().decode("utf-8","replace")
    except Exception as e: return f"ERR {e}"

if __name__=="__main__":
    r=call("device_service", '<GetDeviceInformation xmlns="http://www.onvif.org/ver10/device/wsdl"/>')
    print("auth:", "FAIL (NotAuthorized)" if "NotAuthorized" in r else "OK")
    r=call("media_service", '<GetProfiles xmlns="http://www.onvif.org/ver10/media/wsdl"/>')
    print("profiles:", re.findall(r'token="([^"]+)"', r)[:4], "codecs:", re.findall(r'<tt:Encoding>(\w+)</tt:Encoding>', r))
    t=(re.findall(r'token="([^"]+)"', r) or ["PROFILE_0"])[0]
    r=call("media_service", f'<GetStreamUri xmlns="http://www.onvif.org/ver10/media/wsdl"><StreamSetup xmlns="http://www.onvif.org/ver10/media/wsdl"><Stream xmlns="http://www.onvif.org/ver10/schema">RTP-Unicast</Stream><Transport xmlns="http://www.onvif.org/ver10/schema"><Protocol>RTSP</Protocol></Transport></StreamSetup><ProfileToken>{t}</ProfileToken></GetStreamUri>')
    print("stream uri:", re.findall(r"<tt:Uri>(.*?)</tt:Uri>", r))
