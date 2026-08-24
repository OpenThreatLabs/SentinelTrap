import io
import datetime
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

import models
from geolocate import IPThreatIntelligenceService
from analytics import ThreatAnalyticsEngine

class IncidentReportGenerator:
    """
    Automated PDF Incident Report Generator
    Compiles detailed forensic reports for individual attacker sessions,
    including IP Geolocation, Risk Score, Threat Classification, and Command Timeline.
    """

    @staticmethod
    def generate_pdf_report(session_id: str, db: Session) -> io.BytesIO:
        session = db.query(models.SessionModel).filter(models.SessionModel.id == session_id).first()
        if not session:
            raise ValueError(f"Session '{session_id}' not found")

        events = db.query(models.EventModel).filter(models.EventModel.session_id == session_id).order_by(models.EventModel.timestamp.asc()).all()

        # Gather Geolocation and Risk Analytics
        geo_intel = IPThreatIntelligenceService.lookup_ip(session.ip_address)
        risk_score, classification, indicators = ThreatAnalyticsEngine.calculate_risk_score(events)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            textColor=colors.HexColor('#0f172a'),
            fontSize=22,
            leading=26,
            spaceAfter=15
        )

        h2_style = ParagraphStyle(
            'H2Style',
            parent=styles['Heading2'],
            textColor=colors.HexColor('#1e293b'),
            fontSize=14,
            leading=18,
            spaceBefore=12,
            spaceAfter=8
        )

        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['BodyText'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#334155')
        )

        story.append(Paragraph("🛡️ SentinelTrap Incident Forensics Report", title_style))
        story.append(Paragraph(f"<b>Session Reference ID:</b> {session.id}", body_style))
        story.append(Paragraph(f"<b>Attacker IP Address:</b> {session.ip_address} ({geo_intel.get('city')}, {geo_intel.get('country')})", body_style))
        story.append(Paragraph(f"<b>ISP / ASN Metadata:</b> {geo_intel.get('isp')} | {geo_intel.get('asn')}", body_style))
        story.append(Paragraph(f"<b>Target Credentials Tried:</b> {session.username_attempted} / {session.password_attempted or 'N/A'}", body_style))
        story.append(Paragraph(f"<b>Session Started:</b> {session.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}", body_style))
        if session.ended_at:
            story.append(Paragraph(f"<b>Session Terminated:</b> {session.ended_at.strftime('%Y-%m-%d %H:%M:%S UTC')}", body_style))

        story.append(Spacer(1, 10))

        # Threat Classification & Risk Box
        story.append(Paragraph("Threat Risk Evaluation", h2_style))
        story.append(Paragraph(f"<b>Calculated Risk Score:</b> <font color='#e11d48'><b>{risk_score} / 100</b></font>", body_style))
        story.append(Paragraph(f"<b>Threat Classification:</b> <b>{classification}</b>", body_style))
        if indicators:
            story.append(Paragraph(f"<b>Threat Indicators:</b> {', '.join(indicators)}", body_style))

        story.append(Spacer(1, 15))

        # Captured Activity Timeline
        story.append(Paragraph("Chronological Attack Activity Timeline", h2_style))

        table_data = [["Time (UTC)", "Event Type", "Command / Input Executed"]]
        for event in events:
            time_str = event.timestamp.strftime('%H:%M:%S')
            detail_text = event.input_data if event.input_data else (event.output_data or "")
            if len(detail_text) > 85:
                detail_text = detail_text[:85] + "..."
            table_data.append([time_str, event.event_type, detail_text])

        if len(table_data) == 1:
            table_data.append(["-", "No Events", "No command activity captured during this connection."])

        t = Table(table_data, colWidths=[65, 125, 350])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))

        story.append(t)
        doc.build(story)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_summary_pdf_report(db: Session) -> io.BytesIO:
        """
        Generates an executive SOC Threat Intelligence Executive Summary PDF report
        covering all captured attacker sessions, adversary origins, and MITRE techniques.
        """
        sessions = db.query(models.SessionModel).order_by(models.SessionModel.started_at.desc()).all()
        events = db.query(models.EventModel).order_by(models.EventModel.timestamp.desc()).limit(150).all()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            textColor=colors.HexColor('#0f172a'),
            fontSize=20,
            leading=24,
            spaceAfter=10
        )

        h2_style = ParagraphStyle(
            'H2Style',
            parent=styles['Heading2'],
            textColor=colors.HexColor('#1e293b'),
            fontSize=13,
            leading=16,
            spaceBefore=10,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['BodyText'],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#334155')
        )

        story.append(Paragraph("🛡️ SentinelTrap SOC Threat Intelligence Executive Summary", title_style))
        story.append(Paragraph(f"<b>Report Generated:</b> {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", body_style))
        story.append(Paragraph(f"<b>Total Adversary Ingress Sessions:</b> {len(sessions)} | <b>Total Telemetry Events Logged:</b> {len(events)}", body_style))
        story.append(Paragraph("<b>Supervising Node:</b> SentinelTrap Multi-Layer Honeypot Mesh (VIT Bhopal)", body_style))

        story.append(Spacer(1, 10))

        # Attacker Sessions Table
        story.append(Paragraph("Adversary Ingress Sessions & Target Analysis", h2_style))
        session_table_data = [["Origin IP", "Geolocation", "Protocol", "Attempted User", "Started Time"]]

        for s in sessions[:15]:
            session_table_data.append([
                s.ip_address,
                f"{s.city}, {s.country}",
                s.protocol or "SSH",
                s.username_attempted or "root",
                s.started_at.strftime('%m-%d %H:%M')
            ])

        if len(session_table_data) == 1:
            session_table_data.append(["-", "-", "-", "-", "No active sessions recorded yet."])

        st = Table(session_table_data, colWidths=[90, 130, 60, 110, 150])
        st.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        story.append(st)

        story.append(Spacer(1, 12))

        # Recent Attack Events Table
        story.append(Paragraph("Recent Adversarial Telemetry & Deception Triggers", h2_style))
        event_table_data = [["Timestamp", "Event Classification", "Command / Ingress Payload"]]

        for ev in events[:20]:
            time_str = ev.timestamp.strftime('%H:%M:%S')
            detail = ev.input_data if ev.input_data else (ev.output_data or "")
            if len(detail) > 75:
                detail = detail[:75] + "..."
            event_table_data.append([time_str, ev.event_type, detail])

        if len(event_table_data) == 1:
            event_table_data.append(["-", "-", "No forensic events captured."])

        et = Table(event_table_data, colWidths=[70, 140, 330])
        et.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        story.append(et)

        doc.build(story)
        buffer.seek(0)
        return buffer
