import time
import requests
import random

BACKEND_URL = "http://localhost:8000"

ATTACKER_IPS = [
    "185.220.101.5",  # Known Tor Exit Node (Germany)
    "193.142.146.210", # Known Botnet Scanner (Russia)
    "103.251.140.8",   # Brute-force Probe (China)
    "45.83.223.12"     # Web Exploit Scanner (Netherlands)
]

ATTACK_COMMANDS = [
    ("whoami", "ls -la"),
    ("cat /etc/passwd", "grep password /etc/shadow"),
    ("mysql -h 10.0.4.18 -u root -p", "SELECT * FROM users;"),
    ("nmap -sS -p 1-1000 192.168.1.1", "ifconfig eth0"),
    ("cat /etc/cloud/secrets.env", "curl http://10.0.4.18/api/keys")
]

class LiveExhibitionSimulator:
    """
    SentinelTrap Live Exhibition Simulator
    Simulates real-time multi-protocol cyber attacks for live judge demonstrations.
    Triggers dynamic risk scoring, honeytoken exfiltration alerts, and live dashboard telemetry.
    """

    @staticmethod
    def run_live_demo():
        print("==========================================================================")
        print("🚀 SENTINELTRAP LIVE EXHIBITION DEMONSTRATION SIMULATOR (OpenThreatLabs)")
        print("==========================================================================")
        print("[*] Target Backend:", BACKEND_URL)
        print("[*] Simulating live incoming cyber attack sessions across decoy nodes...\n")

        for i in range(1, 4):
            ip = random.choice(ATTACKER_IPS)
            user = f"admin_probe_{random.randint(10,99)}"
            print(f"[🔥 ATTACK {i}/3] Incoming Session from Attacker IP: {ip} | User: {user}")

            # 1. Register Session
            try:
                r = requests.post(f"{BACKEND_URL}/api/sessions", json={
                    "ip_address": ip,
                    "username_attempted": user,
                    "password_attempted": "Spring2026!Admin"
                }, timeout=3)
                session_id = r.json().get("session_id")
                print(f"   └── Session Registered ID: {session_id}")
            except Exception as e:
                print(f"   └── [!] Backend connection failed: {e}. Is backend running on localhost:8000?")
                continue

            time.sleep(1)

            # 2. Simulate Command Executions & Deception Triggers
            cmds = random.choice(ATTACK_COMMANDS)
            for cmd in cmds:
                print(f"   └── Attacker Executed Command: '{cmd}'")
                try:
                    requests.post(f"{BACKEND_URL}/api/sessions/{session_id}/events", json={
                        "event_type": "command_execution",
                        "input_data": cmd,
                        "output_data": "Adaptive Deception Engine Honey Response Triggered"
                    }, timeout=2)
                except Exception:
                    pass
                time.sleep(1)

            # 3. Fetch Enriched Threat Profile & Risk Score
            try:
                profile = requests.get(f"{BACKEND_URL}/api/threat-intel/ip/{ip}", timeout=2).json()
                print(f"   └── 📊 Threat Intelligence Score: {profile.get('risk_score')}/100 | Profile: {profile.get('threat_classification')}")
                print(f"   └── 🌍 Geolocation: {profile.get('city')}, {profile.get('country')} (ISP: {profile.get('isp')})")
            except Exception:
                pass

            # 4. End Session
            try:
                requests.patch(f"{BACKEND_URL}/api/sessions/{session_id}", timeout=2)
            except Exception:
                pass

            print("--------------------------------------------------------------------------\n")
            time.sleep(1.5)

        print("==========================================================================")
        print("✅ EXHIBITION DEMO SIMULATION COMPLETE")
        print("👉 Access Live Dashboard at: http://localhost:3000")
        print("👉 Access OpenAPI Specs at: http://localhost:8000/docs")
        print("👉 Download Forensic PDF Report: http://localhost:8000/api/reports/pdf/<session_id>")
        print("==========================================================================")

if __name__ == '__main__':
    LiveExhibitionSimulator.run_live_demo()
