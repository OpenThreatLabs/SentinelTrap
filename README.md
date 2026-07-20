# SentinelTrap - Multi-Layer Honeypot Framework

An adaptive honeypot platform designed to attract attackers, monitor behavior in real-time, and present dynamic deception layers.

## Architecture & Work Allocation for 5 Team Members

This framework is split into modular components, making it perfect for a team of 5:

1. **Member 1: Core SSH Honeypot (`/honeypot`)**
   - Custom SSH server simulation using Paramiko.
   - Mimics terminal commands (`ls`, `cd`, `cat`, `sudo`, etc.) and handles raw SSH shells.
2. **Member 2: Adaptive Deception Engine (`/honeypot/deception.py`)**
   - Intercepts attacker commands in real time.
   - Generates fake password files, dynamic API keys, and triggers decoy services when matching patterns are detected.
3. **Member 3: Threat Intelligence & API Backend (`/backend`)**
   - FastAPI backend.
   - Coordinates database storage, session status, IP geolocation lookup, and WebSockets for real-time dashboard events.
4. **Member 4: Real-time Dashboard (`/frontend`)**
   - React + Tailwind frontend dashboard.
   - Charts, active sessions, real-time command terminal feed, and session replays.
5. **Member 5: Containerization, Reporting & DevOps (`/docker`, `/reports`)**
   - Docker configurations (`docker-compose.yml`), PDF reporting tool, and general system integration testing.

---

## Quickstart Guide

### Prerequisites
- Docker and Docker Compose
- Python 3.10+ (if running locally without Docker)
- Node.js & npm (if running frontend locally)

### Running with Docker Compose
Simply run:
```bash
docker-compose up --build
```

This starts:
- **FastAPI Backend**: `http://localhost:8000`
- **React Frontend**: `http://localhost:5173`
- **SSH Honeypot**: `localhost:2222` (Test it: `ssh admin@localhost -p 2222`)

---

## Testing the Honeypot
1. Open your terminal and connect:
   ```bash
   ssh root@localhost -p 2222
   ```
2. Enter any password.
3. Execute commands like:
   - `whoami`
   - `ls -la`
   - `cat /etc/passwd` (triggers deception file generation)
   - `mysql -u root` (triggers database deception layer)
4. Check the React dashboard to see your commands appearing in real time!
