# 🛡️ SentinelTrap: Multi-Layer Adaptive Honeypot & Deception Security Platform

> **Project Technical Overview**  
> *Abstract, Key Contributions, Challenges, Software Architecture (Why, How, When), and Technology Stack*

---

## 1. Abstract

Modern enterprise networks face relentless, automated cyber reconnaissance and zero-day intrusion attempts that routinely bypass traditional perimeter defenses like static firewalls and signature-based IDSs. **SentinelTrap** is an active deception and threat intelligence framework that transitions defense from passive filtering to proactive engagement. The software deploys a multi-protocol decoy network across **SSH, Telnet, HTTP, FTP, MySQL, Redis, and SMTP**, funneling attackers into a secure, virtualized containment sandbox. 

SentinelTrap integrates an **Adaptive Deception Engine** that dynamically generates context-aware honeytokens, decoy database credentials, and fake network topologies in direct response to adversarial keystrokes. Recorded adversarial sessions are mapped to the **MITRE ATT&CK** framework, enriched with real-time **IP geolocation and ASN metadata**, and streamed via **WebSockets** to a Next.js Security Operations Center (SOC) dashboard. With automated **AutoShun firewall rule generation** and forensic PDF reporting, SentinelTrap delivers an end-to-end software defense pipeline that traps adversaries, drains their reconnaissance resources, and converts live attacks into actionable threat intelligence.

---

## 2. Key Contributions

- **Multi-Protocol Decoy Surface with Zero-Leak Containment**: Emulates 9 realistic network services (SSH, Web, Telnet, FTP, MySQL, Redis, SMTP, DNS, RDP) inside an in-memory Virtual File System (VFS), allowing realistic adversary engagement without exposing real host resources.
- **Behavioral Adaptive Deception Engine**: Rather than serving static decoy responses, the engine parses adversarial CLI intent in real time, injecting dynamic honey-credentials, fake cluster routing tables, and deceptive error messages to prolong attacker dwell time.
- **Deterministic MITRE ATT&CK Mapping**: Parses raw attacker command strings and payload signatures directly into MITRE Tactics & Techniques (e.g., `T1003` Credential Dumping, `T1046` Network Scanning, `T1059` Command-Line Interface) with 100% deterministic rule matching and zero AI hallucinations.
- **Real-Time SOC Visualization & 3D Threat Mapping**: Integrates a WebGL/Canvas 3D threat globe visualizing live geospatial ingress vectors alongside instant terminal session replay, live event streaming, and automated forensic PDF/STIX/CEF report generation.
- **Automated Incident Mitigation (AutoShun)**: Generates synthesized host-level firewall rules (`iptables` / `ufw`) dynamically based on attacker risk severity scores to isolate offending nodes immediately.

---

## 3. Key Challenges & Technical Solutions

| Challenge Area | Problem Description | SentinelTrap Software Solution |
| :--- | :--- | :--- |
| **Sandbox Breakout & Host Escape** | Attackers attempting privilege escalation (`sudo`, `rm -rf /`, `/bin/bash` escapes) could compromise the host operating system. | Built a custom **in-memory Virtual File System (VFS)** in Python. All filesystem interactions and file modifications occur in isolated RAM state—zero interaction with the host OS. |
| **Deception Fingerprinting** | Sophisticated attackers can quickly identify static honeypots by checking command quirks or static repetitive responses. | Developed the **Adaptive Deception Engine**, which generates dynamic responses (simulated MySQL handshakes, fake `/etc/passwd` accounts with canary tokens) tailored to the adversary's specific commands. |
| **High-Volume Telemetry & Zero Latency** | Handling concurrent multi-protocol connection floods while maintaining real-time UI dashboard responsiveness. | Implemented an asynchronous **FastAPI + Uvicorn** backend with **WebSocket broadcasting** and connection pooling, decoupling packet reception from dashboard rendering. |
| **Cloud Deployment & Cold States** | Free-tier cloud hosts (Render/Vercel) sleep on inactivity and lack persistent WebSockets across multi-service setups. | Decoupled architecture: Next.js frontend hosted on **Vercel** with smart reconnecting state & waking animations, and the Python ASGI core hosted on **Render** with persistent WebSockets. |

