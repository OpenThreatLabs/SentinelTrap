#!/usr/bin/env python3
"""
SentinelTrap - Multi-Layer Honeypot Framework
Web Admin Portal & REST API Honeypot Module (Ports 8080 & 8081)

Emulates an Enterprise Admin Console, Router Management Gateway, and Microservice REST API.
Traps:
- Web login brute-force attempts (WPH)
- Path traversal probes (/download?file=../../etc/passwd) -> UFH
- SSRF & Cloud Metadata credential harvesting (/api/v1/fetch?url=http://169.254.169.254) -> SSRF
- Exposed secrets & honeytokens (/.env, /config.json) -> HC / SIL
- SQL injection in login & search inputs (' OR 1=1 --) -> PSI / IQC
"""

import os
import sys
import json
import uuid
import datetime
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import threading

import deception

WEB_PORT = int(os.getenv("WEB_PORT", 8080))
API_PORT = int(os.getenv("API_PORT", 8081))
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/api/events")

def report_telemetry(event_data):
    """Sends captured web telemetry to central backend API."""
    timestamp = datetime.datetime.utcnow().isoformat()
    log_entry = {"timestamp": timestamp, **event_data}
    print(f"[{event_data.get('event_type', 'WEB_EVENT')}] {json.dumps(log_entry)}")
    try:
        req = urllib.request.Request(
            BACKEND_URL,
            data=json.dumps(log_entry).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            pass
    except Exception:
        pass


class WebHoneypotHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass # Suppress default HTTP console spam

    def do_GET(self):
        client_ip = self.client_address[0]
        session_id = str(uuid.uuid4())
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        print(f"[!] [Web HP] GET {self.path} from {client_ip}")

        # Check Path Traversal (UFH)
        if ".." in self.path or "etc/passwd" in self.path or "etc/shadow" in self.path:
            report_telemetry({
                "session_id": session_id,
                "ip_address": client_ip,
                "protocol": "HTTP",
                "event_type": "path_traversal_attempt",
                "input_data": f"GET {self.path}",
                "vulnerability_code": "UFH"
            })
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write("root:x:0:0:root:/root:/bin/bash\nadmin:x:1000:1000:admin:/home/admin:/bin/bash\n".encode('utf-8'))
            return

        # Check Exposed Secrets (HC / SIL)
        if path in ["/.env", "/config.json", "/aws_credentials"]:
            report_telemetry({
                "session_id": session_id,
                "ip_address": client_ip,
                "protocol": "HTTP",
                "event_type": "secret_harvesting_attempt",
                "input_data": f"GET {path}",
                "vulnerability_code": "HC"
            })
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(deception.get_fake_env().encode('utf-8'))
            return

        # Check SSRF / Cloud Metadata Probe (SSRF)
        if path == "/api/v1/fetch" or "url" in query:
            target_url = query.get("url", [""])[0]
            report_telemetry({
                "session_id": session_id,
                "ip_address": client_ip,
                "protocol": "HTTP",
                "event_type": "ssrf_attempt",
                "input_data": f"GET {self.path} (target={target_url})",
                "vulnerability_code": "SSRF"
            })
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(deception.get_fake_aws_credentials().encode('utf-8'))
            return

        # Serve Login Page
        report_telemetry({
            "session_id": session_id,
            "ip_address": client_ip,
            "protocol": "HTTP",
            "event_type": "page_view",
            "input_data": f"GET {self.path}"
        })
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Acme Corp - Cloud Gateway Admin Portal</title>
            <style>
                body { background: #0f172a; color: #f8fafc; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                .card { background: #1e293b; padding: 40px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 360px; border: 1px solid #334155; }
                h2 { color: #38bdf8; margin-top: 0; }
                input { width: 100%; padding: 10px; margin: 10px 0; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; }
                button { width: 100%; padding: 12px; background: #0284c7; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 10px; }
                button:hover { background: #0369a1; }
                .footer { font-size: 12px; color: #64748b; margin-top: 20px; text-align: center; }
            </style>
        </head>
        <body>
            <!-- TODO: Dev bypass creds: admin / P@ssw0rd2026_Prod -->
            <div class="card">
                <h2>Acme Gateway v4.2</h2>
                <p style="color:#94a3b8; font-size:14px;">Secure Administrative Single Sign-On</p>
                <form action="/login" method="POST">
                    <input type="text" name="username" placeholder="Username / Email" required /><br/>
                    <input type="password" name="password" placeholder="Password" required /><br/>
                    <button type="submit">Sign In</button>
                </form>
                <div class="footer">Restricted Access. Unauthorized probes monitored.</div>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode('utf-8'))

    def do_POST(self):
        client_ip = self.client_address[0]
        session_id = str(uuid.uuid4())
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8', errors='ignore')

        print(f"[!] [Web HP] POST {self.path} from {client_ip} | Body: {post_data}")

        # Check for SQL Injection (PSI / IQC)
        vulnerability_code = "WPH"
        if "'" in post_data or "OR 1=1" in post_data.upper() or "UNION SELECT" in post_data.upper():
            vulnerability_code = "PSI"
            print(f"[!] [Web HP] ALERT: SQL Injection Exploit Detected ({post_data})")
        elif "cat " in post_data or "whoami" in post_data:
            vulnerability_code = "UCE"

        report_telemetry({
            "session_id": session_id,
            "ip_address": client_ip,
            "protocol": "HTTP",
            "event_type": "login_attempt" if self.path == "/login" else "post_payload",
            "input_data": f"POST {self.path} - Payload: {post_data}",
            "username_attempted": post_data[:50],
            "vulnerability_code": vulnerability_code
        })

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        response_html = """
        <!DOCTYPE html>
        <html>
        <body style="background:#0f172a; color:#f43f5e; font-family:sans-serif; text-align:center; padding-top:100px;">
            <h2>403 Access Denied</h2>
            <p style="color:#94a3b8;">Invalid credentials or security policy violation detected.</p>
            <a href="/" style="color:#38bdf8;">Return to Login</a>
        </body>
        </html>
        """
        self.wfile.write(response_html.encode('utf-8'))


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


def run_web_honeypot(port):
    server = ThreadedHTTPServer(('0.0.0.0', port), WebHoneypotHandler)
    print(f"[*] [Web Honeypot] Listening on http://0.0.0.0:{port}...")
    server.serve_forever()


def main():
    print("============================================================")
    print("      SentinelTrap - Web Admin & API Protocol Honeypot      ")
    print("============================================================")
    print(f"[*] Web Port : {WEB_PORT} (Acme Cloud Admin Portal)")
    print(f"[*] API Port : {API_PORT} (Microservice REST Gateway)")
    print(f"[*] Backend  : {BACKEND_URL}")
    print("--------------------------------================------------")

    web_thread = threading.Thread(target=run_web_honeypot, args=(WEB_PORT,), daemon=True)
    api_thread = threading.Thread(target=run_web_honeypot, args=(API_PORT,), daemon=True)

    web_thread.start()
    api_thread.start()

    try:
        while True:
            web_thread.join(timeout=1.0)
            api_thread.join(timeout=1.0)
    except KeyboardInterrupt:
        print("\n[*] Shutting down Web & API Honeypot services...")
        sys.exit(0)

if __name__ == '__main__':
    main()
