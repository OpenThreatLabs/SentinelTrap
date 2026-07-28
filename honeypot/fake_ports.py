#!/usr/bin/env python3
"""
SentinelTrap - Fake Open Ports & Nmap Scanner Trap Engine
Binds to 15+ simulated open ports to trap Nmap & Masscan network probes.
Returns realistic software banners and reports port scanning telemetry in real time.
"""

import os
import sys
import socket
import threading
import datetime
import json
import uuid
import urllib.request

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/api/events")

# Port Banners Mapping for Network Reconnaissance Traps
PORT_BANNERS = {
    21: b"220 ProFTPD 1.3.5 Server (Acme Gateway) [::ffff:127.0.0.1]\r\n",
    22: b"SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.1\r\n",
    23: b"\r\nAcme Router OS v4.2\r\nlogin: ",
    25: b"220 mail.acmegroup-prod.com ESMTP Postfix (Ubuntu)\r\n",
    80: b"HTTP/1.1 200 OK\r\nServer: Apache/2.4.52 (Ubuntu)\r\n\r\n<html><body><h1>Acme Gateway</h1></body></html>",
    110: b"+OK POP3 server ready <1048.12026@acmegroup-prod.com>\r\n",
    143: b"* OK [CAPABILITY IMAP4rev1 LITERAL+] IMAP4rev1 Server Ready\r\n",
    3306: b"\x4a\x00\x00\x00\x0a\x35\x2e\x37\x2e\x33\x38\x00\x0d\x00\x00\x00\x67\x71\x64\x73\x64\x70\x7a\x00\xff\xf7\x08\x02\x00\x7f\x80\x15\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x62\x72\x79\x76\x64\x72\x61\x78\x00\x6d\x79\x73\x71\x6c\x5f\x6e\x61\x74\x69\x76\x65\x5f\x70\x61\x73\x73\x77\x6f\x72\x64\x00",
    3389: b"\x03\x00\x00\x13\x0e\xd0\x00\x00\x12\x34\x00\x02\x09\x08\x00\x00\x00\x00\x00",
    5432: b"E\x00\x00\x00\x50SFATAL\x00C28000\x00Mno pg_hba.conf entry for host\x00",
    5900: b"RFB 003.008\n",
    6379: b"-ERR unknown command\r\n",
    8080: b"HTTP/1.1 200 OK\r\nServer: nginx/1.18.0 (Ubuntu)\r\n\r\n"
}

def report_telemetry(event_data):
    timestamp = datetime.datetime.utcnow().isoformat()
    log_entry = {"timestamp": timestamp, **event_data}
    print(f"[{event_data.get('event_type', 'PORT_SCAN')}] {json.dumps(log_entry)}")
    try:
        req = urllib.request.Request(
            BACKEND_URL,
            data=json.dumps(log_entry).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            pass
    except Exception:
        pass


def handle_scan_connection(client_sock, client_ip, port):
    session_id = str(uuid.uuid4())
    print(f"[!] [Nmap Trap] Probe on Port {port} from {client_ip}")
    report_telemetry({
        "session_id": session_id,
        "ip_address": client_ip,
        "protocol": f"PORT_{port}",
        "event_type": "nmap_port_scan",
        "input_data": f"Port scan probe on port {port}",
        "vulnerability_code": "NMAP_RECON"
    })
    
    try:
        banner = PORT_BANNERS.get(port, b"220 Service Ready\r\n")
        client_sock.sendall(banner)
    except Exception:
        pass
    finally:
        client_sock.close()


def listen_on_port(port):
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_sock.bind(('0.0.0.0', port))
        server_sock.listen(20)
        print(f"[*] [Fake Port Listener] Active on Port {port}")
    except Exception:
        # Port might be in use by main honeypot service or system
        return

    while True:
        try:
            client_sock, client_addr = server_sock.accept()
            t = threading.Thread(target=handle_scan_connection, args=(client_sock, client_addr[0], port), daemon=True)
            t.start()
        except Exception:
            break


def main():
    print("============================================================")
    print("      SentinelTrap - Fake Open Ports & Nmap Scan Trap       ")
    print("============================================================")
    print(f"[*] Monitoring ports: {list(PORT_BANNERS.keys())}")
    print("--------------------------------================------------")

    threads = []
    for port in PORT_BANNERS.keys():
        t = threading.Thread(target=listen_on_port, args=(port,), daemon=True)
        t.start()
        threads.append(t)

    try:
        while True:
            for t in threads:
                t.join(timeout=1.0)
    except KeyboardInterrupt:
        print("\n[*] Shutting down Fake Open Ports engine...")
        sys.exit(0)

if __name__ == '__main__':
    main()