---

## 4. System Rationale: Why, How, and When

```
   ┌────────────────────────────────────────────────────────────────────────┐
   │                                  WHY?                                  │
   │  Traditional firewalls and antivirus only alert AFTER a breach or rely │
   │  on static signatures. SentinelTrap traps attackers BEFORE they touch  │
   │  real data, wasting attacker resources and gathering early intel.     │
   └───────────────────────────────────┬────────────────────────────────────┘
                                       │
                                       ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │                                  HOW?                                  │
   │  Software-based active deception: Multi-port listeners capture packets │
   │  into a virtual sandbox; an adaptive engine injects deceptive outputs; │
   │  telemetry is normalized to MITRE ATT&CK and streamed to a Next.js SOC.│
   └───────────────────────────────────┬────────────────────────────────────┘
                                       │
                                       ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │                                  WHEN?                                 │
   │  Deployed at the network perimeter (DMZ), internal subnet traps, cloud │
   │  VPCs, and IoT gateways to detect lateral movement and external scans. │
   └────────────────────────────────────────────────────────────────────────┘
```

### • WHY (Problem & Strategic Rationale)
Traditional firewalls and intrusion detection systems (IDS) are fundamentally reactive: firewalls either drop traffic (providing zero intelligence on adversary intent) or rely on static signatures that fail against novel zero-day exploits. SentinelTrap creates an asymmetric defense advantage: any interaction with a decoy node is by definition 100% unauthorized. This yields zero false positives, drains attacker time, and safely exposes adversarial tools and reconnaissance techniques.

### • HOW (Technical Software Mechanism)
The framework operates as a 4-tier software pipeline:
1. **Lure & Intercept**: Modular listener daemons bind to standard service ports (SSH `2222`, Telnet `2223`, HTTP `8080`, FTP `2121`, MySQL `3306`, Redis `6379`, SMTP `2525`).
2. **Contain**: Attackers are granted interactive access to a sandboxed virtual shell running in memory (`honeypot/shell.py`).
3. **Deceive**: The Adaptive Deception Engine injects contextual Canary honeytokens and fake database credentials to track exfiltration attempts.
4. **Analyze & Mitigate**: The FastAPI backend correlates sessions, computes a 0–100 Attacker Risk Score, maps MITRE ATT&CK techniques, broadcasts live telemetry via WebSockets, and generates immediate `iptables`/`ufw` mitigation rules.

### • WHEN (Deployment Context & Operational Triggers)
SentinelTrap is deployed across three primary operational scenarios:
1. **Network Perimeter & DMZ**: Placed alongside edge routers and public cloud IPs to trap external Internet botnets (Mirai, automated SSH brute-forcers, web vulnerability scanners).
2. **Internal Subnets (Lateral Movement Traps)**: Embedded inside corporate LANs and cloud VPCs to instantly alert on malicious insiders or attackers pivoting across internal assets.
3. **Incident Response & Threat Hunting**: Activated whenever security teams need to isolate and analyze live adversary payloads in an air-gapped forensic decoy environment.

---

## 5. Software Specifications & Technology Stack

- **Backend & Telemetry Core**: Python 3.10+, FastAPI (ASGI), Uvicorn, SQLite / SQLAlchemy ORM
- **Decoy Daemons & Sandbox**: Paramiko (Virtual SSH Server), Custom Asynchronous Socket Handlers (Telnet, FTP, SMTP, MySQL, Redis, DNS)
- **Active Deception Engine**: Contextual Rule-Based Honeytoken Generator, In-Memory Virtual File System (VFS)
- **Frontend & SOC Dashboard**: Next.js 15 (React 19, TypeScript, App Router), Tailwind CSS, Lucide Icons, Recharts Analytics
- **3D Threat Visualization**: Cobe (WebGL Dot Sphere) + 60 FPS HTML5 Canvas Ray-Traced Trajectory Engine
- **Forensics & Interoperability**: ReportLab (Automated PDF Incident Reports), STIX 2.1 JSON Exporter, CEF (Common Event Format) Exporter
