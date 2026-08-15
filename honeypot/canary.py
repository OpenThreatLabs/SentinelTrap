import os
import uuid
import hashlib
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

class HoneytokenManager:
    """
    Honeytoken & Canary Key Generator/Validator
    Deploys decoy API keys, AWS credentials, and database tokens into honeypot environments.
    If an attacker attempts to use or exfiltrate a registered honeytoken, this module flags
    a high-severity alert.
    """

    def __init__(self):
        self.deployed_honeytokens = {}

    def generate_aws_honeykey(self) -> dict:
        """Generates a realistic decoy AWS Access Key Pair."""
        access_key = f"AKIA{uuid.uuid4().hex[:16].upper()}"
        secret_key = hashlib.sha256(access_key.encode()).hexdigest()[:40]
        
        self.deployed_honeytokens[access_key] = {
            "type": "AWS_Access_Key",
            "secret": secret_key,
            "description": "Honeytoken placed in /etc/cloud/secrets.env"
        }
        return {"access_key": access_key, "secret_key": secret_key}

    def generate_jwt_honeytoken(self) -> str:
        """Generates a decoy JWT Authorization bearer token."""
        token = f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.{uuid.uuid4().hex}.honey_sig_prod"
        self.deployed_honeytokens[token] = {
            "type": "JWT_Bearer_Token",
            "description": "Honeytoken placed in web application headers"
        }
        return token

    def check_and_alert(self, candidate_token: str, attacker_ip: str = "Unknown") -> bool:
        """
        Checks if a string contains a registered honeytoken.
        If matched, posts an alert to the Threat Intelligence Backend.
        """
        for token, meta in self.deployed_honeytokens.items():
            if token in candidate_token:
                print(f"[!] CRITICAL: Honeytoken Compromised! IP={attacker_ip} | Type={meta['type']}")
                
                # Register alert with FastAPI backend
                try:
                    r = requests.post(
                        f"{BACKEND_URL}/api/sessions",
                        json={
                            "ip_address": attacker_ip,
                            "username_attempted": f"honeytoken_{meta['type']}",
                            "password_attempted": token[:30]
                        },
                        timeout=2
                    )
                    if r.status_code == 200:
                        session_id = r.json().get("session_id")
                        requests.post(
                            f"{BACKEND_URL}/api/sessions/{session_id}/events",
                            json={
                                "event_type": "honeytoken_compromised",
                                "input_data": f"Token Triggered: {token[:25]}...",
                                "output_data": f"High-Severity Alert: {meta['description']}"
                            },
                            timeout=2
                        )
                except Exception as e:
                    print(f"[-] Honeytoken alert registration failed: {e}")
                
                return True
        return False
