import json
import uuid
import re
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

    # Stable namespace UUID for deterministic UUIDv5 generation (OpenThreatLabs SentinelTrap)
    _NS = uuid.UUID("4d8f1e29-87a1-4321-9876-000000000001")

    @classmethod
    def _stix_id(cls, stix_type: str, seed: str) -> str:
        """Generate a deterministic UUIDv5-based STIX 2.1 compliant object ID."""
        return f"{stix_type}--{uuid.uuid5(cls._NS, seed)}"

    @staticmethod
    def _cef_escape(value: str) -> str:
        """Escape special characters in CEF extension field values per the ArcSight CEF spec."""
        if not value:
            return ""
        # Escape backslash first, then pipe, equals, and newlines
        value = value.replace("\\", "\\\\")
        value = value.replace("|", "\\|")
        value = value.replace("=", "\\=")
        value = value.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
        return value

    @classmethod
    def export_stix21_format(cls, db: Session) -> dict:
        """Exports captured threat telemetry as a STIX 2.1 JSON Bundle."""
        sessions = db.query(models.SessionModel).all()
        stix_objects = []

        # STIX Identity Object (OpenThreatLabs) — fixed deterministic ID
        stix_objects.append({
            "type": "identity",
            "spec_version": "2.1",
            "id": cls._stix_id("identity", "OpenThreatLabs-SentinelTrap"),
            "created": "2026-08-15T00:00:00.000Z",
            "modified": "2026-08-15T00:00:00.000Z",
            "name": "OpenThreatLabs SentinelTrap Honeypot Framework",
            "identity_class": "system"
        })

        for s in sessions:
            # Use deterministic UUIDv5 IDs derived from session ID to guarantee STIX compliance
            indicator_id = cls._stix_id("indicator", f"indicator-{s.id}")
            observed_id = cls._stix_id("observed-data", f"observed-{s.id}")

            start_ts = (s.started_at or datetime.utcnow()).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            end_ts = (s.ended_at or s.started_at or datetime.utcnow()).strftime("%Y-%m-%dT%H:%M:%S.000Z")

            # STIX Indicator Object for Attacker IP
            stix_objects.append({
                "type": "indicator",
                "spec_version": "2.1",
                "id": indicator_id,
                "created": start_ts,
                "modified": start_ts,
                "name": f"Honeypot Attacker IP: {s.ip_address}",
                "pattern": f"[ipv4-addr:value = '{s.ip_address}']",
                "pattern_type": "stix",
                "valid_from": start_ts
            })

            # STIX Observed-Data Object
            stix_objects.append({
                "type": "observed-data",
                "spec_version": "2.1",
                "id": observed_id,
                "created": start_ts,
                "modified": start_ts,
                "first_observed": start_ts,
                "last_observed": end_ts,
                "number_observed": 1,
                "objects": {
                    "0": {
                        "type": "ipv4-addr",
                        "value": s.ip_address
                    }
                }
            })

        # Bundle ID is deterministic per export run — always a valid UUIDv5
        bundle_id = cls._stix_id("bundle", "sentineltrap-export-bundle")
        return {
            "type": "bundle",
            "id": bundle_id,
            "objects": stix_objects
        }

    @classmethod
    def export_cef_format(cls, db: Session) -> str:
        """Exports events in Common Event Format (CEF) Syslog standard."""
        # Pre-fetch all sessions to eliminate N+1 queries
        sessions = db.query(models.SessionModel).all()
        session_map = {s.id: s for s in sessions}

        events = db.query(models.EventModel).all()
        cef_lines = []

        for e in events:
            session = session_map.get(e.session_id)
            ip = session.ip_address if session else "127.0.0.1"

            # CEF header fields must also escape pipe characters
            safe_event_type = (e.event_type or "unknown").replace("|", "\\|")

            # Format CEF Header: CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension
            cef_header = f"CEF:0|OpenThreatLabs|SentinelTrap|1.0|{safe_event_type}|Honeypot Command Event|6|"

            # CEF extension values must have special chars escaped
            msg_val = cls._cef_escape(e.input_data or "")
            cs1_val = cls._cef_escape(e.output_data or "")
            extension = f"src={ip} msg={msg_val} cs1={cs1_val} cs1Label=Response"
            cef_lines.append(cef_header + extension)

        return "\n".join(cef_lines)
