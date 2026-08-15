import os
import sys
import socket
import threading
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
SCANNER_PORT = int(os.getenv("SCANNER_PORT", "3389"))  # Decoy Remote Desktop / Service Listener

class PortScannerHoneypotTrap:
    """
    Port Scanner & Vulnerability Probe Trap
    Captures network-wide port scans (nmap, Masscan, Shodan scanners) and unassigned
    high-value target service connections (RDP 3389, VNC 5900, MongoDB 27017).
    """

    def __init__(self, host: str = "0.0.0.0", port: int = SCANNER_PORT):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def handle_client(self, client_socket: socket.socket, client_ip: str):
        session_id = None
        try:
            print(f"[+] Network Port Scan / Probe detected from IP={client_ip} on Port {self.port}")

            # Register session with FastAPI Backend
            try:
                r = requests.post(
                    f"{BACKEND_URL}/api/sessions",
                    json={
                        "ip_address": client_ip,
                        "username_attempted": f"port_scan_{self.port}",
                        "password_attempted": "tcp_syn_probe"
                    },
                    timeout=2
                )
                if r.status_code == 200:
                    session_id = r.json().get("session_id")
            except Exception as e:
                print(f"[-] Scanner Trap Session registration failed: {e}")

            # Read initial scanner payload
            data = client_socket.recv(1024)
            hex_payload = data.hex()[:100] if data else "SYN_CONNECT_ONLY"

            # Log scan event
            if session_id:
                try:
                    requests.post(
                        f"{BACKEND_URL}/api/sessions/{session_id}/events",
                        json={
                            "event_type": "port_scan_detected",
                            "input_data": f"TCP Probe Port {self.port} | Hex Payload: {hex_payload}",
                            "output_data": "Decoy Service Response Sent"
                        },
                        timeout=2
                    )
                except Exception:
                    pass

            # Send decoy response based on port type (RDP / VNC / Generic)
            if self.port == 3389:
                # Decoy RDP Connection Confirm Packet
                client_socket.sendall(b"\x03\x00\x00\x13\x0e\xd0\x00\x00\x12\x34\x00\x02\x09\x08\x00\x00\x00\x00\x00")
            elif self.port == 5900:
                # Decoy VNC Server Protocol Version
                client_socket.sendall(b"RFB 003.008\n")
            else:
                client_socket.sendall(b"220 Enterprise Service Ready\r\n")

        except Exception as e:
            print(f"[-] Scanner Trap Client error {client_ip}: {e}")
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
            print(f"[*] Port Scanner Trap listening on TCP port {self.port}...")
            while True:
                client_sock, (ip, port) = self.server_socket.accept()
                t = threading.Thread(target=self.handle_client, args=(client_sock, ip))
                t.daemon = True
                t.start()
        except KeyboardInterrupt:
            print("\n[*] Stopping Scanner Trap server.")
        except Exception as e:
            print(f"[-] Scanner Trap Server error: {e}")
            sys.exit(1)

if __name__ == '__main__':
    trap = PortScannerHoneypotTrap()
    trap.start()
