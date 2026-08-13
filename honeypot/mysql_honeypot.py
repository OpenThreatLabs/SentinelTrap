import os
import sys
import socket
import threading
import requests
from deception import AdaptiveDeceptionEngine

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))

deception_engine = AdaptiveDeceptionEngine()

class MySQLHoneypotServer:
    """
    MySQL Database Honeypot Server
    Exposes a decoy MySQL database node (Port 3306) to capture automated database scanners,
    credential brute-forcing, and unauthorized SQL dump attempts.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = MYSQL_PORT):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def handle_client(self, client_socket: socket.socket, client_ip: str):
        session_id = None
        try:
            # 1. Send simulated MySQL Handshake Initialization Packet (Protocol v10)
            # MySQL Server Version: 5.7.34-log
            handshake_packet = (
                b"\x4a\x00\x00\x00\x0a\x35\x2e\x37\x2e\x33\x34\x2d\x6c\x6f\x67\x00"
                b"\x0d\x00\x00\x00\x4e\x7b\x23\x51\x3a\x38\x59\x26\x00\xff\xf7\x21"
                b"\x02\x00\x7f\x80\x15\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x4b"
                b"\x37\x21\x65\x29\x4d\x23\x4f\x66\x42\x00\x6d\x79\x73\x71\x6c\x5f"
                b"\x6e\x61\x74\x69\x76\x65\x5f\x70\x61\x73\x73\x77\x6f\x72\x64\x00"
            )
            client_socket.sendall(handshake_packet)

            # 2. Receive Auth Response Packet from client
            auth_data = client_socket.recv(1024)
            username = "root"
            if len(auth_data) > 36:
                # Extract username string from MySQL Auth Packet
                try:
                    user_bytes = auth_data[36:].split(b'\x00')[0]
                    if user_bytes:
                        username = user_bytes.decode('utf-8', errors='ignore')
                except Exception:
                    pass

            print(f"[+] MySQL Connection Attempt: IP={client_ip} | User={username}")

            # Register session with FastAPI Backend
            try:
                r = requests.post(
                    f"{BACKEND_URL}/api/sessions",
                    json={
                        "ip_address": client_ip,
                        "username_attempted": f"mysql_{username}",
                        "password_attempted": "mysql_probe"
                    },
                    timeout=2
                )
                if r.status_code == 200:
                    session_id = r.json().get("session_id")
            except Exception as e:
                print(f"[-] MySQL Session registration failed: {e}")

            # 3. Trigger Deception Response: Return Access Denied Error Packet
            # Error Code 1045 (28000): Access denied for user 'username'@'ip'
            error_packet = (
                b"\x44\x00\x00\x02\xff\x15\x04\x23\x32\x38\x30\x30\x30\x41\x63\x63"
                b"\x65\x73\x73\x20\x64\x65\x6e\x69\x65\x64\x20\x66\x6f\x72\x20\x75"
                b"\x73\x65\x72\x20\x27\x72\x6f\x6f\x74\x27\x40\x27\x25\x27\x20\x28"
                b"\x75\x73\x69\x6e\x67\x20\x70\x61\x73\x73\x77\x6f\x72\x64\x3a\x20"
                b"\x59\x45\x53\x29\x00"
            )
            client_socket.sendall(error_packet)

            # Log Deception Trigger Event
            if session_id:
                try:
                    requests.post(
                        f"{BACKEND_URL}/api/sessions/{session_id}/events",
                        json={
                            "event_type": "deception_triggered",
                            "input_data": f"MySQL Connect Request (user: {username})",
                            "output_data": "Decoy Response: ERROR 1045 (28000) Access Denied"
                        },
                        timeout=2
                    )
                except Exception:
                    pass

        except Exception as e:
            print(f"[-] MySQL Client error {client_ip}: {e}")
        finally:
            if session_id:
                try:
                    requests.patch(f"{BACKEND_URL}/api/sessions/{session_id}", timeout=2)
                except Exception:
                    pass
            client_socket.close()

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(100)
            print(f"[*] MySQL Database Honeypot listening on port {self.port}...")
            while True:
                client_sock, (ip, port) = self.server_socket.accept()
                print(f"[+] Incoming MySQL connection from {ip}:{port}")
                t = threading.Thread(target=self.handle_client, args=(client_sock, ip))
                t.daemon = True
                t.start()
        except KeyboardInterrupt:
            print("\n[*] Stopping MySQL Honeypot server.")
        except Exception as e:
            print(f"[-] MySQL Server error: {e}")
            sys.exit(1)

if __name__ == '__main__':
    server = MySQLHoneypotServer()
    server.start()
