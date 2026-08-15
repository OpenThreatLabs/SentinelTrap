import datetime
from sqlalchemy.orm import Session
import models
from analytics import ThreatAnalyticsEngine

class AutoShunFirewallEngine:
    """
    Automated IP Auto-Shun & Decoy Firewall Engine
    Evaluates attacker risk scores and automatically generates Linux netfilter (iptables / nftables / UFW)
    firewall rules and decoy redirection commands to mitigate high-severity threats.
    """

    @staticmethod
    def generate_firewall_rules(db: Session, risk_threshold: int = 75) -> dict:
        """
        Scans all recorded sessions, identifies IPs exceeding the risk threshold,
        and produces executable firewall rule commands.
        """
        sessions = db.query(models.SessionModel).all()
        shunned_ips = []
        iptables_commands = []
        ufw_commands = []
        decoy_redirect_commands = []

        seen_ips = set()
        for s in sessions:
            if s.ip_address in seen_ips:
                continue
            seen_ips.add(s.ip_address)

            events = db.query(models.EventModel).filter(models.EventModel.session_id == s.id).all()
            risk_score, classification, indicators = ThreatAnalyticsEngine.calculate_risk_score(events)

            if risk_score >= risk_threshold:
                shunned_ips.append({
                    "ip_address": s.ip_address,
                    "risk_score": risk_score,
                    "classification": classification,
                    "country": s.country
                })
                # iptables drop rule
                iptables_commands.append(f"iptables -A INPUT -s {s.ip_address} -j DROP")
                # ufw deny rule
                ufw_commands.append(f"ufw deny from {s.ip_address} to any")
                # Decoy container NAT redirect rule (Redirect to Honeypot Sandbox IP 10.0.4.18)
                decoy_redirect_commands.append(
                    f"iptables -t nat -A PREROUTING -s {s.ip_address} -p tcp --dport 22 -j DNAT --to-destination 10.0.4.18:2222"
                )

        return {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "threshold_applied": risk_threshold,
            "total_shunned_ips": len(shunned_ips),
            "shunned_targets": shunned_ips,
            "rule_scripts": {
                "iptables": "\n".join(iptables_commands),
                "ufw": "\n".join(ufw_commands),
                "decoy_redirect_nat": "\n".join(decoy_redirect_commands)
            }
        }
