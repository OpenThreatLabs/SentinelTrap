import json
from datetime import datetime
from sqlalchemy.orm import Session
import models

class ThreatTelemetryExporter:
    """
    Threat Intelligence SIEM & STIX 2.1 Exporter
    Converts captured honeypot telemetry into STIX 2.1 Threat Objects and
    CEF (Common Event Format) Syslog streams for integration with SIEM platforms
    (Splunk, Microsoft Sentinel, Elastic SIEM).
    """

    @staticmethod
    def export_stix21_format(db: Session) -> dict:
        """Exports captured threat telemetry as a STIX 2.1 JSON Bundle."""
        sessions = db.query(models.SessionModel).all()
        stix_objects = []

        # STIX Identity Object (OpenThreatLabs)
        stix_objects.append({
            "type": "identity",
            "spec_version": "2.1",
            "id": "identity--4d8f1e29-87a1-4321-9876-000000000001",
            "created": "2026-08-15T00:00:00.000Z",
            "modified": "2026-08-15T00:00:00.000Z",
            "name": "OpenThreatLabs SentinelTrap Honeypot Framework",
            "identity_class": "system"
        })

        for s in sessions:
            # STIX Indicator Object for Attacker IP
            indicator_id = f"indicator--{s.id}"
            stix_objects.append({
                "type": "indicator",
                "spec_version": "2.1",
                "id": indicator_id,
                "created": s.started_at.isoformat() + "Z",
                "modified": s.started_at.isoformat() + "Z",
                "name": f"Honeypot Attacker IP: {s.ip_address}",
                "pattern": f"[ipv4-addr:value = '{s.ip_address}']",
                "pattern_type": "stix",
                "valid_from": s.started_at.isoformat() + "Z"
            })

            # STIX Observed-Data Object
            stix_objects.append({
                "type": "observed-data",
                "spec_version": "2.1",
                "id": f"observed-data--{s.id}",
                "created": s.started_at.isoformat() + "Z",
                "modified": s.started_at.isoformat() + "Z",
                "first_observed": s.started_at.isoformat() + "Z",
                "last_observed": (s.ended_at or s.started_at).isoformat() + "Z",
                "number_observed": 1,
                "objects": {
                    "0": {
                        "type": "ipv4-addr",
                        "value": s.ip_address
                    }
                }
            })

        return {
            "type": "bundle",
            "id": f"bundle--stix-export-2026",
            "objects": stix_objects
        }

    @staticmethod
    def export_cef_format(db: Session) -> str:
        """Exports events in Common Event Format (CEF) Syslog standard."""
        events = db.query(models.EventModel).all()
        cef_lines = []

        for e in events:
            session = db.query(models.SessionModel).filter(models.SessionModel.id == e.session_id).first()
            ip = session.ip_address if session else "127.0.0.1"
            
            # Format CEF Header: CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension
            cef_header = f"CEF:0|OpenThreatLabs|SentinelTrap|1.0|{e.event_type}|Honeypot Command Event|6|"
            extension = f"src={ip} msg={e.input_data or ''} cs1={e.output_data or ''} cs1Label=Response"
            cef_lines.append(cef_header + extension)

        return "\n".join(cef_lines)
