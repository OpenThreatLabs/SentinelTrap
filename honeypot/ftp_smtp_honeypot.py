#!/usr/bin/env python3
"""
SentinelTrap - Multi-Layer Honeypot Framework
FTP & SMTP Protocol Honeypot Module

Emulates ProFTPD (Port 2121) and Postfix Mail Server (Port 2525) to trap:
- FTP brute-force logins, directory traversal, decoy file downloads, and malware uploads.
- SMTP open-relay scanning, spam injection, and phishing payload analysis.
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
FTP_PORT = int(os.getenv("FTP_PORT", 2121))
SMTP_PORT = int(os.getenv("SMTP_PORT", 2525))
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

# ============================================================================
# FTP HONEYPOT IMPLEMENTATION (ProFTPD 1.3.5 Emulation)
# ============================================================================

class FTPHoneypotSession(threading.Thread):
    def __init__(self, client_socket, client_ip, client_port):
        super().__init__()
        self.client_socket = client_socket
        self.client_ip = client_ip
        self.client_port = client_port
        self.session_id = str(uuid.uuid4())
        self.authenticated = False
        self.username = "anonymous"
        self.current_dir = "/home/ftpuser"
        self.mode = "ASCII"
        
    def run(self):
        print(f"[+] [FTP HP] Connection from {self.client_ip}:{self.client_port} | Session ID: {self.session_id}")
        report_telemetry({
            "session_id": self.session_id,
            "ip_address": self.client_ip,
            "protocol": "FTP",
            "event_type": "connection_established",
            "input_data": f"Connection from {self.client_ip}:{self.client_port}"
        })
        
        try:
            # Send ProFTPD banner
            self.send_resp("220 ProFTPD 1.3.5 Server (Acme FTP Gateway) [::ffff:127.0.0.1]")
            
            while True:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                    
                line = data.decode('utf-8', errors='ignore').strip()
                if not line:
                    continue
                    
                parts = line.split(' ', 1)
                cmd = parts[0].upper()
                arg = parts[1] if len(parts) > 1 else ""
                
                print(f"[!] [FTP HP] Command from {self.client_ip}: {cmd} {arg}")
                
                # Log command telemetry
                report_telemetry({
                    "session_id": self.session_id,
                    "ip_address": self.client_ip,
                    "protocol": "FTP",
                    "event_type": "command_executed",
                    "input_data": f"{cmd} {arg}".strip(),
                    "vulnerability_code": "UFH" if ".." in arg else None
                })
                
                if cmd == "USER":
                    self.username = arg
                    self.send_resp(f"331 Password required for {self.username}")
                elif cmd == "PASS":
                    self.authenticated = True
                    print(f"[+] [FTP HP] Auth Captured: User={self.username} | Pass={arg}")
                    report_telemetry({
                        "session_id": self.session_id,
                        "ip_address": self.client_ip,
                        "protocol": "FTP",
                        "event_type": "login_attempt",
                        "username_attempted": self.username,
                        "password_attempted": arg,
                        "vulnerability_code": "WPH"
                    })
                    self.send_resp("230 User logged in, proceed")
                elif cmd == "SYST":
                    self.send_resp("215 UNIX Type: L8")
                elif cmd == "PWD":
                    self.send_resp(f'257 "{self.current_dir}" is current directory')
                elif cmd == "CWD":
                    if ".." in arg:
                        self.send_resp("550 Directory traversal prohibited")
                    else:
                        self.current_dir = os.path.normpath(os.path.join(self.current_dir, arg))
                        self.send_resp("250 CWD command successful")
                elif cmd in ["TYPE", "MODE", "STRU"]:
                    self.send_resp("200 Command OK")
                elif cmd == "PASV":
                    self.send_resp("227 Entering Passive Mode (127,0,0,1,195,80)")
                elif cmd == "PORT":
                    self.send_resp("200 PORT command successful")
                elif cmd in ["LIST", "NLST"]:
                    self.send_resp("150 Opening ASCII mode data connection for file list")
                    # Emulate decoy directory list
                    decoy_listing = (
                        "-rw-r--r--   1 root     root       1048576 Jul 28 10:00 backup_2026.zip\r\n"
                        "-rw-r--r--   1 root     root          4096 Jul 28 10:15 db_config.php\r\n"
                        "-rw-r--r--   1 root     root         524288 Jul 28 11:30 customer_data.csv\r\n"
                    )
                    self.send_resp("226 Transfer complete")
                elif cmd == "RETR":
                    filename = arg
                    print(f"[!] [FTP HP] Attacker attempting download of decoy file: {filename}")
                    report_telemetry({
                        "session_id": self.session_id,
                        "ip_address": self.client_ip,
                        "protocol": "FTP",
                        "event_type": "deception_triggered",
                        "input_data": f"RETR {filename}",
                        "vulnerability_code": "SIL"
                    })
                    self.send_resp(f"550 {filename}: Permission denied or honeytoken alert triggered")
                elif cmd == "STOR":
                    filename = os.path.basename(arg)
                    print(f"[!] [FTP HP] Attacker attempting file upload: {filename}")
                    report_telemetry({
                        "session_id": self.session_id,
                        "ip_address": self.client_ip,
                        "protocol": "FTP",
                        "event_type": "file_upload_attempt",
                        "input_data": f"STOR {filename}",
                        "vulnerability_code": "UFH"
                    })
                    self.send_resp("150 Ok to send data")
                    self.send_resp("226 File upload complete (safely quarantined)")
                elif cmd == "QUIT":
                    self.send_resp("221 Goodbye.")
                    break
                else:
                    self.send_resp(f"500 '{cmd}': command not understood")
                    
        except Exception as e:
            print(f"[-] [FTP HP] Exception with {self.client_ip}: {e}")
        finally:
            self.client_socket.close()
            print(f"[-] [FTP HP] Session closed: {self.client_ip}")

    def send_resp(self, msg):
        self.client_socket.sendall((msg + "\r\n").encode('utf-8'))


def run_ftp_honeypot():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind(('0.0.0.0', FTP_PORT))
        server_socket.listen(50)
        print(f"[*] [FTP Honeypot] Listening on port {FTP_PORT} (ProFTPD Emulation)...")
    except Exception as e:
        print(f"[-] [FTP Honeypot] Failed to bind port {FTP_PORT}: {e}")
        return
        
    while True:
        try:
            client_sock, client_addr = server_socket.accept()
            handler = FTPHoneypotSession(client_sock, client_addr[0], client_addr[1])
            handler.daemon = True
            handler.start()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[-] [FTP Honeypot] Accept error: {e}")

# ============================================================================
# SMTP HONEYPOT IMPLEMENTATION (Postfix Mail Server Emulation)
# ============================================================================

class SMTPHoneypotSession(threading.Thread):
    def __init__(self, client_socket, client_ip, client_port):
        super().__init__()
        self.client_socket = client_socket
        self.client_ip = client_ip
        self.client_port = client_port
        self.session_id = str(uuid.uuid4())
        self.mail_from = ""
        self.rcpt_to = []
        self.in_data_mode = False
        self.data_buffer = []
        
    def run(self):
        print(f"[+] [SMTP HP] Connection from {self.client_ip}:{self.client_port} | Session ID: {self.session_id}")
        report_telemetry({
            "session_id": self.session_id,
            "ip_address": self.client_ip,
            "protocol": "SMTP",
            "event_type": "connection_established",
            "input_data": f"Connection from {self.client_ip}:{self.client_port}"
        })
        
        try:
            # Send Postfix banner
            self.send_resp("220 mail.acmegroup-prod.com ESMTP Postfix (Ubuntu)")
            
            while True:
                data = self.client_socket.recv(2048)
                if not data:
                    break
                    
                line = data.decode('utf-8', errors='ignore').rstrip('\r\n')
                if not line:
                    continue
                    
                if self.in_data_mode:
                    if line == ".":
                        self.in_data_mode = False
                        email_body = "\n".join(self.data_buffer)
                        print(f"[!] [SMTP HP] Captured Email Payload from {self.client_ip}:\n--- START ---\n{email_body[:300]}\n--- END ---")
                        
                        # Forensic file save
                        evidence_filename = os.path.join(EVIDENCE_DIR, f"smtp_{self.session_id}.eml")
                        with open(evidence_filename, "w", encoding="utf-8") as f:
                            f.write(email_body)
                            
                        report_telemetry({
                            "session_id": self.session_id,
                            "ip_address": self.client_ip,
                            "protocol": "SMTP",
                            "event_type": "email_payload_captured",
                            "mail_from": self.mail_from,
                            "rcpt_to": self.rcpt_to,
                            "input_data": email_body[:1000],
                            "evidence_file": evidence_filename,
                            "vulnerability_code": "SIL"
                        })
                        self.send_resp("250 2.0.0 Ok: queued as 4F92B801A9")
                        self.data_buffer = []
                    else:
                        self.data_buffer.append(line)
                    continue
                    
                parts = line.split(' ', 1)
                cmd = parts[0].upper()
                arg = parts[1] if len(parts) > 1 else ""
                
                print(f"[!] [SMTP HP] Command from {self.client_ip}: {cmd} {arg}")
                
                if cmd in ["HELO", "EHLO"]:
                    self.send_resp(f"250-mail.acmegroup-prod.com Hello [{self.client_ip}]\r\n250-SIZE 10485760\r\n250-8BITMIME\r\n250-AUTH LOGIN PLAIN\r\n250 OK")
                elif cmd.startswith("MAIL FROM:"):
                    self.mail_from = line[10:].strip('<> ')
                    self.send_resp("250 2.1.0 Ok")
                elif cmd.startswith("RCPT TO:"):
                    rcpt = line[8:].strip('<> ')
                    self.rcpt_to.append(rcpt)
                    # Report open relay probe
                    report_telemetry({
                        "session_id": self.session_id,
                        "ip_address": self.client_ip,
                        "protocol": "SMTP",
                        "event_type": "open_relay_probe",
                        "input_data": f"RCPT TO: <{rcpt}>",
                        "vulnerability_code": "UCE"
                    })
                    self.send_resp("250 2.1.5 Ok")
                elif cmd == "DATA":
                    self.in_data_mode = True
                    self.send_resp("354 End data with <CR><LF>.<CR><LF>")
                elif cmd == "RSET":
                    self.mail_from = ""
                    self.rcpt_to = []
                    self.send_resp("250 2.0.0 Ok")
                elif cmd == "NOOP":
                    self.send_resp("250 2.0.0 Ok")
                elif cmd == "AUTH":
                    print(f"[!] [SMTP HP] Auth Attempt Captured from {self.client_ip}: {arg}")
                    report_telemetry({
                        "session_id": self.session_id,
                        "ip_address": self.client_ip,
                        "protocol": "SMTP",
                        "event_type": "login_attempt",
                        "input_data": f"AUTH {arg}",
                        "vulnerability_code": "WPH"
                    })
                    self.send_resp("334 VXNlcm5hbWU6") # Base64 'Username:'
                elif cmd == "QUIT":
                    self.send_resp("221 2.0.0 Bye")
                    break
                else:
                    self.send_resp("500 5.5.2 Error: command not recognized")
                    
        except Exception as e:
            print(f"[-] [SMTP HP] Exception with {self.client_ip}: {e}")
        finally:
            self.client_socket.close()
            print(f"[-] [SMTP HP] Session closed: {self.client_ip}")

    def send_resp(self, msg):
        self.client_socket.sendall((msg + "\r\n").encode('utf-8'))


def run_smtp_honeypot():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind(('0.0.0.0', SMTP_PORT))
        server_socket.listen(50)
        print(f"[*] [SMTP Honeypot] Listening on port {SMTP_PORT} (Postfix Emulation)...")
    except Exception as e:
        print(f"[-] [SMTP Honeypot] Failed to bind port {SMTP_PORT}: {e}")
        return
        
    while True:
        try:
            client_sock, client_addr = server_socket.accept()
            handler = SMTPHoneypotSession(client_sock, client_addr[0], client_addr[1])
            handler.daemon = True
            handler.start()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[-] [SMTP Honeypot] Accept error: {e}")

# ============================================================================
# MAIN LAUNCHER
# ============================================================================

def main():
    print("============================================================")
    print("      SentinelTrap - FTP & SMTP Dual Protocol Honeypot      ")
    print("============================================================")
    print(f"[*] FTP Port  : {FTP_PORT} (ProFTPD 1.3.5)")
    print(f"[*] SMTP Port : {SMTP_PORT} (Postfix Mail Relay)")
    print(f"[*] Backend   : {BACKEND_URL}")
    print(f"[*] Evidence  : {EVIDENCE_DIR}")
    print("--------------------------------================------------")

    ftp_thread = threading.Thread(target=run_ftp_honeypot, daemon=True)
    smtp_thread = threading.Thread(target=run_smtp_honeypot, daemon=True)

    ftp_thread.start()
    smtp_thread.start()

    try:
        while True:
            ftp_thread.join(timeout=1.0)
            smtp_thread.join(timeout=1.0)
    except KeyboardInterrupt:
        print("\n[*] Shutting down FTP & SMTP Honeypot services...")
        sys.exit(0)

if __name__ == '__main__':
    main()
