import os
import requests

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

class SecurityAlertDispatcher:
    """
    Automated Security Alert & Webhook Notification Dispatcher
    Sends real-time high-priority alerts to Slack, Discord, or SIEM webhooks
    when critical events occur (Risk Score > 75, Honeytoken Exfiltration, DB Dump).
    """

    @staticmethod
    def dispatch_slack_notification(title: str, message: str, risk_score: int = 0):
        if not SLACK_WEBHOOK_URL:
            return

        color = "#e11d48" if risk_score >= 75 else "#f59e0b"
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"🚨 SentinelTrap Alert: {title}",
                    "text": message,
                    "fields": [
                        {"title": "Risk Score", "value": f"{risk_score}/100", "short": True},
                        {"title": "Framework", "value": "OpenThreatLabs SentinelTrap", "short": True}
                    ]
                }
            ]
        }
        try:
            requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=3)
        except Exception as e:
            print(f"[-] Slack alert dispatch failed: {e}")

    @staticmethod
    def dispatch_discord_notification(title: str, message: str, risk_score: int = 0):
        if not DISCORD_WEBHOOK_URL:
            return

        embed = {
            "title": f"🛡️ SentinelTrap Incident: {title}",
            "description": message,
            "color": 14749256 if risk_score >= 75 else 16107531,
            "fields": [
                {"name": "Risk Score", "value": f"{risk_score}/100", "inline": True},
                {"name": "Organization", "value": "OpenThreatLabs", "inline": True}
            ]
        }
        try:
            requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]}, timeout=3)
        except Exception as e:
            print(f"[-] Discord alert dispatch failed: {e}")

    @classmethod
    def evaluate_and_dispatch(cls, ip_address: str, event_type: str, details: str, risk_score: int):
        if risk_score >= 70 or event_type in ["honeytoken_compromised", "database_access_attempt"]:
            title = f"High-Severity Threat Detected ({event_type})"
            message = f"**Attacker IP:** `{ip_address}`\n**Event:** {event_type}\n**Details:** {details}"
            
            print(f"[!] Dispatching Security Webhook Alert for IP={ip_address} | Risk={risk_score}")
            cls.dispatch_slack_notification(title, message, risk_score)
            cls.dispatch_discord_notification(title, message, risk_score)
