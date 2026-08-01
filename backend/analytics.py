import re
from sqlalchemy.orm import Session
import models

class ThreatAnalyticsEngine:
    """
    Threat Analytics Engine
    Analyzes captured attacker sessions, calculates dynamic Threat Risk Scores (0-100),
    and classifies attacker profiles (e.g., Botnet Scanner, Credential Harvester, DB Exploit Vector).
    """

    @staticmethod
    def calculate_risk_score(events: list) -> tuple[int, str, list]:
        """
        Computes risk score and threat classification based on event patterns.
        Returns: (risk_score: int, classification: str, indicators: list[str])
        """
        score = 10  # Base connection score
        indicators = []
        classifications = set()

        for event in events:
            cmd = (event.input_data or "").lower().strip()

            # Rule 1: Credential / Password Searching
            if re.search(r'(passwd|shadow|id_rsa|pass|credentials)', cmd):
                score += 30
                indicators.append("Credential Harvesting Attempt")
                classifications.add("Credential Harvester")

            # Rule 2: Database Exploitation Probes
            if re.search(r'(mysql|psql|mongo|sqlite|dump|sql)', cmd):
                score += 25
                indicators.append("Database Reconnaissance Probe")
                classifications.add("DB Exploit Vector")

            # Rule 3: Network Scanning & Recon
            if re.search(r'(nmap|ifconfig|ip a|netstat|route|arp)', cmd):
                score += 20
                indicators.append("Network Topology Discovery")
                classifications.add("Reconnaissance Probe")

            # Rule 4: System File Inspection
            if re.search(r'(cat|ls|whoami|pwd|id|uname)', cmd):
                score += 5
                indicators.append("System Environment Enumeration")

        # Cap risk score at 100
        final_score = min(score, 100)

        # Primary classification determination
        if "Credential Harvester" in classifications:
            primary_class = "Credential Harvester"
        elif "DB Exploit Vector" in classifications:
            primary_class = "DB Exploit Vector"
        elif "Reconnaissance Probe" in classifications:
            primary_class = "Reconnaissance Probe"
        elif final_score <= 20:
            primary_class = "Automated Botnet Scanner"
        else:
            primary_class = "Generic Reconnaissance Probe"

        return final_score, primary_class, list(set(indicators))

    @classmethod
    def get_ip_threat_profile(cls, ip_address: str, db: Session) -> dict:
        """
        Generates a comprehensive Threat Profile report for a specific attacker IP.
        """
        sessions = db.query(models.SessionModel).filter(models.SessionModel.ip_address == ip_address).all()
        if not sessions:
            return {"ip_address": ip_address, "status": "No historical activity recorded"}

        session_ids = [s.id for s in sessions]
        events = db.query(models.EventModel).filter(models.EventModel.session_id.in_(session_ids)).all()

        risk_score, classification, indicators = cls.calculate_risk_score(events)

        return {
            "ip_address": ip_address,
            "total_sessions": len(sessions),
            "total_commands_executed": len(events),
            "risk_score": risk_score,
            "threat_classification": classification,
            "threat_indicators": indicators,
            "country": sessions[0].country if sessions else "Unknown",
            "first_seen": sessions[-1].started_at.isoformat() if sessions else None,
            "last_seen": sessions[0].started_at.isoformat() if sessions else None
        }
