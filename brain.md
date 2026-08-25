# 🛡️ SentinelTrap — Complete Project Brain

> **This document is the single authoritative reference for the entire SentinelTrap codebase.**
> Every file, module, API route, environment variable, database table, port, class, and design decision is documented here.
> Neither a human nor an AI agent should need to re-read the raw source code to understand this project.

---

## Table of Contents

1. [Project Identity](#1-project-identity)
2. [Repository Layout](#2-repository-layout)
3. [System Architecture](#3-system-architecture)
4. [Technology Stack](#4-technology-stack)
5. [Deployment & Running](#5-deployment--running)
6. [Backend — FastAPI Threat Intelligence Engine](#6-backend--fastapi-threat-intelligence-engine)
7. [Honeypot Suite — Multi-Protocol Decoy Nodes](#7-honeypot-suite--multi-protocol-decoy-nodes)
8. [Frontend — Next.js SOC Dashboard](#8-frontend--nextjs-soc-dashboard)
9. [Full REST & WebSocket API Reference](#9-full-rest--websocket-api-reference)
10. [Database Schema](#10-database-schema)
11. [Environment Variables](#11-environment-variables)
12. [Network Port Map](#12-network-port-map)
13. [Event Types Glossary](#13-event-types-glossary)
14. [Vulnerability Codes & MITRE ATT&CK Mapping](#14-vulnerability-codes--mitre-attck-mapping)
15. [Threat Risk Scoring Algorithm](#15-threat-risk-scoring-algorithm)
16. [Adaptive Deception Engine — Trigger Logic](#16-adaptive-deception-engine--trigger-logic)
17. [Data Flow — End-to-End Attack Capture](#17-data-flow--end-to-end-attack-capture)
18. [Team & Responsibility Map](#18-team--responsibility-map)
19. [Known Quirks, Gotchas & Notes for Developers](#19-known-quirks-gotchas--notes-for-developers)
20. [Git Rules & What NOT to Commit](#20-git-rules--what-not-to-commit)

---

## 1. Project Identity

| Field | Value |
|---|---|
| **Project Name** | SentinelTrap |
| **Organization** | OpenThreatLabs |
| **Repository** | `OpenThreatLabs/SentinelTrap` |
| **License** | MIT |
| **Academic Context** | VIT Bhopal University — Faculty project evaluation |
| **Description** | Multi-layer adaptive honeypot & active cyber deception platform for real-time attack capture, analysis, and automated reporting |
| **Core Philosophy** | Shift from *passive blocking* (firewalls/IDS) to *active cyber deception* — luring attackers into zero-risk isolated environments |

---

## 2. Repository Layout

```
SentinelTrap/                     <- Project root
├── .gitignore                    <- Comprehensive ignore rules
├── LICENSE                       <- MIT License
├── README.md                     <- Public-facing project overview
├── FACULTY_PROJECT_DOCUMENTATION.md  <- Academic evaluation document
├── guide.txt                     <- Team setup guide
├── brain.md                      <- THIS FILE
├── docker-compose.yml            <- Orchestrates backend + honeypot containers
├── run_all.py                    <- Unified local launcher (no Docker)
├── sentinel.db                   <- SQLite DB at root (dev copy)
│
├── backend/                      <- FastAPI Threat Intelligence API
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                   <- App entry point, all routes, WebSocket broker
│   ├── database.py               <- SQLAlchemy engine & session factory
│   ├── models.py                 <- ORM: SessionModel, EventModel, DecoyModel
│   ├── schemas.py                <- Pydantic schemas
│   ├── geolocate.py              <- IP geolocation with LRU cache
│   ├── analytics.py              <- Risk scoring & threat classification
│   ├── vulnerabilities.py        <- RegEx vuln detection + MITRE mapping
│   ├── reporting.py              <- PDF report generation (ReportLab)
│   ├── exporter.py               <- STIX 2.1 JSON + CEF syslog exporters
│   ├── alerts.py                 <- Slack/Discord webhook alerter
│   ├── autoshun.py               <- Auto-shun firewall rule generator
│   ├── decoys.py                 <- Decoy management FastAPI router
│   ├── middleware.py             <- Rate limiter + security headers
│   └── sentinel.db               <- SQLite DB used in Docker
│
├── honeypot/                     <- Multi-protocol honeypot suite
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── runner.py                 <- Launches all 9 honeypot threads
│   ├── server.py                 <- SSH honeypot (Paramiko, Port 2222)
│   ├── shell.py                  <- Virtual Linux shell session
│   ├── deception.py              <- Adaptive Deception Engine
│   ├── telnet_server.py          <- Telnet honeypot (Port 2223)
│   ├── ftp_server.py             <- FTP honeypot (Port 2121)
│   ├── web_trap.py               <- HTTP web trap (Port 8080)
│   ├── web_honeypot.py           <- Advanced HTTP honeypot (8080 & 8081)
│   ├── smtp_honeypot.py          <- SMTP mail honeypot (Port 2525)
│   ├── mysql_honeypot.py         <- MySQL honeypot (Port 3306)
│   ├── redis_honeypot.py         <- Redis honeypot (Port 6379)
│   ├── dns_honeypot.py           <- DNS honeypot (UDP Port 5353)
│   ├── port_scanner_trap.py      <- RDP/port-scanner trap (Port 3389)
│   ├── canary.py                 <- Honeytoken generator & validator
│   ├── fake_ports.py             <- Fake open ports on 12+ ports (Nmap trap)
│   ├── ftp_smtp_honeypot.py      <- Combined FTP+SMTP (alternate impl.)
│   ├── telnet_honeypot.py        <- Alternate telnet implementation
│   ├── attack_simulator.py       <- Simulates real attacker behaviour
│   ├── demo_simulator.py         <- Injects sample events for demos
│   └── evidence/                 <- Captured evidence (gitignored)
│
└── frontend/                     <- Next.js 16 SOC Dashboard UI
    ├── package.json
    ├── next.config.ts
    ├── tsconfig.json
    ├── app/
    │   ├── layout.tsx             <- Root HTML layout
    │   ├── page.tsx               <- Root page + navigation state
    │   └── globals.css
    ├── components/
    │   ├── Header.tsx             <- Navbar + WebSocket status
    │   ├── MetricCards.tsx        <- Top 3 KPI cards
    │   ├── SessionSidebar.tsx     <- Live attacker session list
    │   ├── SessionsView.tsx       <- Full sessions table + detail drawer
    │   ├── Alerts.tsx             <- Alert feed
    │   ├── Analytics.tsx          <- Recharts charts
    │   ├── LiveFeed.tsx           <- Real-time command stream
    │   ├── TerminalReplay.tsx     <- Terminal session replay
    │   ├── ExportPanel.tsx        <- PDF/CSV/JSON export buttons
    │   └── BackendFeaturesView.tsx <- Backend feature showcase
    └── lib/
        └── honeypot-events.ts     <- Types, helpers, simulation functions
```

---

## 3. System Architecture

```
                    [ ATTACKER / SCANNER / BOT ]
                                 |
     SSH:2222  Telnet:2223  HTTP:8080  FTP:2121  SMTP:2525
     MySQL:3306  Redis:6379  DNS:5353  RDP:3389
                                 |
                      Virtual Shell (shell.py)
                      [SSH & Telnet only]
                                 |
                    Adaptive Deception Engine (deception.py)
                                 |
              POST /api/sessions + POST /api/sessions/{id}/events
                                 |
                    FastAPI Backend (Port 8000)
                    - IP Geolocation (ip-api.com)
                    - Risk Scoring
                    - WebSocket Broker /ws
                    - SQLite DB
                                 |
              WebSocket /ws + REST polling every 1.5s
                                 |
                    Next.js Dashboard (Port 3000)
                    SOC Real-time UI
```

**Key flows:**
- Every honeypot node registers attacker via `POST /api/sessions`
- Commands/events logged via `POST /api/sessions/{id}/events`
- Session end via `PATCH /api/sessions/{id}`
- Backend **broadcasts** every write to all WebSocket clients immediately
- Frontend subscribes to `ws://localhost:8000/ws` for real-time updates

---

## 4. Technology Stack

### Backend
| Layer | Technology | Version |
|---|---|---|
| Web Framework | FastAPI | >= 0.111.0 |
| ASGI Server | Uvicorn | >= 0.30.1 |
| ORM | SQLAlchemy | >= 2.0.31 |
| Validation | Pydantic | >= 2.8.0 |
| Database | SQLite | Built-in |
| PDF Reports | ReportLab | >= 4.2.2 |
| HTTP Client | Requests | >= 2.32.3 |
| SSH Protocol | Paramiko | 3.4.0 |
| Crypto | cryptography | 42.0.5 |
| Runtime | Python | 3.10+ |
| Container | Docker (python:3.10-slim) | — |

### Frontend
| Layer | Technology | Version |
|---|---|---|
| Framework | Next.js (App Router) | 16.3.1 |
| Language | TypeScript | ^5 |
| Runtime | React | 19.2.8 |
| Styling | Tailwind CSS | ^4 |
| Charts | Recharts | ^3.10.1 |
| Icons | lucide-react | ^1.31.0 |
| Fonts | Geist Sans + Geist Mono | — |

---

## 5. Deployment & Running

### Option A — Docker Compose

```bash
docker-compose up --build
```

Docker services:
- `sentineltrap_backend` — port 8000, context `./backend`
- `sentineltrap_honeypot` — port 2222, context `./honeypot`
- Network: `sentineltrap_network`
- Note: docker-compose only exposes SSH + backend. Other honeypot ports need manual configuration.

### Option B — Local Python (Full 9-protocol suite)

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r backend/requirements.txt
pip install -r honeypot/requirements.txt
python run_all.py
```

`run_all.py` launches:
1. `backend/main.py` — FastAPI on port 8000
2. `honeypot/runner.py` — All 9 honeypot threads

### Option C — Frontend (SOC Dashboard)

```bash
cd frontend
npm install
npm run dev    # http://localhost:3000
```

### Service URLs

| Service | URL |
|---|---|
| SOC Dashboard | `http://localhost:3000` |
| FastAPI REST | `http://localhost:8000` |
| Swagger Docs | `http://localhost:8000/docs` |
| WebSocket | `ws://localhost:8000/ws` |
| SSH Honeypot | `ssh root@localhost -p 2222` |

---

## 6. Backend — FastAPI Threat Intelligence Engine

### 6.1 `database.py`

```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sentinel.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():   # FastAPI dependency injection
    db = SessionLocal()
    try: yield db
    finally: db.close()
```

- SQLite by default; env var `DATABASE_URL` for PostgreSQL in production
- `check_same_thread=False` needed for SQLite thread safety with FastAPI

---

### 6.2 `models.py` — SQLAlchemy ORM

#### `SessionModel` -> table `sessions`
| Column | Type | Notes |
|---|---|---|
| `id` | String PK | UUID auto-generated |
| `ip_address` | String (indexed) | Attacker IP |
| `protocol` | String (indexed) | SSH, HTTP, FTP, MySQL, etc. Default: "SSH" |
| `country` | String | From IP geolocation |
| `city` | String | From IP geolocation |
| `latitude` | Float nullable | — |
| `longitude` | Float nullable | — |
| `username_attempted` | String | Captured credential |
| `password_attempted` | String | Captured credential |
| `started_at` | DateTime | Auto-set on create |
| `ended_at` | DateTime nullable | Set on PATCH |

Relationship: `events` — one-to-many — `EventModel` (cascade delete)

#### `EventModel` -> table `events`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK autoincrement | — |
| `session_id` | String FK -> sessions.id | — |
| `timestamp` | DateTime | Auto-set |
| `protocol` | String | Defaults to "SSH" |
| `event_type` | String | See Event Types Glossary |
| `vulnerability_code` | String nullable | WPH, UCE, UFH, PSI, SSRF, etc. |
| `input_data` | Text nullable | Raw attacker command/payload |
| `output_data` | Text nullable | Deception/system response |

Relationship: `session` — many-to-one — `SessionModel`

#### `DecoyModel` -> table `decoys`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | — |
| `name` | String | Descriptive name |
| `type` | String | `port`, `file`, `database`, `network` |
| `status` | String | `active` / `inactive` |
| `triggered_by_session` | String FK nullable | — |
| `activated_at` | DateTime nullable | — |

---

### 6.3 `schemas.py` — Pydantic Schemas

| Schema | Direction | Fields |
|---|---|---|
| `SessionCreate` | Request for `POST /api/sessions` | `ip_address`, `username_attempted`, `password_attempted` |
| `SessionResponse` | Response | All session fields |
| `EventCreate` | Request for `POST /api/sessions/{id}/events` | `event_type`, `input_data`, `output_data` |
| `EventResponse` | Response | All event fields |
| `TopItem` | Embedded in stats | `name`, `count` |
| `ThreatStatsOverview` | Response for overview | `total_sessions`, `total_events`, `top_usernames`, `top_commands` |

---

### 6.4 `main.py` — FastAPI Application

App startup:
```python
models.Base.metadata.create_all(bind=database.engine)   # Auto-create tables
app = FastAPI(title="SentinelTrap Threat Intelligence Backend")
app.add_middleware(SecurityAuditMiddleware, requests_per_minute=300)
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
app.include_router(decoys.router)   # /api/decoys
```

**WebSocket ConnectionManager**:
```python
class ConnectionManager:
    active_connections: list[WebSocket]
    async def connect(websocket)    # accept + append
    def disconnect(websocket)       # remove
    async def broadcast(message)    # send to all
```

**Every DB write immediately calls `manager.broadcast()`** — this drives all frontend real-time updates.

**Demo seed data** (`POST /api/data/seed`) inserts 5 sessions if not already present:
1. `185.220.101.5` (Germany, Frankfurt) — SSH, root, shadow file access + stage2 payload download
2. `194.26.29.114` (Netherlands, Amsterdam) — HTTP, SQL injection + UNION SELECT
3. `45.155.205.233` (Russia, Moscow) — MySQL, database dump attempt
4. `91.240.118.242` (Bulgaria, Sofia) — Redis, cron injection via CONFIG SET
5. `103.149.138.82` (Singapore) — Telnet, network enum

---

### 6.5 `geolocate.py` — IP Geolocation Service

**Class**: `IPThreatIntelligenceService`
- API: `http://ip-api.com/json/{ip}?fields=status,country,city,lat,lon,isp,as,mobile,proxy`
- Timeout: 3 seconds
- **LRU cache** `maxsize=1024` prevents repeated lookups for same IP
- Private IPs (`127.0.0.1`, `192.168.x`, `10.x`, `::1`) return hardcoded "Local Network" data
- Returns: `{ip, country, city, latitude, longitude, isp, asn, is_proxy}`
- Falls back to "Unknown" on API failure
- **Rate limit warning**: ip-api.com free tier = ~45 req/minute

---

### 6.6 `analytics.py` — Threat Risk Scoring Engine

**Class**: `ThreatAnalyticsEngine`

**`calculate_risk_score(events) -> (score, classification, indicators)`**:

| Rule | Pattern | Score Added | Classification |
|---|---|---|---|
| Credential Search | `passwd\|shadow\|id_rsa\|pass\|credentials` | +30 | Credential Harvester |
| Database Probe | `mysql\|psql\|mongo\|sqlite\|dump\|sql` | +25 | DB Exploit Vector |
| Network Recon | `nmap\|ifconfig\|ip a\|netstat\|route\|arp` | +20 | Reconnaissance Probe |
| System Enum | `cat\|ls\|whoami\|pwd\|id\|uname` | +5 | (indicator only) |
| Base | — | 10 | — |

- **Score capped at 100**
- Classification priority: Credential Harvester > DB Exploit Vector > Reconnaissance Probe > Automated Botnet Scanner

**`get_ip_threat_profile(ip_address, db) -> dict`**:
- Queries all sessions from that IP, computes risk score, returns full threat profile

---

### 6.7 `vulnerabilities.py` — Vulnerability Detection

Standalone payload analysis module. Available for import by any component.

**Vulnerability Codes (`VULN_PATTERNS`):**

| Code | Type | Example Pattern |
|---|---|---|
| `PSI` | SQL Injection | `union select`, `' OR '1'='1`, `admin'--` |
| `UCE` | Command Injection | `; whoami`, `\| bash`, `$(cmd)` |
| `UFH` | Path Traversal | `../../`, `/etc/passwd`, `/etc/shadow` |
| `SSRF` | Server-Side Request Forgery | `169.254.169.254`, `metadata/v1` |
| `XSS` | Cross-Site Scripting | `<script>`, `onerror=`, `javascript:` |
| `ID` | Insecure Deserialization | `rO0AB` (Java), `gASV` (Python pickle) |
| `DDE` | Dynamic Execution | `eval(`, `exec(`, `system(` |
| `HC` | Hardcoded Credentials | `AKIA...` (AWS), `password = "..."` |
| `WPH` | Brute Force / Weak Passwords | `admin\|root\|password\|123456` |

**Functions**:
- `analyze_payload(input_text) -> list[str]` — returns detected vuln codes
- `calculate_risk_score(events_list) -> int` — weights-based 0-100 score (System 2)
- `get_mitre_info(vuln_code) -> dict` — MITRE ATT&CK metadata

---

### 6.8 `reporting.py` — PDF Report Generator

**Class**: `IncidentReportGenerator` (uses ReportLab)

**`generate_pdf_report(session_id, db) -> io.BytesIO`**:
- Per-session forensic report
- Contents: session metadata, geo/ISP data, risk score, threat classification, command timeline table
- Design: dark header (`#0f172a`), light body (`#f8fafc`)

**`generate_summary_pdf_report(db) -> io.BytesIO`**:
- Executive SOC summary covering all sessions
- Top 15 sessions table + top 20 events table
- References "SentinelTrap Multi-Layer Honeypot Mesh (VIT Bhopal)"

---

### 6.9 `exporter.py` — STIX 2.1 & CEF Exporter

**Class**: `ThreatTelemetryExporter`

**`export_stix21_format(db) -> dict`**:
- STIX 2.1 JSON bundle: Identity + Indicator objects (one per session IP) + Observed-Data
- Compatible with Splunk, Microsoft Sentinel, Elastic SIEM

**`export_cef_format(db) -> str`**:
- Format: `CEF:0|OpenThreatLabs|SentinelTrap|1.0|{event_type}|...|src={ip} msg={input}`

---

### 6.10 `alerts.py` — Security Alert Dispatcher

**Class**: `SecurityAlertDispatcher`

| Method | Target | Trigger Condition |
|---|---|---|
| `dispatch_slack_notification()` | Slack Webhook | `SLACK_WEBHOOK_URL` env var set |
| `dispatch_discord_notification()` | Discord Webhook | `DISCORD_WEBHOOK_URL` env var set |
| `evaluate_and_dispatch()` | Both | `risk_score >= 70` OR critical event type |

Alert colour: Red for risk >= 75, Amber for lower. Silent if env vars not set.

---

### 6.11 `autoshun.py` — Auto-Shun Firewall Engine

**Class**: `AutoShunFirewallEngine`

**`generate_firewall_rules(db, risk_threshold=75) -> dict`**:
- Scans all sessions, computes risk per unique IP
- For IPs above threshold, generates:
  - `iptables -A INPUT -s {ip} -j DROP`
  - `ufw deny from {ip} to any`
  - `iptables -t nat -A PREROUTING -s {ip} -p tcp --dport 22 -j DNAT --to-destination 10.0.4.18:2222` (NAT decoy redirect)

---

### 6.12 `decoys.py` — Decoy Management Router

**Router prefix**: `/api/decoys`

**Default decoys** (auto-seeded on first list):
1. `Honey Credential File (/etc/passwd)` — type: `file`, status: `active`
2. `Decoy Database Cluster (10.0.4.18:3306)` — type: `database`, status: `active`
3. `Decoy Routing Network (10.0.4.25)` — type: `network`, status: `active`
4. `Honey Production API Keys (/etc/cloud/secrets.env)` — type: `file`, status: `inactive`

Endpoints:
- `GET /api/decoys` — list all decoys
- `POST /api/decoys/trigger/{decoy_id}` — activate
- `POST /api/decoys/reset/{decoy_id}` — reset to inactive

---

### 6.13 `middleware.py` — Security Audit Middleware

**Class**: `SecurityAuditMiddleware(BaseHTTPMiddleware)`

- **Rate limit**: 300 req/minute per IP on `/api/` routes → HTTP 429 on excess
- **WebSocket bypass**: WS requests skip middleware entirely
- **Security headers on every response**:
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Server: SentinelTrap-ThreatEngine/1.0`

---

## 7. Honeypot Suite — Multi-Protocol Decoy Nodes

### 7.1 `runner.py` — Multi-Protocol Orchestrator

Launches **9 honeypot services** as daemon threads (0.2s delay between each):

| # | Service | Port | Class/Function |
|---|---|---|---|
| 1 | SSH | TCP 2222 | `server.main` |
| 2 | Telnet | TCP 2223 | `TelnetHoneypotServer().start()` |
| 3 | HTTP Web Trap | TCP 8080 | `web_trap.main` |
| 4 | FTP | TCP 2121 | `FTPHoneypotServer().start()` |
| 5 | SMTP | TCP 2525 | `SMTPHoneypotServer().start()` |
| 6 | MySQL | TCP 3306 | `MySQLHoneypotServer().start()` |
| 7 | Redis | TCP 6379 | `RedisHoneypotServer().start()` |
| 8 | DNS | UDP 5353 | `DNSHoneypotServer().start()` |
| 9 | Port Scanner/RDP | TCP 3389 | `PortScannerHoneypotTrap().start()` |

---

### 7.2 `server.py` — SSH Honeypot

- **Port**: 2222 (env `PORT`)
- **Library**: Paramiko
- **Host Key**: Auto-generated 2048-bit RSA (`test_rsa.key`) on first run
- **Always accepts every password** (`AUTH_SUCCESSFUL`)
- Registers session with backend on auth attempt
- Extracts `session_id` from backend response
- Sends fake Ubuntu 22.04 welcome banner
- Character-by-character terminal loop (handles backspace `\x7f`, Ctrl+C `\x03`, Ctrl+D `\x04`)
- On disconnect: `PATCH /api/sessions/{id}`

---

### 7.3 `shell.py` — Virtual Shell Session

**Class**: `VirtualShellSession`

- Simulated host: `root@prod-web-srv-01`, starting CWD: `/root`
- Integrates `AdaptiveDeceptionEngine` (checked first)

**Simulated commands:**

| Command | Response |
|---|---|
| `cd [dir]` | Changes internal `cwd` state |
| `pwd` | Returns `self.cwd` |
| `whoami` | `"root"` |
| `id` | `"uid=0(root) gid=0(root) groups=0(root)"` |
| `ls` / `ll` | Fake directory listing with `config.json`, `deploy.sh` |
| `cat config.json` | Fake JSON: `db_host: 10.0.4.18`, `api_key: sk_prod_9021849128` |
| `cat deploy.sh` | Fake deploy script |
| `sudo` / `su` | "not in sudoers" |
| `help` | Lists available commands |
| `clear` | ANSI clear screen |
| `exit` | Returns `"exit"` (ends session) |
| Anything else | `bash: {cmd}: command not found` |

---

### 7.4 `deception.py` — Adaptive Deception Engine

**Class**: `AdaptiveDeceptionEngine`

**`inspect_and_respond(command) -> (output, triggered, trap_type)`**:

| Trigger Pattern | Trap Type | Response |
|---|---|---|
| `cat.*passwd`, `grep.*pass`, `cat.*shadow`, `cat.*id_rsa` | `credential_harvesting` | Fake `/etc/passwd` with honey users (`admin`, `db_backup_user`, `deploy_user`) + API key hint |
| `mysql`, `psql`, `postgres`, `mongo`, `sqlite`, `dump`, `redis-cli` | `database_access_attempt` | `ERROR 1045 (28000)` + "warning dispatched to SecOps" |
| `nmap`, `ping`, `ifconfig`, `ip a`, `netstat`, `route`, `arp`, `traceroute` | `network_reconnaissance` | Fake routing table with `10.0.4.18` (Decoy DB) and `10.0.4.25` (Decoy Auth Gateway) |

---

### 7.5 `telnet_server.py` — Telnet Honeypot

- **Port**: 2223 (env `TELNET_PORT`)
- Sends Telnet negotiation bytes (`\xFF\xFB\x01\xFF\xFB\x03`)
- Prompts: `prod-web-srv-01 login:` -> `Password:`
- Registers session after credentials captured
- Reuses `VirtualShellSession` (same as SSH)
- PATCH session on disconnect

---

### 7.6 `ftp_server.py` — FTP Honeypot

- **Port**: 2121 (env `FTP_PORT`)
- Banner: `220 (vsFTPd 3.0.3 - Production File Server)`
- Always `230 Login successful` to any USER/PASS
- Registers session on PASS command with `ftp_` prefix on username
- Logs `ftp_command_execution` events for: SYST, PWD, CWD, TYPE, PORT, PASV, LIST, STOR, RETR
- `STOR` replies "Payload captured" (traps upload attempts)
- `RETR` returns `550 Access Denied`

---

### 7.7 `web_trap.py` — HTTP Web Trap

- **Port**: 8080 (env `WEB_TRAP_PORT`)
- Registers session + event for every request
- GET: serves fake admin login form or directory listing; passes URL through deception engine
- POST: responds `401 Unauthorized: Credentials logged`

---

### 7.8 `web_honeypot.py` — Advanced Web Honeypot

Runs on **ports 8080 and 8081** with `ThreadedHTTPServer`.

GET handler precedence:
1. **Path Traversal** (`../` or `etc/passwd`) -> `UFH` code -> returns fake `/etc/passwd`
2. **Exposed Secrets** (`/.env`, `/config.json`, `/aws_credentials`) -> `HC` code -> returns fake env/AWS creds
3. **SSRF Probe** (`/api/v1/fetch` or `url` in query) -> `SSRF` code -> returns fake AWS credentials
4. **Default** -> serves Acme Corp admin login HTML page (HTML comment contains `admin / P@ssw0rd2026_Prod` honey credentials)

POST handler: Detects SQL injection -> `PSI` code; command injection -> `UCE` code.

---

### 7.9 `smtp_honeypot.py` — SMTP Mail Honeypot

- **Port**: 2525 (env `SMTP_PORT`)
- Banner: `220 mail.prod-web-srv-01.local ESMTP Postfix (Ubuntu)`
- Supports: HELO/EHLO, MAIL FROM, RCPT TO, DATA, QUIT
- Registers session on MAIL FROM (sender as username)
- Captures full email body in DATA mode
- Logs `smtp_phishing_captured` event (sender, recipients, body snippet 300 chars)

---

### 7.10 `mysql_honeypot.py` — MySQL Honeypot

- **Port**: 3306 (env `MYSQL_PORT`)
- Sends **real MySQL v10 binary handshake packet** (version `5.7.34-log`)
- Extracts username from auth packet at byte offset 36
- Registers session with `mysql_` prefix
- Returns **real MySQL error packet** `ERROR 1045 (28000): Access denied`
- Logs `deception_triggered` event

---

### 7.11 `redis_honeypot.py` — Redis Honeypot

- **Port**: 6379 (env `REDIS_PORT`)
- Registers session on first connection (`redis_unauth`)
- Logs every command as `redis_command_probe`
- Responds: `PING` -> `+PONG`, `AUTH` -> `-ERR invalid password`, `INFO` -> fake Redis 6.2.6 info, `CONFIG SET` -> `+OK` (detects RCE), `FLUSHALL/KEYS` -> fake key list, everything else -> `+OK`

---

### 7.12 `dns_honeypot.py` — DNS Honeypot

- **Port**: UDP 5353 (env `DNS_PORT`)
- Uses `socket.SOCK_DGRAM` (UDP)
- Parses queried domain from raw DNS bytes (offset 12)
- Returns A-record pointing to `10.0.4.18`
- Registers session (username: `dns_query`, password: queried domain)
- Logs `dns_recon_attempt` event

---

### 7.13 `port_scanner_trap.py` — Port Scanner Trap

- **Port**: TCP 3389 (env `SCANNER_PORT`) — mimics RDP
- Logs `port_scan_detected` event with hex payload
- Port-specific decoy responses:
  - Port 3389 -> RDP confirm packet
  - Port 5900 -> VNC `RFB 003.008\n`
  - Others -> `220 Enterprise Service Ready`

---

### 7.14 `canary.py` — Honeytoken Manager

**Class**: `HoneytokenManager`

- `generate_aws_honeykey()` -> creates `AKIA{UUID[:16].upper()}` + sha256 secret
- `generate_jwt_honeytoken()` -> `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.{uuid}.honey_sig_prod`
- `check_and_alert(candidate_token, attacker_ip)` -> scans for registered tokens, fires backend alert
- When triggered: registers session, logs `honeytoken_compromised` event

---

### 7.15 `fake_ports.py` — Fake Open Ports Engine

Binds to 12 ports simultaneously for Nmap/Masscan trap:

| Port | Fake Banner |
|---|---|
| 21 | ProFTPD 1.3.5 |
| 22 | OpenSSH_8.9p1 |
| 23 | Acme Router OS v4.2 |
| 25 | Postfix ESMTP |
| 80 | Apache/2.4.52 |
| 110 | POP3 server |
| 143 | IMAP4rev1 |
| 3306 | MySQL 5.7.38 (binary) |
| 3389 | RDP confirm |
| 5432 | PostgreSQL FATAL |
| 5900 | VNC RFB 003.008 |
| 6379 | Redis -ERR |
| 8080 | nginx/1.18.0 |

All logged as `nmap_port_scan` with `vulnerability_code: NMAP_RECON`.

---

### 7.16 Other Honeypot Files

| File | Purpose |
|---|---|
| `ftp_smtp_honeypot.py` | Combined FTP+SMTP — alternate/earlier implementation |
| `telnet_honeypot.py` | Alternate telnet implementation |
| `attack_simulator.py` | Test: simulates SSH brute force + command execution |
| `demo_simulator.py` | Demo: injects sample events for presentations |

---

## 8. Frontend — Next.js SOC Dashboard

### 8.1 Project Structure

- **Framework**: Next.js 16, App Router
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS v4
- **State**: React hooks only (useState, useEffect) — no Redux/Zustand
- **Data fetching**: `fetch()` with 1.5s polling + WebSocket real-time
- **Env vars**: `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_SENTINELTRAP_WS_URL`

---

### 8.2 `app/layout.tsx`

- Root HTML; Geist Sans + Geist Mono fonts via CSS variables
- `metadata.title`: "SentinelTrap | Cyber Defense & Autonomous Threat Intelligence"
- Dark mode default: `className="dark h-full antialiased"`
- `suppressHydrationWarning` on `<html>` for client-side theme toggle

---

### 8.3 `app/page.tsx` — Root Page & Navigation

- State: `activePage` (string), `isDark` (boolean)
- Theme stored in `localStorage` key `"theme"`
- Pages: Dashboard, Sessions, Alerts, Analytics, Backend Features
- Floating bottom-right theme toggle button (Sun/Moon icons)
- Dashboard layout: MetricCards + 3-col grid (SessionSidebar 1-col + workspace 2-col)

---

### 8.4 `components/Header.tsx`

- Sticky top navbar (z-40)
- Brand: gradient shield icon (cyan->indigo->fuchsia) + "SentinelTrap" + "OpenThreatLabs"
- Nav tabs: Dashboard, Sessions, Alerts, Analytics, Backend Features
- **Backend status indicator**: dual-check (WebSocket + HTTP poll to `/api/stats/overview`)
  - Green pulsing = Live; Red = Offline
  - WS reconnect: 2s timeout; health poll: every 1.5s

---

### 8.5 `components/MetricCards.tsx`

Three KPI cards (fetch `/api/stats/overview` every 1.5s + WebSocket trigger):

| Card | Metric | Colour |
|---|---|---|
| Active Attacker Sessions | `total_sessions` | Cyan |
| Forensic Commands Captured | `total_events` | Emerald |
| Deception & Canary Probes | `min(total_events, 4)` | Rose |

---

### 8.6 `components/SessionSidebar.tsx`

- Fetches `GET /api/sessions` every 1.5s + WebSocket trigger
- Shows: IP, country, city, username, start time
- Active sessions: pulsing emerald dot; closed: grey dot
- Supports `onSelectSession` callback + `selectedSessionId` highlight

---

### 8.7 `components/SessionsView.tsx`

- Full sessions table with expandable detail drawer
- Shows risk score, protocol badge, geo, threat classification
- Integrates `TerminalReplay` and `ExportPanel`

---

### 8.8 `components/Alerts.tsx`

- Fetches `GET /api/events/alerts` (events enriched with IPs)
- Colour-coded severity badges by event type
- Filters: All, Command, Deception, Auth, System
- Auto-refreshes via WebSocket

---

### 8.9 `components/Analytics.tsx`

- Uses **Recharts** library
- Charts: sessions over time (AreaChart), top commands (BarChart), threat classification (PieChart)
- Written by: **Anushka Mudgal**

---

### 8.10 `components/LiveFeed.tsx`

- Real-time command stream; subscribes to WebSocket `/ws`
- On `new_event` message: appends to feed list
- Shows: timestamp, event type badge, IP, command payload
- Written by: **Khushi Wankhede**

---

### 8.11 `components/TerminalReplay.tsx`

- Interactive terminal session replay
- Fetches events via `GET /api/sessions/{id}/events`
- Replays with simulated typing animation
- Uses `simulateDeceptionResponse()` and `simulateShellOutput()` from `lib/honeypot-events.ts`
- Play/Pause/Step/Speed controls
- Written by: **Khushi Wankhede**

---

### 8.12 `components/ExportPanel.tsx`

| Button | Endpoint |
|---|---|
| Download PDF Summary | `GET /api/export/pdf` |
| Download CSV | `GET /api/export/csv` |
| Download STIX 2.1 | `GET /api/reports/stix` |
| Download CEF Syslog | `GET /api/export/cef` |
| Download JSON | `GET /api/reports/export?format=json` |

Written by: **Anushka Mudgal**

---

### 8.13 `components/BackendFeaturesView.tsx`

Interactive showcase:
- AutoShun firewall rules (`GET /api/firewall/rules`)
- Decoy management (`GET /api/decoys`, `POST /api/decoys/trigger/{id}`)
- Data seed (`POST /api/data/seed`)
- Data clear (`DELETE /api/data/clear`)
- IP threat intel lookup (`GET /api/threat-intel/ip/{ip}`)

---

### 8.14 `lib/honeypot-events.ts`

```typescript
interface HoneypotEvent { id, event_type, input_data, output_data, timestamp, session_id }
type EventCategory = "command" | "deception" | "auth" | "system"

categorizeEvent(eventType)          // Maps event_type -> EventCategory
humanizeEventType(eventType)        // "command_execution" -> "Command Execution"
createShellReplayState()            // { cwd: "/root", env: {USER, HOME, SHELL} }
simulateDeceptionResponse(input)    // TypeScript mirror of backend deception.py logic
simulateShellOutput(input, state)   // TypeScript mirror of shell.py commands
```

---

## 9. Full REST & WebSocket API Reference

Base URL: `http://localhost:8000`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/sessions` | Create session (geo-enriched) |
| `PATCH` | `/api/sessions/{session_id}` | End session |
| `POST` | `/api/sessions/{session_id}/events` | Log event |
| `GET` | `/api/sessions` | List all sessions (desc by time) |
| `GET` | `/api/sessions/{session_id}` | Get single session |
| `GET` | `/api/sessions/{session_id}/events` | Get session events |
| `GET` | `/api/events/session/{session_id}` | Alias for above |
| `GET` | `/api/events/alerts` | Recent 100 events + IP enrichment |
| `GET` | `/api/threat-intel/ip/{ip}` | Full IP threat profile + risk score |
| `GET` | `/api/firewall/rules?risk_threshold=75` | Auto-shun firewall rules |
| `GET` | `/api/reports/pdf/summary` | Executive SOC PDF |
| `GET` | `/api/export/pdf` | Alias for above |
| `GET` | `/api/reports/pdf/{session_id}` | Per-session incident PDF |
| `GET` | `/api/reports/csv` | CSV export of all events |
| `GET` | `/api/export/csv` | Alias for above |
| `GET` | `/api/reports/stix` | STIX 2.1 JSON bundle |
| `GET` | `/api/threat-intel/stix2` | Alias for above |
| `GET` | `/api/reports/cef` | CEF syslog stream |
| `GET` | `/api/export/cef` | Alias for above |
| `GET` | `/api/reports/export?format=json\|csv` | Generic export |
| `GET` | `/api/stats/overview` | KPI summary |
| `DELETE` | `/api/data/clear` | Purge all data |
| `POST` | `/api/data/seed` | Inject 5 demo sessions |
| `GET` | `/api/decoys` | List decoys |
| `POST` | `/api/decoys/trigger/{decoy_id}` | Activate decoy |
| `POST` | `/api/decoys/reset/{decoy_id}` | Reset decoy |
| `GET` | `/ws` | WebSocket info (HTTP) |
| `WS` | `/ws` | WebSocket real-time stream |

**WebSocket broadcast events:**

| `event_type` | Trigger |
|---|---|
| `session_created` | New session registered |
| `session_ended` | Session terminated |
| `new_event` | Command/event logged |
| `data_cleared` | All data purged |
| `data_seeded` | Demo data injected |

---

## 10. Database Schema

```sql
CREATE TABLE sessions (
    id VARCHAR PRIMARY KEY,                 -- UUID string
    ip_address VARCHAR NOT NULL,            -- indexed
    protocol VARCHAR DEFAULT 'SSH',         -- indexed
    country VARCHAR DEFAULT 'Unknown',
    city VARCHAR DEFAULT 'Unknown',
    latitude FLOAT,
    longitude FLOAT,
    username_attempted VARCHAR DEFAULT 'Unknown',
    password_attempted VARCHAR DEFAULT 'Unknown',
    started_at DATETIME,
    ended_at DATETIME                       -- NULL = active session
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR REFERENCES sessions(id),
    timestamp DATETIME,
    protocol VARCHAR DEFAULT 'SSH',
    event_type VARCHAR NOT NULL,
    vulnerability_code VARCHAR,             -- optional: WPH, UCE, UFH, etc.
    input_data TEXT,
    output_data TEXT
);

CREATE TABLE decoys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    type VARCHAR NOT NULL,                  -- 'port', 'file', 'database', 'network'
    status VARCHAR DEFAULT 'inactive',
    triggered_by_session VARCHAR REFERENCES sessions(id),
    activated_at DATETIME
);
```

**SQLite file locations**:
- `./sentinel.db` — used when running from project root locally
- `./backend/sentinel.db` — used in Docker (backend dir mounted as `/app`)

---

## 11. Environment Variables

| Variable | Default | Used In | Description |
|---|---|---|---|
| `DATABASE_URL` | `sqlite:///./sentinel.db` | `backend/database.py` | DB connection URL |
| `BACKEND_URL` | `http://localhost:8000` | All honeypot files | FastAPI base URL |
| `PORT` | `2222` | `honeypot/server.py` | SSH honeypot port |
| `TELNET_PORT` | `2223` | `honeypot/telnet_server.py` | — |
| `FTP_PORT` | `2121` | `honeypot/ftp_server.py` | — |
| `WEB_TRAP_PORT` | `8080` | `honeypot/web_trap.py` | — |
| `WEB_PORT` | `8080` | `honeypot/web_honeypot.py` | — |
| `API_PORT` | `8081` | `honeypot/web_honeypot.py` | — |
| `SMTP_PORT` | `2525` | `honeypot/smtp_honeypot.py` | — |
| `MYSQL_PORT` | `3306` | `honeypot/mysql_honeypot.py` | — |
| `REDIS_PORT` | `6379` | `honeypot/redis_honeypot.py` | — |
| `DNS_PORT` | `5353` | `honeypot/dns_honeypot.py` | — |
| `SCANNER_PORT` | `3389` | `honeypot/port_scanner_trap.py` | — |
| `SLACK_WEBHOOK_URL` | `""` | `backend/alerts.py` | Optional alert webhook |
| `DISCORD_WEBHOOK_URL` | `""` | `backend/alerts.py` | Optional alert webhook |
| `NEXT_PUBLIC_API_BASE_URL` | `""` (empty) | Frontend | FastAPI URL for browser |
| `NEXT_PUBLIC_SENTINELTRAP_WS_URL` | `ws://127.0.0.1:8000/ws` | Frontend | WebSocket URL |

---

## 12. Network Port Map

| Port | Proto | Service | File |
|---|---|---|---|
| 3000 | TCP | Next.js Dashboard | frontend/ |
| 8000 | TCP | FastAPI Backend + WS | backend/main.py |
| 2222 | TCP SSH | SSH Honeypot | honeypot/server.py |
| 2223 | TCP Telnet | Telnet Honeypot | honeypot/telnet_server.py |
| 8080 | TCP HTTP | HTTP Web Trap | honeypot/web_trap.py |
| 8081 | TCP HTTP | HTTP API Trap | honeypot/web_honeypot.py |
| 2121 | TCP FTP | FTP Honeypot | honeypot/ftp_server.py |
| 2525 | TCP SMTP | SMTP Honeypot | honeypot/smtp_honeypot.py |
| 3306 | TCP MySQL | MySQL Honeypot | honeypot/mysql_honeypot.py |
| 6379 | TCP Redis | Redis Honeypot | honeypot/redis_honeypot.py |
| 5353 | **UDP** DNS | DNS Honeypot | honeypot/dns_honeypot.py |
| 3389 | TCP RDP | Scanner Trap | honeypot/port_scanner_trap.py |
| 21,22,23,25,80,110,143,3306,3389,5432,5900,6379,8080 | TCP | Fake Ports | honeypot/fake_ports.py |

---

## 13. Event Types Glossary

| Event Type | Source | Meaning |
|---|---|---|
| `login_attempt` | SSH, Telnet, FTP, Web | Auth attempt captured |
| `command_execution` | shell.py | Shell command executed |
| `deception_triggered` | deception.py, mysql_honeypot.py | Deception engine fired |
| `web_scan_attempt` | web_trap.py | HTTP request to web trap |
| `ftp_command_execution` | ftp_server.py | FTP protocol command |
| `redis_command_probe` | redis_honeypot.py | Redis command received |
| `dns_recon_attempt` | dns_honeypot.py | DNS query probe |
| `port_scan_detected` | port_scanner_trap.py | Network port scan |
| `smtp_phishing_captured` | smtp_honeypot.py | Phishing email body captured |
| `path_traversal_attempt` | web_honeypot.py | `../` or `/etc/passwd` in URL |
| `secret_harvesting_attempt` | web_honeypot.py | `/.env` etc. probed |
| `ssrf_attempt` | web_honeypot.py | SSRF/cloud metadata probe |
| `honeytoken_compromised` | canary.py | Honeytoken used |
| `nmap_port_scan` | fake_ports.py | Port scanner probe |
| `post_payload` | web_honeypot.py | POST body received |
| `page_view` | web_honeypot.py | Basic HTTP page view |

---

## 14. Vulnerability Codes & MITRE ATT&CK Mapping

| Code | Vulnerability | MITRE ID | Technique | Tactic |
|---|---|---|---|---|
| PSI | SQL Injection | T1190 | Exploit Public-Facing App | Initial Access |
| UCE | Command Injection | T1059 | Command & Scripting Interpreter | Execution |
| UFH | Path Traversal | T1083 | File and Directory Discovery | Discovery |
| SSRF | Server-Side Request Forgery | T1552 | Unsecured Credentials | Credential Access |
| XSS | Cross-Site Scripting | T1189 | Drive-by Compromise | Initial Access |
| ID | Insecure Deserialization | T1203 | Exploitation for Client Execution | Execution |
| DDE | Dangerous Dynamic Execution | T1059.006 | Python/Script Dynamic Execution | Execution |
| HC | Hardcoded Credentials | T1552.001 | Credentials In Files | Credential Access |
| WPH | Weak Password / Brute Force | T1110 | Brute Force | Credential Access |

---

## 15. Threat Risk Scoring Algorithm

Two parallel systems:

### System 1: `analytics.py` (Command-Pattern Based)

```
Risk Score = 10 (base)
           + 30 (credential pattern: passwd, shadow, id_rsa, pass, credentials)
           + 25 (DB pattern: mysql, psql, mongo, sqlite, dump, sql)
           + 20 (network pattern: nmap, ifconfig, netstat, route, arp)
           + 5  (system enum: cat, ls, whoami, pwd, id, uname)
           [capped at 100]
```

Classification: Credential Harvester > DB Exploit Vector > Reconnaissance Probe > Automated Botnet Scanner

### System 2: `vulnerabilities.py` (Vulnerability-Code Based)

```
Risk Score = 10 (base)
           + UCE: 25, PSI: 20, SSRF: 20, UFH: 15, ID: 25, HC: 15, WPH: 10, XSS: 10
           [capped at 100]
```

System 1 is used by `/api/threat-intel/ip/{ip}` and PDF reports.
System 2 is a standalone utility in `vulnerabilities.py`.

---

## 16. Adaptive Deception Engine — Trigger Logic

```
Attacker types command
        |
        v
deception.py: inspect_and_respond(command)
        |
        +-- matches /etc/passwd|shadow|id_rsa|grep pass?
        |    -> Return fake /etc/passwd + honey users
        |    -> Log: event_type="deception_triggered", type="credential_harvesting"
        |
        +-- matches mysql|psql|mongo|sqlite|dump|redis-cli?
        |    -> Return ERROR 1045 (DB access denied) + warning
        |    -> Log: event_type="deception_triggered", type="database_access_attempt"
        |
        +-- matches nmap|ping|ifconfig|netstat|route|arp|traceroute?
        |    -> Return fake routing table with 10.0.4.18 and 10.0.4.25
        |    -> Log: event_type="deception_triggered", type="network_reconnaissance"
        |
        +-- No match -> ("", False, "") -> shell.py handles standard commands
```

**Honey IPs shown to attackers**:
- `10.0.4.18` — "Decoy Database Host"
- `10.0.4.25` — "Decoy Auth Gateway"

---

## 17. Data Flow — End-to-End Attack Capture

```
1.  Attacker connects to SSH Port 2222
2.  server.py: Accept TCP + Paramiko handshake
3.  Attacker enters username/password
4.  server.py: POST /api/sessions -> backend registers + geolocates IP
5.  Backend: broadcasts {event_type: "session_created"} via WebSocket
6.  Frontend: MetricCards + SessionSidebar update
7.  server.py: VirtualShellSession(session_id) initialized
8.  Attacker types "cat /etc/passwd"
9.  shell.py: POST /api/sessions/{id}/events (command_execution)
10. shell.py: passes to AdaptiveDeceptionEngine.inspect_and_respond()
11. deception.py: pattern match -> triggered = True
12. shell.py: POST /api/sessions/{id}/events (deception_triggered)
13. Backend: broadcasts "new_event" twice (command + deception)
14. Frontend: LiveFeed renders new entries; MetricCards updates
15. server.py: returns deception output to attacker's terminal
16. Attacker disconnects (Ctrl+D or exit)
17. server.py: PATCH /api/sessions/{id} -> sets ended_at
18. Backend: broadcasts {event_type: "session_ended"}
```

---

## 18. Team & Responsibility Map

| Priority | Name | Role | Files Owned |
|---|---|---|---|
| 1 (Lead) | **Abhinav Mishra** | Project Lead & Core Architect | `honeypot/deception.py`, `backend/main.py`, `backend/analytics.py`, `backend/geolocate.py`, Docker setup |
| 2 | **Jaiyansh Dhaulakhandi** | Senior Backend & Honeypot Engineer | `honeypot/server.py`, `honeypot/telnet_server.py`, `honeypot/web_trap.py`, `honeypot/ftp_server.py`, `honeypot/shell.py` |
| 3 | **Shivani Saxena** | Frontend Core Developer | `frontend/app/layout.tsx`, `frontend/app/page.tsx`, `frontend/components/Header.tsx`, `frontend/components/MetricCards.tsx`, `frontend/components/SessionSidebar.tsx` |
| 4 | **Khushi Wankhede** | Frontend Streaming Developer | `frontend/components/LiveFeed.tsx`, `frontend/components/TerminalReplay.tsx` |
| 5 | **Anushka Mudgal** | Frontend Analytics & Reports | `frontend/components/Analytics.tsx`, `frontend/components/ExportPanel.tsx` |

---

## 19. Known Quirks, Gotchas & Notes for Developers

1. **Two sentinel.db files**: `./sentinel.db` (root) vs `./backend/sentinel.db`. Docker uses the backend one; running `python backend/main.py` from root uses root one. Always check your CWD.

2. **Docker-compose only exposes 2 ports**: Only SSH (2222) and API (8000) are in compose. For all 9 protocols, use `run_all.py` locally.

3. **SSH host key regeneration**: `test_rsa.key` is auto-generated on first run. Deleting it causes a new key — SSH clients will see a different fingerprint and warn.

4. **Multiple WebSocket connections**: Header, MetricCards, and SessionSidebar each create independent WS connections. Intentional for simplicity, but could be consolidated via React Context.

5. **ip-api.com rate limits**: Free tier ~45 req/minute. LRU cache helps but high-traffic deployments should use MaxMind GeoIP2.

6. **web_honeypot.py vs web_trap.py**: `runner.py` uses `web_trap.py`. `web_honeypot.py` is a more advanced version but NOT used by the runner — running them simultaneously on port 8080 would conflict.

7. **`deception.py` function gap**: `web_honeypot.py` calls `deception.get_fake_env()` and `deception.get_fake_aws_credentials()`. These may not exist in the current `deception.py` which only has `AdaptiveDeceptionEngine`. This could cause `AttributeError` if `web_honeypot.py` is run directly.

8. **`vulnerability_code` not populated via REST**: The `EventCreate` schema doesn't include `vulnerability_code`. Only `web_honeypot.py` posts it by going directly to the backend URL. Events from SSH/Telnet/FTP go through the schema and the column stays NULL.

9. **Frontend env vars for dev**: If `NEXT_PUBLIC_API_BASE_URL` is empty (default), `fetch()` uses relative paths — requires a Next.js proxy config or running on same origin. Set to `http://localhost:8000` for dev.

10. **Alert dispatching is silent**: No error if Slack/Discord webhooks aren't configured — alerts are computed but silently dropped.

11. **`attack_simulator.py` and `demo_simulator.py`**: Use `demo_simulator.py` to populate dashboard for presentations without real attack traffic.

12. **Middleware order**: `SecurityAuditMiddleware` runs before `CORSMiddleware`. Rate limiting happens before CORS headers.

13. **`run_all.py` signal handling**: On Windows, `SIGTERM` may not work — use Ctrl+C (SIGINT) for graceful shutdown.

14. **`ftp_smtp_honeypot.py` and `telnet_honeypot.py`**: These are alternate/earlier implementations, not imported by `runner.py`. They're reference/backup modules only.

---

## 20. Git Rules & What NOT to Commit

**Never commit:**
- `venv/` — Python virtual environment
- `.env` — environment secrets
- `*.db`, `*.sqlite` — database files
- `logs/`, `*.log` — log files
- `evidence/` — captured attack evidence
- `captures/`, `*.pcap` — packet captures
- `generated_reports/` — PDF/CSV exports
- `uploads/`, `downloads/` — captured payloads
- SSL certs, private keys (`.pem`, `.key`, `.crt`)
- `node_modules/`, `.next/` — Node.js build artifacts
- `__pycache__/`, `*.pyc` — Python cache
- `test_rsa.key` — SSH host key (auto-generated)

**Team workflow rules:**
1. Always `git pull` before starting work
2. Test code before committing
3. Never modify project structure without team discussion
4. The `.gitignore` keeps `.gitkeep` files to preserve directory structure

---

*Last updated: 2026-08-25 | Auto-generated from full source code analysis of SentinelTrap @ OpenThreatLabs/SentinelTrap*
