# 🛡️ SentinelTrap: The Complete Plain-English Project Guide

> **Project Title:** SentinelTrap — Multi-Layer Adaptive Honeypot & Deception Security Platform  
> **Target Audience:** Evaluators, Academic Supervisors, Exhibition Attendees, and Non-Technical Stakeholders  
> **Format:** Plain English Comprehensive Overview (Layman's Guide)

---

## 📑 Table of Contents
1. [The Big Picture: What is SentinelTrap?](#1-the-big-picture-what-is-sentineltrap)
2. [The Real-World Problem: Why Do We Need It?](#2-the-real-world-problem-why-do-we-need-it)
3. [The Core Philosophy: Passive Defense vs. Active Deception](#3-the-core-philosophy-passive-defense-vs-active-deception)
4. [How It Works Step-by-Step (The Complete Life Cycle)](#4-how-it-works-step-by-step-the-complete-life-cycle)
5. [The 9 Decoy Traps (What We Emulate)](#5-the-9-decoy-traps-what-we-emulate)
6. [The Brain: Adaptive Deception & Honeytokens](#6-the-brain-adaptive-deception--honeytokens)
7. [The Virtual Sandbox: Why the Real Computer is 100% Safe](#7-the-virtual-sandbox-why-the-real-computer-is-100-safe)
8. [The Intelligence Engine: Scoring & MITRE ATT&CK](#8-the-intelligence-engine-scoring--mitre-attck)
9. [The Live Visual Center: Dashboard, Terminal Replay & 3D Globe](#9-the-live-visual-center-dashboard-terminal-replay--3d-globe)
10. [Automated Defense: AutoShun & Firewall Rules](#10-automated-defense-autoshun--firewall-rules)
11. [Reports & Exports: PDFs, STIX, and CEF](#11-reports--exports-pdfs-stix-and-cef)
12. [Under the Hood: Tech Stack Explained Simply](#12-under-the-hood-tech-stack-explained-simply)
13. [How to Explain the Entire Project in an Exhibition / Viva (Script)](#13-how-to-explain-the-entire-project-in-an-exhibition--viva-script)

---

## 1. The Big Picture: What is SentinelTrap?

Imagine you own a bank. 
- **Traditional security** puts a thick vault door and a guard at the entrance. If a clever burglar manages to pick the lock or crawl through a vent, they are immediately in the real vault taking real money.
- **SentinelTrap takes a completely different approach.** Right beside the real vault, we build a **fake vault** with a sign that says *"High-Value Gold & Passwords"*.
  - When the burglar enters the fake room, everything looks, feels, and responds like a real vault.
  - The gold bars and cash are fake props.
  - The burglar wastes their precious time, energy, and tools trying to break open safes that contain nothing of value.
  - While they are inside, hidden CCTV cameras record every tool they use, how they operate, and what they are looking for.
  - The system automatically triggers the alarms, blocks the doors, and sends a full investigation report to the police.

**In the digital world, SentinelTrap is that fake vault.** It is an **Active Deception Honeypot System**. It pretends to be a vulnerable corporate server so hackers attack it instead of the real company systems.

---

## 2. The Real-World Problem: Why Do We Need It?

Today's cybersecurity has three massive flaws:

1. **Firewalls & Antivirus Are Always 1 Step Behind:**  
   Traditional tools work like "Wanted" posters. They only stop viruses and hackers they have seen before (known signatures). If an attacker invents a brand-new technique or uses a "zero-day" bug, the antivirus does nothing.
2. **Companies Don't Know They Are Hacked:**  
   Industry statistics show that attackers stay inside a company's network for an average of **200+ days** before being detected ("dwell time"). During that time, they quietly steal files and search for passwords.
3. **Alert Fatigue (The "Boy Who Cried Wolf"):**  
   Security teams receive thousands of fake warning emails every day from their firewalls. They get so overwhelmed that they miss the real attacks.

**SentinelTrap Solves All Three:**
- Any connection to SentinelTrap is **100% an attacker** (because legitimate employees have no business connecting to a decoy).
- There are **ZERO false alarms**. If an alert fires, you know with absolute certainty someone is attacking you.
- It catches brand new attacks because it doesn't look for known signatures—it catches anyone knocking on the door.

---

## 3. The Core Philosophy: Passive Defense vs. Active Deception

| Traditional Defense (Passive) | SentinelTrap (Active Deception) |
| :--- | :--- |
| Hides behind a firewall and hopes nobody breaks in. | Sets up tempting bait to attract attackers away from valuable data. |
| Drops malicious traffic silently, learning nothing about the hacker. | Lets the hacker in, watching and recording their every move. |
| The attacker has all the advantages (they only need to find 1 flaw). | The defender has the advantage (the attacker is tricked into a fake maze). |
| Produces thousands of noisy false alarms every day. | Produces **zero false alarms**—only real threats trigger alerts. |
| Reaction occurs only **after** real data is stolen. | Defense happens **before** attackers even get close to real databases. |

---

## 4. How It Works Step-by-Step (The Complete Life Cycle)

```
[ Attacker on Internet or Local Network ]
                  │
                  ▼
         [ 1. Lure / Bait ]
  SentinelTrap leaves open doors 
  (SSH on 2222, Web on 8080, MySQL on 3306)
                  │
                  ▼
      [ 2. Safe Containment (VFS) ]
  Attacker logs in with "root" / "password".
  Access is granted, but trapped in an in-memory
  fake Linux filesystem (RAM only).
                  │
                  ▼
     [ 3. Adaptive Mind-Game (Deception) ]
  Attacker searches for passwords or files.
  SentinelTrap dynamically fabricates convincing
  fake passwords, fake tokens, and fake keys.
                  │
                  ▼
      [ 4. Telemetry & AI Scoring ]
  Keystrokes are categorized into MITRE ATT&CK.
  Risk score (0-100) is calculated in real time.
                  │
                  ▼
         [ 5. Actionable Defense ]
  • Live attack trajectory flashes on 3D Globe
  • Keystrokes replayed on Live Terminal
  • AutoShun creates instant firewall block rule
  • PDF investigation report generated
```

---

## 5. The 9 Decoy Traps (What We Emulate)

Hackers use different tools depending on what they are looking for. SentinelTrap offers 9 different "flavors" of fake services:

1. **SSH Decoy (Port 2222):** Pretends to be a Linux terminal login. Hackers try to brute-force passwords (`admin`, `root`, `123456`) and get full interactive command-line access to our fake shell.
2. **Web / HTTP Decoy (Port 8080):** Pretends to be an internal company portal or an administrative login page. Traps web vulnerability scanners (looking for SQL injections or exposed `.env` files).
3. **Telnet Decoy (Port 2223):** Old, unencrypted remote terminal protocol frequently targeted by IoT botnets (like the infamous Mirai botnet).
4. **FTP Decoy (Port 2121):** Pretends to be a file storage server with fake company directories.
5. **MySQL Decoy (Port 3306):** Pretends to be a company database server. Accepts SQL queries and returns fake customer lists.
6. **Redis Decoy (Port 6379):** Emulates an in-memory cache server commonly abused for remote code execution.
7. **SMTP Decoy (Port 2525):** Pretends to be an email mail exchange server to catch spammers and phishing bots.
8. **DNS Decoy (Port 5353):** Catches attackers scanning the network to discover computer names and domain layouts.
9. **RDP / Remote Desktop (Port 3389):** Emulates Windows Remote Desktop login screens.

---

## 6. The Brain: Adaptive Deception & Honeytokens

Most old-school honeypots are "static"—they give the exact same fixed reply to every command. Smart hackers quickly realize it's a trap and leave.

**SentinelTrap is Adaptive:**
- If the hacker types `cat /etc/passwd` (trying to see list of user accounts):  
  The system doesn't just return an empty error. It generates realistic user accounts, like `backup-admin`, `devops-deploy`, and `db_service`.
- **Honeytokens (Digital Marked Money):**  
  Just like banks put dye-packs or serial-number-marked banknotes in bags to track thieves later, SentinelTrap plants **Canary Honeytokens**:
  - Fake AWS cloud access keys (`AKIAIOSFODNN7EXAMPLE`)
  - Fake internal database passwords
  - Fake confidential PDF file names
- When the hacker copies those fake credentials and tries to use them anywhere else on the Internet, an alarm immediately goes off, proving that the person using them is the intruder.

---

## 7. The Virtual Sandbox: Why the Real Computer is 100% Safe

One of the biggest questions evaluators and teachers ask is:  
*"If you let a hacker log in, can't they delete your hard drive or use your computer to attack other people?"*

**Answer: Absolutely NOT.**

1. **Zero Real Host Access:**  
   The hacker is never given access to Windows or Linux. Instead, SentinelTrap includes a custom-built **In-Memory Virtual File System (VFS)**.
2. **RAM-Only Containment:**  
   When the hacker types `ls`, `mkdir`, or `cat`, they are modifying temporary variables inside Python's RAM memory. 
3. **Harmless Destruction:**  
   If the hacker types `rm -rf /` (the command to wipe out a machine), SentinelTrap happily responds *"Deleting system files..."* while in reality, not a single file on the real hard drive is touched.
4. **No Outbound Connections:**  
   The virtual shell disables outbound network requests, meaning the attacker cannot download live malware or use the honeypot as a launchpad to attack someone else.

---

## 8. The Intelligence Engine: Scoring & MITRE ATT&CK

SentinelTrap doesn't just log plain text; it thinks like a professional cybersecurity analyst:

### A. MITRE ATT&CK Framework Mapping
MITRE ATT&CK is the globally recognized encyclopedia of hacker tactics used by military and top security teams (FBI, NSA, SOCs). SentinelTrap automatically tags incoming commands:
- If hacker types `whoami` or `uname -a` ➡️ Tagged as **Discovery / System Information Discovery (`T1082`)**
- If hacker searches for passwords ➡️ Tagged as **Credential Access / OS Credential Dumping (`T1003`)**
- If hacker types `nmap` or `ping` ➡️ Tagged as **Discovery / Network Service Scanning (`T1046`)**
- If hacker executes shell scripts ➡️ Tagged as **Execution / Command and Scripting Interpreter (`T1059`)**

### B. Attacker Threat Score (0 to 100)
Every attacker is scored dynamically:
- Trying simple passwords = Low Risk (20–40/100)
- Reconnaissance commands (`id`, `pwd`, `netstat`) = Medium Risk (40–70/100)
- Attempting root privileges, injecting backdoor malware, or credential harvesting = Critical Risk (80–100/100)

---

## 9. The Live Visual Center: Dashboard, Terminal Replay & 3D Globe

The frontend is a Security Operations Center (SOC) dashboard:

1. **The 3D Cyber Threat Globe:**
   - A 3D WebGL sphere modeled after GitHub’s visual styling.
   - When an attacker connects, an arc flies through space from their country of origin directly into the **Decoy Core in India**.
   - Features plasma lasers with white-hot cores, radar ping ripples at the origin country, and an orbital rotating crosshair reticle over India.
2. **Live Keystroke Replay (Terminal CCTV):**
   - Just like playing a video recording, security analysts can click "Replay" and watch the attacker type their commands letter-by-letter with realistic typing pauses.
3. **Live Ingress Feed:**
   - Powered by WebSockets. No need to refresh the page; whenever an attacker presses Enter on their terminal, the command appears on the web screen in less than 50 milliseconds.

---

## 10. Automated Defense: AutoShun & Firewall Rules

Most honeypots just watch and do nothing. **SentinelTrap fights back automatically.**

- Once an attacker reaches a critical threat score (e.g., above 75/100), SentinelTrap's **AutoShun Engine** triggers.
- It automatically writes ready-to-run firewall rules:
  - Linux `iptables`: `iptables -A INPUT -s <attacker-ip> -j DROP`
  - Linux `ufw`: `ufw deny from <attacker-ip>`
- This ensures that the moment someone reveals themselves as a threat on the decoy, they are permanently blocked from reaching any real server in the organization.

---

## 11. Reports & Exports: PDFs, STIX, and CEF

In corporate environments, cybersecurity teams must submit incident reports to their managers and export data to enterprise systems (like Splunk, IBM QRadar, or Microsoft Sentinel):

1. **Automated PDF Incident Reports:**  
   Clicking one button generates a multi-page, formatted PDF complete with session timelines, attacker IP, geolocation, risk breakdown, and command history.
2. **STIX 2.1 Format:**  
   The international cybersecurity standard format used by threat intelligence sharing platforms.
3. **CEF (Common Event Format):**  
   Standard log format that plugs directly into SIEM tools like Splunk.

---

## 12. Under the Hood: Tech Stack Explained Simply

- **FastAPI (Python):** The high-speed backend engine that receives events from all honeypots and streams them to the website.
- **Paramiko (Python):** The library that simulates a real SSH server and handles network handshakes.
- **SQLite & SQLAlchemy:** The database storing attacker logs, commands, and IP histories.
- **Next.js & React (TypeScript):** The web dashboard that provides a dark-mode military-grade interface.
- **Tailwind CSS:** Modern styling for responsive design.
- **Cobe (WebGL) & HTML5 Canvas:** Powers the 60fps 3D globe animation and laser trajectory calculations.
- **ReportLab:** The Python library that compiles PDF incident reports on the fly.

---

## 13. How to Explain the Entire Project in an Exhibition / Viva (Script)

Use this concise 1-minute explanation if an examiner asks you: **"What does your project do?"**

> *"Respected Sir/Ma'am, traditional cybersecurity tools like firewalls and antivirus wait at the front door and hope they recognize the attacker. But if a hacker uses a new trick, traditional tools fail.*
>
> *Our project, **SentinelTrap**, is an **Active Deception Platform**. Instead of just defending our real servers, we deploy a network of convincing digital decoys across 9 major protocols—including SSH, Web, and Databases.*
>
> *When an attacker finds our decoy, they think they have successfully hacked an unprotected server. In reality, they are trapped inside an isolated in-memory sandbox where our Adaptive Deception Engine feeds them fake passwords and files.*
>
> *While the hacker is busy playing with fake data, SentinelTrap records their keystrokes, maps their behavior to the international MITRE ATT&CK matrix, plots their origin on a live 3D cyber threat globe, and automatically writes firewall rules to ban that hacker from the real company network.*
>
> *In short: SentinelTrap turns the tables on hackers, wasting their time, protecting real data, and giving defenders zero-false-alarm threat intelligence."*
