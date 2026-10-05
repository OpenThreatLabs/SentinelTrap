# ⚔️ SentinelTrap — Manual Live Attack Demonstration Cheat-Sheet

> **Target Setup:** Machine 1 (Defense Server at `192.168.1.4`) & Machine 2 (Attacker Laptop / Kali Linux)  
> **Format:** Run each command manually one by one in Machine 2's terminal while faculty watches Machine 1's Dashboard.

---

## 🚀 Pre-Demo Checklist (30 seconds before presentation)

1. **On Machine 1 (Defense Laptop - `192.168.1.4`):**
   - Open PowerShell and start the project:
     ```powershell
     python run_all.py
     ```
   - Open the Dashboard in Chrome/Edge: **`http://localhost:3000`** (Maximize it on screen / projector).

2. **On Machine 2 (Attacker Laptop / Kali Linux):**
   - Open your terminal.

---

## 🎯 Step-by-Step Manual Attack Commands

### Command 1: The SSH Break-in
In Machine 2's terminal, type:
```bash
ssh root@192.168.1.4 -p 2222
```
- **Password Prompt:** Type anything (e.g., `admin123` or `toor`) and press **Enter**.
- **What happens:** The honeypot accepts the password and drops you into the Ubuntu prompt:
  ```text
  Welcome to Ubuntu 22.04.1 LTS (GNU/Linux 5.15.0-52-generic x86_64)
  root@ubuntu-srv-01:~#
  ```
- 🗣️ **Tell Teacher:**  
  *"Look at Machine 1's dashboard—the moment I pressed Enter, a new active session appeared on our Sessions sidebar and the 3D Threat Globe with Machine 2's IP!"*

---

### Command 2: Reconnaissance (Who Am I & OS Architecture Check)
In the honeypot shell, type:
```bash
whoami
```
*(Returns: `root`)*

Then type:
```bash
uname -a
```
*(Returns: `Linux ubuntu-srv-01 5.15.0-52-generic x86_64`)*

- 🗣️ **Tell Teacher:**  
  *"The hacker checks privileges. We safely let them believe they are root on an authentic Ubuntu LTS kernel."*

---

### Command 3: Credential Harvesting (Testing the Adaptive Deception Engine)
In the honeypot shell, type:
```bash
cat /etc/passwd
```
- **What happens:** The screen prints realistic Linux user accounts, but with injected decoy users (`db_admin`, `backup_svc`).
- 🗣️ **Tell Teacher:**  
  *"The hacker tries to dump user accounts. Notice how our Adaptive Deception Engine dynamically generates decoy credentials to mislead the attacker."*

---

### Command 4: Finding Sensitive Files (Triggering the CANARY TRIPWIRE)
In the honeypot shell, type:
```bash
ls -la /var/backups
```
*(You will see a file called `credentials.txt`)*

Now read the credentials:
```bash
cat /var/backups/credentials.txt
```
- **What happens:** It displays a planted fake AWS Secret Key (`AWS_SECRET_ACCESS_KEY=...`).
- 🗣️ **Tell Teacher:**  
  *"Look at Machine 1's screen right now! Under the **Alerts** tab, a **CRITICAL TRIPWIRE ALERT** just fired. The honeypot knows the attacker touched our planted honeytoken!"*

---

### Command 5: Attempting Database Exploitation
In the honeypot shell, type:
```bash
mysql -u root -p
```
- **What happens:** It returns an authentic MySQL binary connection error.
- 🗣️ **Tell Teacher:**  
  *"The hacker attempts to breach an internal MySQL database. Our virtual shell intercepts the call and serves a deceptive handshake error to drain their time."*

---

### Command 6: Destructive Sabotage (Proving Sandbox Safety)
In the honeypot shell, type:
```bash
sudo rm -rf / --no-preserve-root
```
- **What happens:** The command executes safely without affecting the host.
- 🗣️ **Tell Teacher:**  
  *"The hacker attempts a destructive wipe command. But because SentinelTrap operates inside an isolated in-memory Virtual File System (VFS), our real host machine remains completely untouched and safe."*

---

### Command 7: Disconnect
In the honeypot shell, type:
```bash
exit
```
- **What happens:** Connection closes cleanly.
- 🗣️ **Tell Teacher:**  
  *"The session status on Machine 1 instantly changes to Terminated / Closed."*

---

## 🏆 The Grand Finale on Machine 1 (Show Evaluators the Proof)

Switch to Machine 1's browser and show:

1. **Sessions Tab:**
   - Click on Machine 2's session.
   - Point to the **Forensic Command Stream** showing the exact list of commands you just typed.
   - Click **"Export PDF"** $\rightarrow$ Show the auto-generated forensic report with MITRE ATT&CK technique IDs (`T1003`, `T1059`).
2. **Backend Features Tab:**
   - Show the **AutoShun Firewall** card:  
     Point out that SentinelTrap automatically generated an `iptables` rule to permanently block Machine 2's IP:
     ```bash
     sudo iptables -A INPUT -s 192.168.1.X -j DROP
     ```
