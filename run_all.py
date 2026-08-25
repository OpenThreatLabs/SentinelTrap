#!/usr/bin/env python3
"""
SentinelTrap - Multi-Layer Honeypot Framework
Unified Master Launcher Script

Launches the complete SentinelTrap architecture:
1. FastAPI Backend API & WebSockets (Port 8000)
2. Multi-Protocol Honeypot Suite (9 Decoy Services)
3. Next.js SOC Dashboard (Port 3000)
"""

import os
import sys
import time
import subprocess
import signal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
processes = []


def start_service(name, cmd_list, cwd=BASE_DIR):
    print(f"[*] Starting {name}...")
    p = subprocess.Popen(cmd_list, cwd=cwd)
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
    start_service(
        "FastAPI Backend & Telemetry Stream (Port 8000)",
        [sys.executable, "main.py"],
        os.path.join(BASE_DIR, "backend")
    )

    # 2. Multi-Protocol Deception Suite (9 Decoy Traps)
    start_service(
        "9 Multi-Protocol Decoy Services (Honeypot Suite)",
        [sys.executable, "runner.py"],
        os.path.join(BASE_DIR, "honeypot")
    )

    # 3. Next.js SOC Dashboard (Port 3000)
    start_service(
        "Next.js SOC Dashboard (Port 3000)",
        ["npm.cmd", "run", "dev"],
        os.path.join(BASE_DIR, "frontend")
    )

    print("\n[+] All SentinelTrap services launched successfully!")
    print("[+] SOC Dashboard: http://localhost:3000")
    print("[+] REST API:      http://localhost:8000")
    print("[+] Press CTRL+C to terminate all services gracefully.")
    print("------------------------------------------------------------\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()


if __name__ == '__main__':
    main()