import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from deception import AdaptiveDeceptionEngine

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
WEB_TRAP_PORT = int(os.getenv("WEB_TRAP_PORT", "8080"))

deception_engine = AdaptiveDeceptionEngine()

class WebTrapHandler(BaseHTTPRequestHandler):
    """
    HTTP Web Trap Honeypot Handler
    Captures web vulnerability scanners, directory traversal, SQL injection attempts,
    and admin login brute-force activity.
    """

    def log_session_and_event(self, path: str, method: str, body: str = "") -> str:
        ip = self.client_address[0]
        session_id = None

        # Register Web Honeypot session with FastAPI backend
        try:
            r = requests.post(
                f"{BACKEND_URL}/api/sessions",
                json={
                    "ip_address": ip,
                    "username_attempted": f"web_{method}",
                    "password_attempted": path[:50]
                },
                timeout=2
            )
            if r.status_code == 200:
                session_id = r.json().get("session_id")
        except Exception:
            pass

        # Log detailed request event
        if session_id:
            try:
                requests.post(
                    f"{BACKEND_URL}/api/sessions/{session_id}/events",
                    json={
                        "event_type": "web_scan_attempt",
                        "input_data": f"{method} {path} | Body: {body[:200]}",
                        "output_data": "HTTP 200 OK / Decoy Web Response"
                    },
                    timeout=2
                )
            except Exception:
                pass

        return session_id

    def do_GET(self):
        session_id = self.log_session_and_event(self.path, "GET")
        
        # Check path against Adaptive Deception Engine
        deception_output, triggered, trap_type = deception_engine.inspect_and_respond(self.path)

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Server", "Apache/2.4.41 (Ubuntu)")
        self.end_headers()

        if triggered and deception_output:
            html = f"<html><body><pre>{deception_output}</pre></body></html>"
        elif "admin" in self.path or "login" in self.path:
            html = """
            <!DOCTYPE html>
            <html>
            <head><title>Corporate Portal - Restricted Access</title></head>
            <body style="background:#0f172a; color:#f8fafc; font-family:sans-serif; text-align:center; padding-top:50px;">
              <h2>Corporate Intranet Authentication Gateway</h2>
              <form method="POST" action="/login" style="display:inline-block; background:#1e293b; padding:20px; border-radius:8px;">
                <input type="text" name="username" placeholder="Employee Username" required style="display:block; margin:10px; padding:8px;"><br>
                <input type="password" name="password" placeholder="Password" required style="display:block; margin:10px; padding:8px;"><br>
                <button type="submit" style="background:#10b981; color:white; border:none; padding:10px 20px; border-radius:4px;">Sign In</button>
              </form>
            </body>
            </html>
            """
        else:
            html = "<html><body><h1>Index of /</h1><hr><ul><li><a href='/admin'>admin/</a></li><li><a href='/config.json'>config.json</a></li></ul></body></html>"

        self.wfile.write(html.encode("utf-8"))

        if session_id:
            try:
                requests.patch(f"{BACKEND_URL}/api/sessions/{session_id}", timeout=2)
            except Exception:
                pass

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8', errors='ignore')
        
        session_id = self.log_session_and_event(self.path, "POST", body)

        self.send_response(401)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body><h3>401 Unauthorized: Credentials logged for security review.</h3></body></html>")

        if session_id:
            try:
                requests.patch(f"{BACKEND_URL}/api/sessions/{session_id}", timeout=2)
            except Exception:
                pass

def main():
    print(f"[*] HTTP Web Trap Honeypot listening on port {WEB_TRAP_PORT}...")
    server = HTTPServer(("0.0.0.0", WEB_TRAP_PORT), WebTrapHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopping Web Trap server.")
        server.server_close()

if __name__ == '__main__':
    main()
