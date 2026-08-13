import os
import sys
import socket
import threading
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

class RedisHoneypotServer:
    """
    Redis Database Honeypot Server
    Captures automated Redis database scanners, unauthenticated RCE attempts,
    SSH key injection probes, and unauthorized database dump commands.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = REDIS_PORT):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def handle_client(self, client_socket: socket.socket, client_ip: str):
        session_id = None

        # Register Redis Session with FastAPI Backend
        print(f"[+] Redis Connection Probe from IP={client_ip}")
        try:
            r = requests.post(
                f"{BACKEND_URL}/api/sessions",
                json={
                    "ip_address": client_ip,
                    "username_attempted": "redis_unauth",
                    "password_attempted": "redis_probe"
                },
                timeout=2
            )
            if r.status_code == 200:
                session_id = r.json().get("session_id")
        except Exception as e:
            print(f"[-] Redis Session Backend registration failed: {e}")

        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8', errors='ignore')
                if not data:
                    break

                raw_cmd = data.strip()

                # Log captured Redis command to backend
                if session_id:
                    try:
                        requests.post(
                            f"{BACKEND_URL}/api/sessions/{session_id}/events",
                            json={
                                "event_type": "redis_command_probe",
                                "input_data": raw_cmd[:200],
                                "output_data": "Decoy Redis Response"
                            },
                            timeout=2
                        )
                    except Exception:
                        pass

                cmd_upper = raw_cmd.upper()

                if "PING" in cmd_upper:
                    client_socket.sendall(b"+PONG\r\n")

                elif "AUTH" in cmd_upper:
                    client_socket.sendall(b"-ERR invalid password\r\n")

                elif "INFO" in cmd_upper:
                    info_payload = (
                        "$180\r\n"
                        "# Server\r\nredis_version:6.2.6\r\nos:Linux 5.15.0-52-generic x86_64\r\n"
                        "tcp_port:6379\r\nconnected_clients:1\r\nused_memory_human:2.4M\r\n\r\n"
                    )
                    client_socket.sendall(info_payload.encode('utf-8'))

                elif "CONFIG" in cmd_upper:
                    if "SET" in cmd_upper and ("DIR" in cmd_upper or "DBFILENAME" in cmd_upper):
                        # Detect RCE attempt via Redis CONFIG SET dir /root/.ssh
                        client_socket.sendall(b"+OK\r\n")
                    else:
                        client_socket.sendall(b"+OK\r\n")

                elif "FLUSHALL" in cmd_upper or "KEYS" in cmd_upper:
                    client_socket.sendall(b"*2\r\n$11\r\nsession_keys\r\n$10\r\ndb_secrets\r\n")

                elif "QUIT" in cmd_upper:
                    client_socket.sendall(b"+OK\r\n")
                    break

                else:
                    client_socket.sendall(b"+OK\r\n")

        except Exception as e:
            print(f"[-] Redis Client error {client_ip}: {e}")
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
            print(f"[*] Redis Database Honeypot listening on port {self.port}...")
            while True:
                client_sock, (ip, port) = self.server_socket.accept()
                print(f"[+] Incoming Redis connection from {ip}:{port}")
                t = threading.Thread(target=self.handle_client, args=(client_sock, ip))
                t.daemon = True
                t.start()
        except KeyboardInterrupt:
            print("\n[*] Stopping Redis Honeypot server.")
        except Exception as e:
            print(f"[-] Redis Server error: {e}")
            sys.exit(1)

if __name__ == '__main__':
    server = RedisHoneypotServer()
    server.start()
