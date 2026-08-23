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

    # 1. Backend API (FastAPI & WebSockets on Port 8000)
    start_service("FastAPI Backend & Telemetry Stream (Port 8000)", [sys.executable, "backend/main.py"])

    # 2. Multi-Protocol Deception Suite (9 Decoy Traps: SSH, Telnet, HTTP, FTP, SMTP, MySQL, Redis, DNS, RDP)
    start_service("9 Multi-Protocol Decoy Services (Honeypot Suite)", [sys.executable, "honeypot/runner.py"])

    print("\n[+] All SentinelTrap services (Backend + 9 Decoys) launched successfully!")
    print("[+] SOC Dashboard available at: http://localhost:3000")
    print("[+] REST API available at: http://localhost:8000")
    print("[+] Press CTRL+C to terminate all services gracefully.")
    print("------------------------------------------------------------\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()

if __name__ == '__main__':
    main()
