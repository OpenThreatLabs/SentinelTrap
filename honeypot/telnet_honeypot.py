#!/usr/bin/env python3
"""
SentinelTrap - Multi-Layer Honeypot Framework
IoT Telnet Protocol Honeypot Module

Emulates a BusyBox / OpenWrt Embedded Router Telnet Server (Port 2323) to trap:
- Automated IoT botnet brute-force logins (Mirai, Bashlite, Hajime, Mozi).
- Shell command execution, CPU/system enumeration, and malware payload downloaders (wget, curl, tftp).
Telemetry is logged locally and sent in real time to the central backend API.
"""

import os
import sys
import socket
import threading
import datetime
import json
import uuid
import urllib.request
import urllib.error

# Configuration Defaults
TELNET_PORT = int(os.getenv("TELNET_PORT", 2323))
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/api/events")
EVIDENCE_DIR = os.path.join(os.path.dirname(__file__), "evidence")

os.makedirs(EVIDENCE_DIR, exist_ok=True)

def report_telemetry(event_data):
    """
    Sends captured telemetry event to the Central Backend API.
    Fallback to console logging if backend is offline.
    """
    timestamp = datetime.datetime.utcnow().isoformat()
    log_entry = {
        "timestamp": timestamp,
        **event_data
    }
    
    print(f"[{event_data.get('event_type', 'EVENT')}] {json.dumps(log_entry)}")
    
    try:
        req = urllib.request.Request(
            BACKEND_URL,
            data=json.dumps(log_entry).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            pass
    except Exception:
        # Backend server might be starting up or offline; local logging handles telemetry
        pass


class TelnetHoneypotSession(threading.Thread):
    def __init__(self, client_socket, client_ip, client_port):
        super().__init__()
        self.client_socket = client_socket
        self.client_ip = client_ip
        self.client_port = client_port
        self.session_id = str(uuid.uuid4())
        self.authenticated = False
        self.username = None
        self.password = None
        self.command_history = []
        
    def run(self):
        print(f"[+] [Telnet HP] Connection from {self.client_ip}:{self.client_port} | Session ID: {self.session_id}")
        report_telemetry({
            "session_id": self.session_id,
            "ip_address": self.client_ip,
            "protocol": "TELNET",
            "event_type": "connection_established",
            "input_data": f"Connection from {self.client_ip}:{self.client_port}"
        })
        
        try:
            # Send Telnet Iac negotiate options (basic terminal reset)
            # IAC DO ECHO, IAC WILL ECHO, IAC DO SUPPRESS GO AHEAD
            self.client_socket.sendall(bytes([255, 253, 1, 255, 251, 1, 255, 253, 3]))
            
            # Send Router BusyBox Banner
            banner = (
                "\r\n"
                "BusyBox v1.31.1 (2026-01-15 08:22:11 UTC) multi-call binary.\r\n"
                "Acme-IoT Edge Gateway Router OS v4.2\r\n"
                "User Access Verification\r\n\r\n"
            )
            self.send_data(banner)
            
            # Login Prompt
            self.send_data("login: ")
            self.username = self.read_line().strip()
            
            self.send_data("Password: ")
            self.password = self.read_line().strip()
            
            print(f"[+] [Telnet HP] Auth Captured: User='{self.username}' | Pass='{self.password}' (IP={self.client_ip})")
            report_telemetry({
                "session_id": self.session_id,
                "ip_address": self.client_ip,
                "protocol": "TELNET",
                "event_type": "login_attempt",
                "username_attempted": self.username,
                "password_attempted": self.password,
                "vulnerability_code": "WPH"
            })
            
            # Accept all logins to entice attacker/botnet
            self.authenticated = True
            self.send_data("\r\n\r\nBusyBox v1.31.1 (2026-01-15 08:22:11 UTC) built-in shell (ash)\r\nEnter 'help' for a list of built-in commands.\r\n\r\n")
            
            prompt = "Router-GW# "
            self.send_data(prompt)
            
            while True:
                cmd_line = self.read_line()
                if cmd_line is None:
                    break
                    
                cmd_raw = cmd_line.strip()
                if not cmd_raw:
                    self.send_data(prompt)
                    continue
                    
                print(f"[!] [Telnet HP] Command from {self.client_ip}: {cmd_raw}")
                self.command_history.append(cmd_raw)
                
                # Check for malware downloader probes (Mirai signature: wget / curl / tftp)
                vulnerability_code = None
                if any(pkg in cmd_raw.lower() for pkg in ["wget", "curl", "tftp", "chmod +x", "chmod 777"]):
                    vulnerability_code = "UCE"
                    print(f"[!] [Telnet HP] ALERT: Botnet Malware Downloader Probe Detected ({cmd_raw})")
                elif "cat /etc" in cmd_raw.lower() or "cat /proc" in cmd_raw.lower():
                    vulnerability_code = "SIL"
                elif "enable" in cmd_raw.lower() or "system" in cmd_raw.lower() or "shell" in cmd_raw.lower():
                    vulnerability_code = "HC"

                report_telemetry({
                    "session_id": self.session_id,
                    "ip_address": self.client_ip,
                    "protocol": "TELNET",
                    "event_type": "command_executed",
                    "input_data": cmd_raw,
                    "vulnerability_code": vulnerability_code
                })
                
                if cmd_raw in ["exit", "quit"]:
                    self.send_data("Goodbye.\r\n")
                    break
                
                # Emulate BusyBox shell responses
                response = self.emulate_command(cmd_raw)
                self.send_data(response)
                self.send_data(prompt)
                
        except Exception as e:
            print(f"[-] [Telnet HP] Exception handling {self.client_ip}: {e}")
        finally:
            # Save session log for forensics
            if self.command_history:
                log_path = os.path.join(EVIDENCE_DIR, f"telnet_{self.session_id}.log")
                try:
                    with open(log_path, "w", encoding="utf-8") as f:
                        f.write(f"Session ID: {self.session_id}\nIP: {self.client_ip}\nUser: {self.username}\nPass: {self.password}\n\nCommands:\n")
                        for c in self.command_history:
                            f.write(f"{c}\n")
                except Exception:
                    pass
                    
            self.client_socket.close()
            print(f"[-] [Telnet HP] Session closed: {self.client_ip}")

    def send_data(self, text):
        self.client_socket.sendall(text.encode('utf-8', errors='ignore'))

    def read_line(self):
        buf = ""
        while True:
            try:
                char = self.client_socket.recv(1)
                if not char:
                    return None if not buf else buf
                char_str = char.decode('utf-8', errors='ignore')
                if char_str in ['\r', '\n']:
                    # Consume extra newline if present
                    return buf
                elif char_str == '\x08' or char_str == '\x7f': # Backspace
                    if len(buf) > 0:
                        buf = buf[:-1]
                else:
                    buf += char_str
            except Exception:
                return buf if buf else None

    def emulate_command(self, cmd):
        cmd_parts = cmd.split()
        base_cmd = cmd_parts[0] if cmd_parts else ""
        
        if base_cmd == "whoami":
            return "root\r\n"
        elif base_cmd == "id":
            return "uid=0(root) gid=0(root) groups=0(root)\r\n"
        elif base_cmd == "pwd":
            return "/root\r\n"
        elif base_cmd == "uname" or cmd == "uname -a":
            return "Linux Router-GW 4.14.180-openwrt #0 SMP Tue Jan 15 08:22:11 2026 mips GNU/Linux\r\n"
        elif base_cmd == "help" or base_cmd == "?":
            return "Built-in commands:\r\n------------------\r\n  cat cd chmod cp echo enable help id ifconfig ls mkdir mv ps pwd reboot rm system whoami\r\n\r\n"
        elif base_cmd == "ls" or base_cmd == "dir":
            return "bin  dev  etc  lib  mnt  proc  root  sbin  sys  tmp  usr  var\r\n"
        elif base_cmd == "ps" or cmd.startswith("ps"):
            return (
                "  PID USER       VSZ STAT COMMAND\r\n"
                "    1 root      1200 S    /sbin/init\r\n"
                "    2 root         0 SW   [kthreadd]\r\n"
                "  230 root      1420 S    /usr/sbin/uhttpd -f -p 80\r\n"
                "  512 root      1180 S    /usr/sbin/telnetd -p 2323\r\n"
                "  890 root      1340 S    /usr/sbin/dnsmasq -k\r\n"
            )
        elif base_cmd == "ifconfig":
            return (
                "br-lan    Link encap:Ethernet  HWaddr 00:11:22:33:44:55\r\n"
                "          inet addr:192.168.1.1  Bcast:192.168.1.255  Mask:255.255.255.0\r\n"
                "          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1\r\n\r\n"
                "eth0      Link encap:Ethernet  HWaddr 00:11:22:33:44:56\r\n"
                "          inet addr:10.0.8.22  Bcast:10.0.8.255  Mask:255.255.255.0\r\n"
                "          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1\r\n"
            )
        elif cmd.startswith("cat /proc/cpuinfo"):
            return (
                "system type\t\t: MIPS 24Kc V7.4\r\n"
                "processor\t\t: 0\r\n"
                "cpu model\t\t: MIPS 24Kc V7.4\r\n"
                "BogoMIPS\t\t: 359.62\r\n"
            )
        elif cmd.startswith("cat /etc/passwd"):
            return (
                "root:x:0:0:root:/root:/bin/ash\r\n"
                "admin:x:1000:1000:Admin User:/home/admin:/bin/ash\r\n"
                "support:x:1001:1001:Support Account:/home/support:/bin/ash\r\n"
            )
        elif cmd.startswith("wget") or cmd.startswith("curl") or cmd.startswith("tftp"):
            return "Connecting... 200 OK. Payload downloaded to /tmp/.botnet (simulated honeypot capture)\r\n"
        elif cmd.startswith("chmod"):
            return "\r\n"
        elif base_cmd in ["enable", "system", "shell"]:
            return "Access granted. Administrative shell active.\r\n"
        else:
            return f"-ash: {base_cmd}: not found\r\n"


def main():
    print("============================================================")
    print("      SentinelTrap - IoT Telnet Protocol Honeypot          ")
    print("============================================================")
    print(f"[*] Telnet Port : {TELNET_PORT} (BusyBox OpenWrt Emulation)")
    print(f"[*] Backend     : {BACKEND_URL}")
    print(f"[*] Evidence    : {EVIDENCE_DIR}")
    print("--------------------------------================------------")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind(('0.0.0.0', TELNET_PORT))
        server_socket.listen(50)
        print(f"[*] [Telnet Honeypot] Listening on port {TELNET_PORT}...")
    except Exception as e:
        print(f"[-] [Telnet Honeypot] Bind error on port {TELNET_PORT}: {e}")
        sys.exit(1)

    while True:
        try:
            client_sock, client_addr = server_socket.accept()
            handler = TelnetHoneypotSession(client_sock, client_addr[0], client_addr[1])
            handler.daemon = True
            handler.start()
        except KeyboardInterrupt:
            print("\n[*] Shutting down Telnet Honeypot service...")
            break
        except Exception as e:
            print(f"[-] [Telnet Honeypot] Accept error: {e}")

if __name__ == '__main__':
    main()
