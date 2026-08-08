<div align="center">

# 🛡️ SentinelTrap
### Multi-Layer Adaptive Honeypot & Cyber Attack Analysis Framework

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.140-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14%2F15-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

<p align="center">
  <b>Active Deception • Real-Time Attack Monitoring • Threat Geolocation • Automated Incident Reporting</b>
</p>

---

</div>

## 📌 Executive Summary

**SentinelTrap** is an advanced, multi-layer honeypot and active deception platform designed to lure unauthorized adversaries into controlled decoy environments. Unlike passive firewalls, SentinelTrap actively engages attackers across multiple protocols (**SSH**, **Telnet**, **HTTP Web Trap**, **FTP**) and deploys an **Adaptive Deception Engine** that dynamically generates honey-credentials, decoy database connection errors, and fake network routing tables based on real-time attacker commands.

---

## 🔥 Core Key Features

- **🌐 Multi-Protocol Decoy Suite**:
  - **SSH Honeypot (`Port 2222`)**: Custom Paramiko SSH server capturing raw credentials and bash keystrokes.
  - **Telnet Honeypot (`Port 2223`)**: Traps IoT botnet probes (e.g., Mirai botnets) and credential brute-forcing.
  - **HTTP Web Trap (`Port 8080`)**: Captures web scanners, SQL injection payloads, and path traversal probes (`/.env`, `/admin`).
  - **FTP Honeypot (`Port 2121`)**: Traps anonymous FTP logins, directory scans, and malicious payload uploads.

- **🎭 Adaptive Deception Engine**:
  - **Credential Trap**: Dynamically injects fake user accounts and honey API keys when commands like `cat /etc/passwd` or `grep password` are executed.
  - **Database Decoy**: Intercepts `mysql`, `psql`, or `mongo` commands to display fake cluster alerts and security warnings.
  - **Network Reconnaissance Trap**: Intercepts `nmap`, `ifconfig`, or `netstat` to expose dummy internal IP addresses (`10.0.4.18`).

- **📊 Threat Intelligence & Risk Scoring**:
  - **Attacker Risk Score (0–100)**: Evaluates command severity to compute real-time risk scores.
  - **Threat Classification**: Classifies attackers into profiles (*Botnet Scanner*, *Credential Harvester*, *DB Exploit Vector*, *Reconnaissance Probe*).
  - **IP Geolocation Enrichment**: Resolves IP addresses to geographical coordinates, country, city, ISP name, ASN, and proxy flags with LRU caching.

- **📄 Automated Reporting & Log Exporting**:
  - Direct PDF incident report generation via ReportLab.
  - Instant attack log exports in structured **CSV** and **JSON** formats.

---

## 🏗️ System Architecture

```
                                  [ ATTACKER / SCANNER ]
                                             │
      ┌──────────────────────┬───────────────┴───────────────┬──────────────────────┐
      │                      │                               │                      │
      ▼                      ▼                               ▼                      ▼
┌─────────────┐        ┌─────────────┐                 ┌─────────────┐        ┌─────────────┐
│ SSH Server  │        │   Telnet    │                 │  HTTP Web   │        │ FTP Server  │
│ (Port 2222) │        │ (Port 2223) │                 │ Trap (8080) │        │ (Port 2121) │
└──────┬──────┘        └──────┬──────┘                 └──────┬──────┘        └──────┬──────┘
       │                      │                               │                      │
       └──────────────────────┴───────────────┬───────────────┴──────────────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │  Virtual Shell Runner   │
                                 └────────────┬────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │ Adaptive Deception Engine│
                                 └────────────┬────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │ FastAPI Threat Backend  │
                                 │  - IP Geolocation & ASN │
                                 │  - Threat Risk Scoring  │
                                 │  - Real-Time WebSockets │
                                 └────────────┬────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │ Next.js Dashboard UI    │
                                 └─────────────────────────┘
```

---

## 👥 Team Work Allocation & Responsibilities

| Priority | Team Member | Primary Role | Key Responsibilities & Submodules |
| :---: | :--- | :--- | :--- |
| 🥇 **1** | **Abhinav Mishra** | **Project Lead & Core Architect** | Overall Framework Architecture, Adaptive Deception Engine (`deception.py`), FastAPI Threat Backend (`main.py`, `analytics.py`, `geolocate.py`), System Integration & Docker Orchestration |
| 🥈 **2** | **Jaiyansh Dhaulakhandi** | **Senior Backend & Honeypot Engineer** | Multi-Protocol Honeypot Nodes: SSH Server (`server.py`), Telnet Server (`telnet_server.py`), HTTP Web Trap (`web_trap.py`), FTP Server (`ftp_server.py`), and Virtual Shell Runner (`shell.py`) |
| 🥉 **3** | **Shivani Saxena** | **Frontend Core Developer** | Next.js App Router core setup, root layout, live WebSocket connection status indicator, total session summary metrics, and Attacker Sessions sidebar |
| 🥉 **4** | **Khushi Wankhede** | **Frontend Streaming Developer** | Real-time command stream component (`LiveFeed.tsx`) & interactive terminal bash session replay player (`TerminalReplay.tsx`) |
| 🥉 **5** | **Anushka Mudgal** | **Frontend Analytics & Reports** | Recharts threat data analytics (`Analytics.tsx`) & PDF/CSV/JSON export control panel (`ExportPanel.tsx`) |

> 📖 **Faculty Evaluation Document**: See [FACULTY_PROJECT_DOCUMENTATION.md](file:///d:/Codes/SentinelTrap/FACULTY_PROJECT_DOCUMENTATION.md) for official academic evaluation details.

---

## 🚀 Quickstart & Deployment

### Prerequisites
- [Docker & Docker Compose](https://www.docker.com/)
- Python 3.10+ (or Python 3.13)
- Node.js 18+ (for Next.js frontend)

### Running via Docker Compose
```bash
docker-compose up --build
```

**Services Running:**
- **FastAPI Threat Backend**: `http://localhost:8000` (API Docs: `http://localhost:8000/docs`)
- **SSH Honeypot Node**: `localhost:2222`
- **Telnet Honeypot Node**: `localhost:2223`
- **HTTP Web Trap Node**: `http://localhost:8080`
- **FTP Honeypot Node**: `localhost:2121`

---

## 🧪 Testing Deception Traps

1. **Connect via SSH**:
   ```bash
   ssh root@localhost -p 2222
   ```
2. **Execute Commands**:
   - `whoami` & `ls -la`
   - `cat /etc/passwd` *(Triggers Credential Deception Trap)*
   - `mysql -u root` *(Triggers Database Deception Trap)*
   - `nmap 192.168.1.1` *(Triggers Network Reconnaissance Trap)*

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
