import os
import socket
import sys
import threading
import requests
from shell import VirtualShellSession

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
TELNET_PORT = int(os.getenv("TELNET_PORT", "2223"))

class TelnetHoneypotServer:
    """
    Telnet Honeypot Server
    Expands SentinelTrap into a Multi-Protocol Honeypot platform by capturing
    Telnet (Port 23/2223) attacks, botnet probes (e.g. Mirai), and credential brute-force attempts.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = TELNET_PORT):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def handle_client(self, client_socket: socket.socket, client_ip: str):
        session_id = None
        try:
            # Handle basic Telnet negotiation bytes (Suppress Go Ahead, Echo off for password)
            client_socket.sendall(bytes([255, 251, 1, 255, 251, 3]))

            # Prompt for login credentials
            client_socket.sendall(b"\r\nprod-web-srv-01 login: ")
            username = client_socket.recv(1024).decode('utf-8', errors='ignore').strip()

            client_socket.sendall(b"Password: ")
            password = client_socket.recv(1024).decode('utf-8', errors='ignore').strip()

            print(f"[+] Telnet Login Attempt: IP={client_ip} | User={username} | Pass={password}")

            # Register session with FastAPI backend
            try:
                r = requests.post(
                    f"{BACKEND_URL}/api/sessions",
                    json={
                        "ip_address": client_ip,
                        "username_attempted": username,
                        "password_attempted": password
                    },
                    timeout=3
                )
                if r.status_code == 200:
                    session_id = r.json().get("session_id")
            except Exception as e:
                print(f"[-] Telnet session backend registration failed: {e}")

            # Welcome banner
            client_socket.sendall(b"\r\nWelcome to Ubuntu 22.04.1 LTS (GNU/Linux 5.15.0-52-generic x86_64)\r\n\r\n")

            # Initialize virtual shell session handler
            shell = VirtualShellSession(session_id, BACKEND_URL)
            client_socket.sendall(shell.get_prompt().encode('utf-8'))

            buf = ""
            while True:
                data = client_socket.recv(1024).decode('utf-8', errors='ignore')
                if not data:
                    break

                for char in data:
                    if char in ['\r', '\n']:
                        client_socket.sendall(b"\r\n")
                        response = shell.execute_command(buf)
                        if response == "exit":
                            break
                        elif response:
                            formatted = response.replace('\n', '\r\n')
                            client_socket.sendall(formatted.encode('utf-8'))

                        buf = ""
                        client_socket.sendall(shell.get_prompt().encode('utf-8'))
                    elif char == '\x7f' or ord(char) == 8: # Backspace
                        if len(buf) > 0:
                            buf = buf[:-1]
                            client_socket.sendall(b"\b \b")
                    else:
                        buf += char
                        client_socket.sendall(char.encode('utf-8'))
                else:
                    continue
                break

        except Exception as e:
            print(f"[-] Error handling Telnet client {client_ip}: {e}")
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
            print(f"[*] Telnet Honeypot listening on port {self.port}...")
            while True:
                client_sock, (ip, port) = self.server_socket.accept()
                print(f"[+] Incoming Telnet connection from {ip}:{port}")
                t = threading.Thread(target=self.handle_client, args=(client_sock, ip))
                t.daemon = True
                t.start()
        except KeyboardInterrupt:
            print("\n[*] Stopping Telnet Honeypot server.")
        except Exception as e:
            print(f"[-] Telnet Server error: {e}")
            sys.exit(1)

if __name__ == '__main__':
    server = TelnetHoneypotServer()
    server.start()
