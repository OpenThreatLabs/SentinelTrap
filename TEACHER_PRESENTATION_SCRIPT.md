# 🎤 SentinelTrap — Complete Teacher & Evaluator Presentation Script

> **Target Presentation Time:** 5 to 7 Minutes  
> **Screen Setup:** Split screen (Left: Deployed Vercel Dashboard in Chrome • Right: Terminal / PowerShell or phone ready)

---

## 📌 Scene 0: Introduction & Problem Statement (0:00 – 1:00)

**[Stand confidently, look at your teacher/evaluator, and begin]**

> "Good morning / afternoon Ma'am / Sir and respected evaluators.
>
> Today, we present **SentinelTrap: A Multi-Layer Adaptive Honeypot & Deception Security Platform**.
>
> In modern cybersecurity, traditional perimeter defenses like static firewalls and signature-based IDSs are **fundamentally reactive**. They either drop traffic—giving security analysts zero insight into attacker intentions—or rely on static signatures that fail completely against zero-day exploits.
>
> **SentinelTrap changes this paradigm from passive filtering to active deception.**
> Instead of blocking adversaries, our software lures them into an isolated, in-memory containment sandbox. We feed them deceptive data, monitor every single keystroke in real time, map their techniques to the **MITRE ATT&CK** framework, and autonomously synthesize firewall rules to neutralize the threat."

---

## 🏗️ Scene 1: High-Level Software Architecture (1:00 – 2:00)

**[Point to your screen showing the live deployed dashboard]**

> "Before I demonstrate a live attack, here is how our software architecture works:
>
> 1. **Multi-Protocol Decoy Layer:** We emulate 9 network services—SSH, Telnet, HTTP Web Trap, FTP, MySQL, Redis, SMTP, and DNS.
> 2. **Isolated Virtual File System (VFS):** When an attacker breaches our honeypots, they are contained entirely inside an in-memory virtual shell in Python. No attacker commands can ever touch or damage the host operating system.
> 3. **Behavioral Adaptive Deception Engine:** When an attacker runs commands like `cat /etc/passwd` or searches for AWS credentials, our engine dynamically generates **Canary Honeytokens**—fake credentials that trigger silent alarms when touched.
> 4. **FastAPI & WebSocket Threat Core:** Telemetry is enriched with real-time IP Geolocation, ASN data, and MITRE technique IDs, then broadcasted instantly to our **Next.js SOC Dashboard**."

---

## ⚔️ Scene 2: The Live Attack Demonstration (2:00 – 4:00)

**[Open your terminal side-by-side with your browser showing the hosted dashboard]**

> "Now, let us demonstrate how a real hacker attacks our system, and how SentinelTrap responds in real time.
>
> Watch our live cloud dashboard on the left while I execute the attack on the right."

### Step 1: Initiating the Attack
**[In your terminal, run:]**
```powershell
python live_cloud_attack.py
```
*(Or if using the GUI, go to **Backend Features** and click **"Simulate Ingress Attack"**)*

**[Speak while the terminal runs:]**
> "The attacker has just connected to our honeypot from an external IP (`185.220.101.5`).
> Look at the dashboard: The **Total Sessions** counter instantly incremented, and our **3D Geospatial Threat Globe** has rendered a live trajectory vector from the attacker's origin country directly into our decoy node!"

### Step 2: Reconnaissance & Credential Dumping
**[As the terminal prints `whoami`, `uname -a`, and `cat /etc/passwd`:]**
> "Notice what the hacker is doing:
> First, they ran `whoami` and `uname -a` to check privileges. We safely let them believe they are `root` on an authentic Ubuntu LTS kernel.
> 
> Next, they attempted credential harvesting by dumping `/etc/passwd`.
> Notice that SentinelTrap's **Adaptive Deception Engine** intervened dynamically—injecting fake user accounts like `db_admin` and `backup_svc` to mislead the attacker."

### Step 3: Canary Honeytoken Tripped
**[As the terminal prints `cat /var/backups/credentials.txt`:]**
> "Here is the critical moment: The attacker discovered a backup file containing AWS access keys.
> **This was a planted Canary Honeytoken.**
> Notice the **Alerts** tab on our dashboard—it immediately fired a **CRITICAL TRIPWIRE ALERT** showing that confidential credentials were accessed!"

