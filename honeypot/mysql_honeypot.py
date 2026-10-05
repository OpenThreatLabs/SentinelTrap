import os
import sys
import socket
import threading
import requests
from deception import AdaptiveDeceptionEngine

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
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
            salt1 = b"N{#Q:8Y&"                                 # 8 bytes
            salt2 = b"K7!e)M#OfB12\x00"                         # 13 bytes (12 bytes salt + 1 NUL byte)
            hs_payload = (
                b"\x0a"                                         # Protocol 10
                b"5.7.34-log\x00"                               # Server Version (null-terminated)
                b"\x0d\x00\x00\x00"                             # Connection ID: 13
                + salt1 +                                       # auth-plugin-data-part-1 (8 bytes)
                b"\x00"                                         # filler
                b"\xff\xf7"                                     # capability flags (lower 2 bytes)
                b"\x21"                                         # character set (utf8_general_ci: 33)
                b"\x02\x00"                                     # status flags (SERVER_STATUS_AUTOCOMMIT: 2)
                b"\x7f\x80"                                     # capability flags (upper 2 bytes)
                b"\x15"                                         # auth_plugin_data_len (21 bytes)
                b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # reserved (10 bytes 0x00)
                + salt2 +                                       # auth-plugin-data-part-2 (13 bytes = max(13, 21 - 8))
                b"mysql_native_password\x00"                    # auth_plugin_name (null-terminated)
            )
            handshake_packet = len(hs_payload).to_bytes(3, 'little') + b"\x00" + hs_payload
            client_socket.sendall(handshake_packet)

            # 2. Receive Auth Response Packet from client
            header = client_socket.recv(4)
            auth_payload = b""
            if len(header) == 4:
                pkt_len = int.from_bytes(header[:3], 'little')
                while len(auth_payload) < pkt_len:
                    chunk = client_socket.recv(pkt_len - len(auth_payload))
                    if not chunk:
                        break
                    auth_payload += chunk

            auth_data = header + auth_payload
            username = "root"
            if len(auth_data) > 36:
                # Extract username string from MySQL Auth Packet (offset 36 in HandshakeResponse41)
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
                        "password_attempted": "mysql_probe",
                        "protocol": "MySQL"
                    },
                    timeout=2
                )
                if r.status_code == 200:
                    session_id = r.json().get("session_id")
            except Exception as e:
                print(f"[-] MySQL Session registration failed: {e}")

            # 3. Trigger Deception Response: Return Access Denied Error Packet
            # Error Code 1045 (28000): Access denied for user 'username'@'%' (using password: YES)
            err_msg = f"Access denied for user '{username}'@'%' (using password: YES)".encode('utf-8')
            err_payload = b"\xff\x15\x04#28000" + err_msg
            error_packet = len(err_payload).to_bytes(3, 'little') + b"\x02" + err_payload
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
            try:
                client_socket.shutdown(socket.SHUT_WR)
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
