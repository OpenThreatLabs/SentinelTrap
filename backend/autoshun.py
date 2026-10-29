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
        sessions_by_ip = {}
        for s in sessions:
            sessions_by_ip.setdefault(s.ip_address, []).append(s)

        # Batch query all events in a single query
        all_events = db.query(models.EventModel).all()
        events_by_session = {}
        for ev in all_events:
            events_by_session.setdefault(ev.session_id, []).append(ev)

        shunned_ips = []
        iptables_commands = []
        ufw_commands = []
        decoy_redirect_commands = []

        for ip_address, ip_sessions in sessions_by_ip.items():
            all_sessions_for_ip = ip_sessions
            primary_session = all_sessions_for_ip[0]
            ip_events = []
            seen_sigs = set()

            # Aggregate and deduplicate events across ALL sessions from this IP (in_(all_session_ids) batch)
            for sess in all_sessions_for_ip:
                for ev in events_by_session.get(sess.id, []):
                    sig = (ev.event_type, ev.input_data, ev.timestamp)
                    if sig not in seen_sigs:
                        seen_sigs.add(sig)
                        ip_events.append(ev)

            risk_score, classification, indicators = ThreatAnalyticsEngine.calculate_risk_score(ip_events)

            if risk_score >= risk_threshold:
                shunned_ips.append({
                    "ip_address": ip_address,
                    "risk_score": risk_score,
                    "classification": classification,
                    "country": primary_session.country
                })
                # iptables drop rule
                iptables_commands.append(f"iptables -A INPUT -s {ip_address} -j DROP")
                # ufw deny rule
                ufw_commands.append(f"ufw deny from {ip_address} to any")
                # Decoy container NAT redirect rule (Redirect to Honeypot Sandbox IP 10.0.4.18)
                decoy_redirect_commands.append(
                    f"iptables -t nat -A PREROUTING -s {ip_address} -p tcp --dport 22 -j DNAT --to-destination 10.0.4.18:2222"
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