### Step 4: Destructive Command Neutralized
**[As the terminal prints `sudo rm -rf /`:]**
> "Finally, the frustrated hacker tries a destructive wipe command: `sudo rm -rf /`.
> In a conventional server, this would destroy the operating system. But in SentinelTrap, this ran entirely inside our **RAM-isolated Virtual File System**. Our host system remains completely unharmed."

---

## 📊 Scene 3: Navigating the 5 SOC Dashboard Tabs (4:00 – 5:30)

**[Click through each tab in the top navigation bar smoothly to show the animations]**

### 1. Dashboard Tab
> "On our main dashboard, we see executive security metrics: Total Sessions captured, Deterministic TTP events logged, and Canary tripwires tripped. Below is our real-time active session monitor."

### 2. Sessions Tab
> "In the **Sessions** view, security analysts can inspect every captured intruder.
> We can see their exact IP, city, country, and duration.
> Under **Forensic Command Stream**, every command entered by the adversary is archived chronologically."

### 3. Alerts Tab
> "The **Alerts** tab acts as our real-time Security Incident and Event Management (SIEM) feed.
> It categorizes threats by severity: **CRITICAL** for Canary token exfiltration, **HIGH** for password dumping, and **MEDIUM** for reconnaissance scans."

### 4. Analytics Tab (Show the 3D Threat Globe)
> "In the **Analytics** view, we provide geospatial threat intelligence.
> This WebGL 3D Globe renders dynamic, ray-traced attack arcs tracking adversary locations worldwide.
> Below, our protocol distribution charts break down whether adversaries are targeting SSH, Web, or database services."

### 5. Backend Features & AutoShun Defense Tab
> "Finally, under **Backend Features**, SentinelTrap completes the defense lifecycle with **AutoShun**:
> The software doesn't just watch attacks—it evaluates an **Attacker Risk Score (0 to 100)** and automatically synthesizes a host-level firewall rule:
> `sudo iptables -A INPUT -s 185.220.101.5 -j DROP`
> With one click, the security administrator can also export an executive **Forensic PDF Incident Report**, ready for C-suite briefings or law enforcement evidence."

---

## 🏁 Scene 4: Conclusion & Q&A Readiness (5:30 – 6:00)

**[Conclude firmly]**

> "To summarize:
> SentinelTrap delivers an autonomous, zero-false-positive deception software system. It safely traps adversaries, drains their reconnaissance time, maps their TTPs against MITRE ATT&CK, and automates active incident mitigation.
>
> Thank you, and we are now open to your questions."

---

## 🎯 Likely Teacher Questions & Fast 10-Second Answers

| Potential Teacher Question | Your Crisp, Winning Answer |
| :--- | :--- |
| **Q1: "Is this hardware or pure software?"** | *"It is 100% pure software. It runs as containerized Python ASGI microservices for the backend and a Next.js single-page application for the SOC dashboard."* |
| **Q2: "What if an attacker hacks your honeypot and escapes into your laptop?"** | *"They cannot. Our custom Virtual Shell (VFS) has zero kernel syscall bindings. Commands are parsed in Python string memory; no actual subshell or host `/bin/bash` process is ever spawned for the attacker."* |
| **Q3: "How is this different from a normal firewall like pfSense?"** | *"A firewall is passive: it drops packets, leaving you blind to what the attacker was looking for. SentinelTrap is active deception: any interaction with a honeypot is 100% unauthorized by definition, giving us zero false positives and exposing attacker tools and credentials."* |
| **Q4: "Why did you use WebSockets instead of normal HTTP polling?"** | *"Cyber attacks happen in sub-seconds. Normal HTTP polling introduces lag and server overload. WebSockets allow our backend to push incoming attacker keystrokes to our dashboard in under 15 milliseconds."* |
| **Q5: "Why did you choose deterministic MITRE rules instead of an AI/LLM model?"** | *"In forensic and legal compliance, AI models hallucinate and provide non-reproducible answers. Our deterministic engine maps commands directly to verified MITRE ATT&CK technique IDs with 100% consistency."* |
