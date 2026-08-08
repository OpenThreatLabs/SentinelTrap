import os
import sys
import socket
import threading
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FTP_PORT = int(os.getenv("FTP_PORT", "2121"))

class FTPHoneypotServer:
    """
    FTP Honeypot Server
    Captures automated FTP brute-force attacks, anonymous login probes,
    and malicious file upload/download attempts.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = FTP_PORT):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def handle_client(self, client_socket: socket.socket, client_ip: str):
        session_id = None
        username = "anonymous"
        password = ""

        try:
            # Banner greeting
            client_socket.sendall(b"220 (vsFTPd 3.0.3 - Production File Server)\r\n")

            while True:
                data = client_socket.recv(1024).decode('utf-8', errors='ignore')
                if not data:
                    break

                cmd_line = data.strip()
                parts = cmd_line.split(" ", 1)
                cmd = parts[0].upper()
                arg = parts[1] if len(parts) > 1 else ""

                if cmd == "USER":
                    username = arg
                    client_socket.sendall(b"331 Please specify the password.\r\n")

                elif cmd == "PASS":
                    password = arg
                    client_socket.sendall(b"230 Login successful.\r\n")

                    # Register FTP Session with FastAPI Backend
                    print(f"[+] FTP Login Attempt: IP={client_ip} | User={username} | Pass={password}")
                    try:
                        r = requests.post(
                            f"{BACKEND_URL}/api/sessions",
                            json={
                                "ip_address": client_ip,
                                "username_attempted": f"ftp_{username}",
                                "password_attempted": password
                            },
                            timeout=2
                        )
                        if r.status_code == 200:
                            session_id = r.json().get("session_id")
                    except Exception as e:
                        print(f"[-] FTP Session Backend registration failed: {e}")

                elif cmd in ["SYST", "PWD", "CWD", "TYPE", "PORT", "PASV", "LIST", "STOR", "RETR"]:
                    # Log event to backend
                    if session_id:
                        try:
                            requests.post(
                                f"{BACKEND_URL}/api/sessions/{session_id}/events",
                                json={
                                    "event_type": "ftp_command_execution",
                                    "input_data": cmd_line,
                                    "output_data": "Decoy Response Executed"
                                },
                                timeout=2
                            )
                        except Exception:
                            pass

                    if cmd == "SYST":
                        client_socket.sendall(b"215 UNIX Type: L8\r\n")
                    elif cmd == "PWD":
                        client_socket.sendall(b'257 "/home/ftp_share" is current directory.\r\n')
                    elif cmd == "TYPE":
                        client_socket.sendall(b"200 Switching to Binary mode.\r\n")
                    elif cmd in ["PORT", "PASV"]:
                        client_socket.sendall(b"227 Entering Passive Mode (127,0,0,1,8,8).\r\n")
                    elif cmd == "LIST":
                        client_socket.sendall(b"150 Here comes the directory listing.\r\n")
                        client_socket.sendall(b"226 Directory send OK.\r\n")
                    elif cmd == "STOR":
                        client_socket.sendall(b"150 Ok to send data.\r\n226 Transfer complete. Payload captured.\r\n")
                    elif cmd == "RETR":
                        client_socket.sendall(b"550 Failed to open file: Access Denied.\r\n")
                    else:
                        client_socket.sendall(b"200 Command OK.\r\n")

                elif cmd in ["QUIT", "EXIT"]:
                    client_socket.sendall(b"221 Goodbye.\r\n")
                    break
                else:
                    client_socket.sendall(b"500 Unknown command.\r\n")

        except Exception as e:
            print(f"[-] FTP Client error {client_ip}: {e}")
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
            print(f"[*] FTP Honeypot listening on port {self.port}...")
            while True:
                client_sock, (ip, port) = self.server_socket.accept()
                print(f"[+] Incoming FTP connection from {ip}:{port}")
                t = threading.Thread(target=self.handle_client, args=(client_sock, ip))
                t.daemon = True
                t.start()
        except KeyboardInterrupt:
            print("\n[*] Stopping FTP Honeypot server.")
        except Exception as e:
            print(f"[-] FTP Server error: {e}")
            sys.exit(1)

if __name__ == '__main__':
    server = FTPHoneypotServer()
    server.start()
