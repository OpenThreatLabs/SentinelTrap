#!/usr/bin/env python3
"""
SentinelTrap - Multi-Layer Honeypot Framework
Unified Master Launcher Script

Launches the complete SentinelTrap architecture:
1. FastAPI Backend API & WebSockets (Port 8000)
2. Interactive SSH Honeypot (Port 2222)
3. Web Admin & REST API Honeypot (Ports 8080 & 8081)
4. IoT Telnet Honeypot (Port 2323)
5. FTP & SMTP Honeypot (Ports 2121 & 2525)
6. Fake Open Ports Nmap Scan Trap Engine
"""

import os
import sys
import time
import subprocess
import signal

processes = []

def start_service(name, cmd_list):
    print(f"[*] Starting {name}...")
    p = subprocess.Popen(cmd_list, cwd=os.path.dirname(__file__) or ".")
    processes.append((name, p))
    time.sleep(1)

def cleanup(signum=None, frame=None):
    print("\n[*] Shutting down SentinelTrap multi-layer services...")
    for name, p in processes:
        try:
            print(f"[-] Stopping {name} (PID {p.pid})...")
            p.terminate()
        except Exception:
            pass
    sys.exit(0)

def main():
    print("============================================================")
    print("      SentinelTrap - Multi-Layer Honeypot Framework         ")
    print("                  Master System Launcher                    ")
    print("============================================================")

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # 1. Backend API
    start_service("FastAPI Backend API (Port 8000)", [sys.executable, "backend/main.py"])

    # 2. SSH Honeypot
    start_service("SSH Honeypot (Port 2222)", [sys.executable, "honeypot/server.py"])

    # 3. Web & API Honeypot
    start_service("Web & REST API Honeypot (Ports 8080 & 8081)", [sys.executable, "honeypot/web_honeypot.py"])

    # 4. IoT Telnet Honeypot
    start_service("IoT Telnet Honeypot (Port 2323)", [sys.executable, "honeypot/telnet_honeypot.py"])

    # 5. FTP & SMTP Honeypot
    start_service("FTP & SMTP Honeypot (Ports 2121 & 2525)", [sys.executable, "honeypot/ftp_smtp_honeypot.py"])

    # 6. Fake Open Ports Engine
    start_service("Fake Open Ports Engine (Nmap Trap)", [sys.executable, "honeypot/fake_ports.py"])

    print("\n[+] All SentinelTrap services launched successfully!")
    print("[+] Press CTRL+C to terminate all services gracefully.")
    print("------------------------------------------------------------\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()

if __name__ == '__main__':
    main()
