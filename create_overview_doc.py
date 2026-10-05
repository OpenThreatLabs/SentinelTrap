import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def create_document():
    doc = docx.Document()

    # Set standard margins (1 inch)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Styles & Fonts
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(33, 37, 41)

    # Colors
    c_primary = RGBColor(14, 116, 144)      # Teal / Cyan 700 (#0e7490)
    c_dark = RGBColor(15, 23, 42)          # Slate 900 (#0f172a)
    c_gray = RGBColor(100, 116, 139)       # Slate 500 (#64748b)

    def set_cell_background(cell, fill_hex):
        shading_xml = f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'
        cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))

    def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = OxmlElement('w:tcMar')
        for margin_name, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
            node = OxmlElement(f'w:{margin_name}')
            node.set(qn('w:w'), str(val))
            node.set(qn('w:type'), 'dxa')
            tcMar.append(node)
        tcPr.append(tcMar)

    # --- TITLE HEADER ---
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(4)
    run_title = title_p.add_run("SentinelTrap: Multi-Layer Adaptive Honeypot & Deception Security Platform")
    run_title.font.name = 'Calibri'
    run_title.font.size = Pt(22)
    run_title.bold = True
    run_title.font.color.rgb = c_primary

    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(18)
    run_sub = sub_p.add_run("Project Technical Overview • Abstract, Key Contributions, Challenges, Software Architecture (Why, How, When)")
    run_sub.font.name = 'Calibri'
    run_sub.font.size = Pt(11)
    run_sub.font.color.rgb = c_gray
    run_sub.italic = True

    # Divider bar
    divider_tbl = doc.add_table(rows=1, cols=1)
    divider_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    divider_tbl.autofit = False
    cell_d = divider_tbl.rows[0].cells[0]
    cell_d.width = Inches(6.5)
    set_cell_background(cell_d, "0E7490")
    p_d = cell_d.paragraphs[0]
    p_d.paragraph_format.space_before = Pt(1)
    p_d.paragraph_format.space_after = Pt(1)
    run_d = p_d.add_run("")
    run_d.font.size = Pt(2)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # Helper function for section headings
    def add_section_header(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(6)
        run = h.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(14)
        run.bold = True
        run.font.color.rgb = c_primary

    # --- 1. ABSTRACT ---
    add_section_header("1. Abstract")
    p_abs = doc.add_paragraph()
    p_abs.paragraph_format.line_spacing = 1.15
    p_abs.paragraph_format.space_after = Pt(10)
    p_abs.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run_abs = p_abs.add_run(
        "Modern enterprise networks face relentless, automated cyber reconnaissance and zero-day intrusion attempts that "
        "routinely bypass traditional perimeter defenses like static firewalls and signature-based IDSs. SentinelTrap is an "
        "active deception and threat intelligence framework that transitions defense from passive filtering to proactive engagement. "
        "The software deploys a multi-protocol decoy network across SSH, Telnet, HTTP, FTP, MySQL, Redis, and SMTP, funneling "
        "attackers into a secure, virtualized containment sandbox. SentinelTrap integrates an Adaptive Deception Engine that "
        "dynamically generates context-aware honeytokens, decoy database credentials, and fake network topologies in direct "
        "response to adversarial keystrokes. Recorded adversarial sessions are mapped to the MITRE ATT&CK framework, enriched with "
        "real-time IP geolocation and ASN metadata, and streamed via WebSockets to a Next.js Security Operations Center (SOC) "
        "dashboard. With automated AutoShun firewall rule generation and forensic PDF reporting, SentinelTrap delivers an "
        "end-to-end software defense pipeline that traps adversaries, drains their reconnaissance resources, and converts live "
        "attacks into actionable threat intelligence."
    )

    # --- 2. KEY CONTRIBUTIONS ---
    add_section_header("2. Key Contributions")

    contributions = [
        ("Multi-Protocol Decoy Surface with Zero-Leak Containment: ",
         "Emulates 9 realistic network services (SSH, Web, Telnet, FTP, MySQL, Redis, SMTP, DNS, RDP) inside an in-memory Virtual File System (VFS), allowing realistic adversary engagement without exposing real host resources."),
        ("Behavioral Adaptive Deception Engine: ",
         "Rather than serving static decoy responses, the engine parses adversarial CLI intent in real time, injecting dynamic honey-credentials, fake cluster routing tables, and deceptive error messages to prolong attacker dwell time."),
        ("Deterministic MITRE ATT&CK Mapping: ",
         "Parses raw attacker command strings and payload signatures directly into MITRE Tactics & Techniques (e.g., T1003 Credential Dumping, T1046 Network Scanning, T1059 Command-Line Interface) with 100% deterministic rule matching and zero AI hallucinations."),
        ("Real-Time SOC Visualization & 3D Threat Mapping: ",
         "Integrates a WebGL/Canvas 3D threat globe visualizing live geospatial ingress vectors alongside instant terminal session replay, live event streaming, and automated forensic PDF/STIX/CEF report generation."),
        ("Automated Incident Mitigation (AutoShun): ",
         "Generates synthesized host-level firewall rules (iptables / ufw) dynamically based on attacker risk severity scores to isolate offending nodes immediately.")
    ]

    for title, desc in contributions:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        r_title = p.add_run(title)
        r_title.bold = True
        r_title.font.color.rgb = c_dark
        r_desc = p.add_run(desc)

    # --- 3. CHALLENGES & HOW THEY WERE SOLVED ---
    add_section_header("3. Key Challenges & Technical Solutions")

    table = doc.add_table(rows=1, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    col_widths = [Inches(1.6), Inches(2.3), Inches(2.6)]

    # Header Row
    hdr_cells = table.rows[0].cells
    headers = ["Challenge Area", "Problem Description", "SentinelTrap Software Solution"]
    for i, title in enumerate(headers):
        hdr_cells[i].width = col_widths[i]
        set_cell_background(hdr_cells[i], "0E7490")
        set_cell_margins(hdr_cells[i], top=120, bottom=120, left=140, right=140)
        p = hdr_cells[i].paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(title)
        run.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
        run.font.size = Pt(10)

    challenges_data = [
        ("Sandbox Breakout & Host Escape",
         "Attackers attempting privilege escalation (sudo, rm -rf /, /bin/bash escapes) could compromise the host operating system.",
         "Built a custom in-memory Virtual File System (VFS) in Python. All filesystem interactions and file modifications occur in isolated RAM state—zero interaction with the host OS."),
        ("Deception Fingerprinting",
         "Sophisticated attackers can quickly identify static honeypots by checking command quirks or static repetitive responses.",
         "Developed the Adaptive Deception Engine, which generates dynamic responses (simulated MySQL handshakes, fake /etc/passwd accounts with canary tokens) tailored to the adversary's specific commands."),
        ("High-Volume Telemetry & Zero Latency",
         "Handling concurrent multi-protocol connection floods while maintaining real-time UI dashboard responsiveness.",
         "Implemented an asynchronous FastAPI + Uvicorn backend with WebSocket broadcasting and connection pooling, decoupling packet reception from dashboard rendering."),
        ("Cloud Deployment & Cold States",
         "Free-tier cloud hosts (Render/Vercel) sleep on inactivity and lack persistent WebSockets across multi-service setups.",
         "Decoupled architecture: Next.js frontend hosted on Vercel with smart reconnecting state & waking animations, and the Python ASGI core hosted on Render with persistent WebSockets.")
    ]

    for row_idx, (chal, prob, sol) in enumerate(challenges_data):
        row_cells = table.add_row().cells
        bg_hex = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for i, text in enumerate([chal, prob, sol]):
            row_cells[i].width = col_widths[i]
            set_cell_background(row_cells[i], bg_hex)
            set_cell_margins(row_cells[i], top=100, bottom=100, left=130, right=130)
            p = row_cells[i].paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            run = p.add_run(text)
            run.font.size = Pt(9.5)
            if i == 0:
                run.bold = True
                run.font.color.rgb = c_dark

    # --- 4. WHY, HOW, AND WHEN ---
    add_section_header("4. System Rationale: Why, How, and When")

    why_how_when = [
        ("WHY (Problem & Strategic Rationale):",
         "Traditional firewalls and intrusion detection systems (IDS) are fundamentally reactive: firewalls either drop traffic (providing zero intelligence on adversary intent) or rely on static signatures that fail against novel zero-day exploits. SentinelTrap creates an asymmetric defense advantage: any interaction with a decoy node is by definition 100% unauthorized. This yields zero false positives, drains attacker time, and safely exposes adversarial tools and reconnaissance techniques."),
        ("HOW (Technical Software Mechanism):",
         "The framework operates as a multi-tier software pipeline: (1) Lure & Intercept: Modular listener daemons bind to standard service ports (SSH, Telnet, HTTP, FTP, MySQL, Redis, SMTP). (2) Contain: Attackers are granted interactive access to a sandboxed virtual shell running in memory. (3) Deceive: The Adaptive Deception Engine injects contextual Canary honeytokens and fake database credentials to track exfiltration attempts. (4) Analyze & Mitigate: The FastAPI backend correlates sessions, computes a 0–100 Attacker Risk Score, maps MITRE ATT&CK techniques, broadcasts live telemetry via WebSockets, and generates immediate iptables/ufw mitigation rules."),
        ("WHEN (Deployment Context & Operational Triggers):",
         "SentinelTrap is deployed across three operational contexts: (1) Network Perimeter & DMZ: Placed alongside edge routers and public cloud IPs to trap external Internet botnets (Mirai, automated SSH brute-forcers, web vulnerability scanners). (2) Internal Subnets (Lateral Movement Traps): Embedded inside corporate LANs and cloud VPCs to instantly alert on malicious insiders or attackers pivoting across internal assets. (3) Incident Response & Threat Hunting: Activated whenever security teams need to isolate and analyze live adversary payloads in an air-gapped forensic decoy environment.")
    ]

    for title, desc in why_how_when:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r_t = p.add_run(title + "\n")
        r_t.bold = True
        r_t.font.color.rgb = c_dark
        r_d = p.add_run(desc)

    # --- 5. SOFTWARE SPECIFICATIONS & TECH STACK ---
    add_section_header("5. Software Specifications & Technology Stack")

    stack_items = [
        ("Backend & Telemetry Core: ", "Python 3.10+, FastAPI (ASGI), Uvicorn, SQLite / SQLAlchemy ORM"),
        ("Decoy Daemons & Sandbox: ", "Paramiko (Virtual SSH Server), Custom Asynchronous Socket Handlers (Telnet, FTP, SMTP, MySQL, Redis, DNS)"),
        ("Active Deception Engine: ", "Contextual Rule-Based Honeytoken Generator, In-Memory Virtual File System (VFS)"),
        ("Frontend & SOC Dashboard: ", "Next.js 15 (React 19, TypeScript, App Router), Tailwind CSS, Lucide Icons, Recharts Analytics"),
        ("3D Threat Visualization: ", "Cobe (WebGL Dot Sphere) + 60 FPS HTML5 Canvas Ray-Traced Trajectory Engine"),
        ("Forensics & Interoperability: ", "ReportLab (Automated PDF Incident Reports), STIX 2.1 JSON Exporter, CEF (Common Event Format) Exporter")
    ]

    for label, desc in stack_items:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(3)
        r_lbl = p.add_run(label)
        r_lbl.bold = True
        r_lbl.font.color.rgb = c_dark
        r_val = p.add_run(desc)

    # Save to disk
    out_path = r"d:\Codes\SentinelTrap\SentinelTrap_Project_Overview.docx"
    doc.save(out_path)
    print(f"Document created successfully at: {out_path}")

if __name__ == "__main__":
    create_document()
