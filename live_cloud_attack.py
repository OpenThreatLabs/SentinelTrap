import sys
import time
import requests

BACKEND_URL = "https://sentineltrap-nz03.onrender.com"

def run_live_attack():
    print("=" * 60)
    print("🛡️  SENTINELTRAP CLOUD ATTACK INJECTOR")
    print(f"Targeting: {BACKEND_URL}")
    print("Open your hosted Vercel dashboard to watch real-time updates!")
    print("=" * 60)

    # 1. Register new adversary session from an external IP
    attacker_ip = "185.220.101.5"  # Typical Tor Exit Node / Scanner IP
    username = "admin"
    password = "password123"

    print(f"\n[+] Step 1: Connecting to honeypot as '{username}' from {attacker_ip}...")
    try:
        r = requests.post(
            f"{BACKEND_URL}/api/sessions",
            json={
                "ip_address": attacker_ip,
                "username_attempted": username,
                "password_attempted": password,
                "protocol": "SSH"
            },
            timeout=10
        )
        if r.status_code != 200:
            print(f"[-] Failed to create session: {r.status_code} {r.text}")
            return
        session_id = r.json().get("session_id")
        print(f"[✓] Session Registered! Session ID: {session_id}")
        print(">>> Look at your hosted Vercel dashboard! A new active session just appeared.")
    except Exception as e:
        print(f"[-] Connection error: {e}")
        return

    # Real-time commands to inject sequentially
    commands = [
        ("command", "whoami", "root"),
        ("command", "uname -a", "Linux ubuntu-srv-01 5.15.0-52-generic x86_64"),
        ("command", "cat /etc/passwd", "root:x:0:0:root:/root:/bin/bash\ndb_admin:x:1001:1001:Database Service:/home/db_admin:/bin/bash"),
        ("canary_tripped", "cat /var/backups/credentials.txt", "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\nAWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"),
        ("deception_tripped", "mysql -h localhost -u root -p", "ERROR 1045 (28000): Access denied for user 'root'@'localhost' (using password: NO)"),
        ("command", "sudo rm -rf / --no-preserve-root", "rm: cannot remove '/proc': Operation not permitted"),
    ]

    print("\n[+] Step 2: Injecting real-time attacker commands...")
    for ev_type, cmd, out in commands:
        print(f"\n[Attacker Command] > {cmd}")
        time.sleep(2)  # Delay so evaluators see live streaming keystrokes
        try:
            r = requests.post(
                f"{BACKEND_URL}/api/sessions/{session_id}/events",
                json={
                    "event_type": ev_type,
                    "protocol": "SSH",
                    "input_data": cmd,
                    "output_data": out
                },
                timeout=10
            )
            if r.status_code == 200:
                print(f"[✓] Streamed to cloud dashboard! Event: {ev_type}")
            else:
                print(f"[-] Failed: {r.status_code}")
        except Exception as e:
            print(f"[-] Event injection error: {e}")

    # 3. Close the session
    print("\n[+] Step 3: Attacker disconnecting...")
    time.sleep(2)
    try:
        requests.patch(f"{BACKEND_URL}/api/sessions/{session_id}", timeout=10)
        print("[✓] Session terminated! Status set to Closed on dashboard.")
    except Exception as e:
        print(f"[-] Disconnect error: {e}")

    print("\n" + "=" * 60)
    print("🎉 Live attack demonstration completed successfully!")
    print("Now click on the session in your hosted Vercel UI to show:")
    print(" 1. Keystroke / Terminal Replay")
    print(" 2. Auto-generated PDF Forensic Incident Report")
    print(" 3. MITRE ATT&CK Technique Mapping")
    print("=" * 60)

if __name__ == "__main__":
    run_live_attack()
