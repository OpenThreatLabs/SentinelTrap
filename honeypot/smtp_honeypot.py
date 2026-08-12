import os
import sys
import socket
import threading
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
SMTP_PORT = int(os.getenv("SMTP_PORT", "2525"))

class SMTPHoneypotServer:
    """
    SMTP Mail Honeypot Server
    Captures automated email spam bots, phishing distribution attempts,
    and open-relay mail server exploitation probes.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = SMTP_PORT):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def handle_client(self, client_socket: socket.socket, client_ip: str):
        session_id = None
        sender = "unknown"
        recipients = []
        is_data_mode = False
        email_body = ""

        try:
            # Banner greeting
            client_socket.sendall(b"220 mail.prod-web-srv-01.local ESMTP Postfix (Ubuntu)\r\n")

            while True:
                data = client_socket.recv(1024).decode('utf-8', errors='ignore')
                if not data:
                    break

                if is_data_mode:
                    email_body += data
                    if "\r\n.\r\n" in email_body or data.strip() == ".":
                        is_data_mode = False
                        client_socket.sendall(b"250 2.0.0 Ok: queued as 4F92B102A8\r\n")

                        # Log captured email body event to backend
                        if session_id:
                            try:
                                requests.post(
                                    f"{BACKEND_URL}/api/sessions/{session_id}/events",
                                    json={
                                        "event_type": "smtp_phishing_captured",
                                        "input_data": f"From: {sender} | To: {','.join(recipients)}",
                                        "output_data": f"Body Snippet: {email_body[:300]}"
                                    },
                                    timeout=2
                                )
                            except Exception:
                                pass
                        email_body = ""
                    continue

                cmd_line = data.strip()
                parts = cmd_line.split(" ", 1)
                cmd = parts[0].upper()
                arg = parts[1] if len(parts) > 1 else ""

                if cmd in ["HELO", "EHLO"]:
                    client_socket.sendall(b"250-mail.prod-web-srv-01.local Hello\r\n250-AUTH LOGIN PLAIN\r\n250 OK\r\n")

                elif cmd.startswith("MAIL"):
                    sender = arg.replace("FROM:", "").strip("<> ")
                    client_socket.sendall(b"250 2.1.0 Ok\r\n")

                    # Register session with backend
                    print(f"[+] SMTP Probe from IP={client_ip} | Sender={sender}")
                    try:
                        r = requests.post(
                            f"{BACKEND_URL}/api/sessions",
                            json={
                                "ip_address": client_ip,
                                "username_attempted": f"smtp_{sender[:30]}",
                                "password_attempted": "smtp_relay"
                            },
                            timeout=2
                        )
                        if r.status_code == 200:
                            session_id = r.json().get("session_id")
                    except Exception as e:
                        print(f"[-] SMTP Session registration failed: {e}")

                elif cmd.startswith("RCPT"):
                    recipient = arg.replace("TO:", "").strip("<> ")
                    recipients.append(recipient)
                    client_socket.sendall(b"250 2.1.5 Ok\r\n")

                elif cmd == "DATA":
                    is_data_mode = True
                    client_socket.sendall(b"354 End data with <CR><LF>.<CR><LF>\r\n")

                elif cmd == "QUIT":
                    client_socket.sendall(b"221 2.0.0 Bye\r\n")
                    break

                else:
                    client_socket.sendall(b"250 OK\r\n")

        except Exception as e:
            print(f"[-] SMTP Client error {client_ip}: {e}")
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
            print(f"[*] SMTP Mail Honeypot listening on port {self.port}...")
            while True:
                client_sock, (ip, port) = self.server_socket.accept()
                print(f"[+] Incoming SMTP connection from {ip}:{port}")
                t = threading.Thread(target=self.handle_client, args=(client_sock, ip))
                t.daemon = True
                t.start()
        except KeyboardInterrupt:
            print("\n[*] Stopping SMTP Honeypot server.")
        except Exception as e:
            print(f"[-] SMTP Server error: {e}")
            sys.exit(1)

if __name__ == '__main__':
    server = SMTPHoneypotServer()
    server.start()
