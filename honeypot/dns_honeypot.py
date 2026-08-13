import os
import sys
import socket
import threading
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
DNS_PORT = int(os.getenv("DNS_PORT", "5353"))

class DNSHoneypotServer:
    """
    DNS Honeypot Server
    Captures DNS amplification attack probes, DNS tunneling activity,
    AXFR zone transfer attempts, and domain reconnaissance queries.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = DNS_PORT):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def parse_dns_qname(self, data: bytes) -> str:
        """Parses queried domain name from DNS request payload bytes."""
        try:
            domain_parts = []
            idx = 12  # Header offset
            while idx < len(data):
                length = data[idx]
                if length == 0:
                    break
                domain_parts.append(data[idx + 1:idx + 1 + length].decode('utf-8', errors='ignore'))
                idx += 1 + length
            return ".".join(domain_parts)
        except Exception:
            return "unknown.domain"

    def build_dns_response(self, data: bytes, qname: str) -> bytes:
        """Builds a decoy DNS A-record response pointing to 10.0.4.18."""
        if len(data) < 12:
            return b""

        transaction_id = data[:2]
        flags = b"\x81\x80"  # Standard query response, No error
        qdcount = data[4:6]
        ancount = b"\x00\x01" # 1 Answer record
        nscount = b"\x00\x00"
        arcount = b"\x00\x00"

        header = transaction_id + flags + qdcount + ancount + nscount + arcount
        question = data[12:]

        # Answer Section (Name pointer + Type A + Class IN + TTL 300 + IP 10.0.4.18)
        answer = b"\xc0\x0c\x00\x01\x00\x01\x00\x00\x01\x2c\x00\x04\x0a\x00\x04\x12"

        return header + question + answer

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            print(f"[*] DNS Honeypot listening on UDP port {self.port}...")
            
            while True:
                data, addr = self.server_socket.recvfrom(1024)
                client_ip = addr[0]
                qname = self.parse_dns_qname(data)

                print(f"[+] DNS Query Probe: IP={client_ip} | Domain={qname}")

                # Register session with FastAPI Backend
                session_id = None
                try:
                    r = requests.post(
                        f"{BACKEND_URL}/api/sessions",
                        json={
                            "ip_address": client_ip,
                            "username_attempted": "dns_query",
                            "password_attempted": qname[:50]
                        },
                        timeout=2
                    )
                    if r.status_code == 200:
                        session_id = r.json().get("session_id")
                except Exception:
                    pass

                # Log event
                if session_id:
                    try:
                        requests.post(
                            f"{BACKEND_URL}/api/sessions/{session_id}/events",
                            json={
                                "event_type": "dns_recon_attempt",
                                "input_data": f"DNS Query: {qname}",
                                "output_data": "Decoy A-Record Response: 10.0.4.18"
                            },
                            timeout=2
                        )
                    except Exception:
                        pass

                # Send Decoy Response
                response_bytes = self.build_dns_response(data, qname)
                if response_bytes:
                    self.server_socket.sendto(response_bytes, addr)

                if session_id:
                    try:
                        requests.patch(f"{BACKEND_URL}/api/sessions/{session_id}", timeout=2)
                    except Exception:
                        pass

        except KeyboardInterrupt:
            print("\n[*] Stopping DNS Honeypot server.")
        except Exception as e:
            print(f"[-] DNS Server error: {e}")
            sys.exit(1)

if __name__ == '__main__':
    server = DNSHoneypotServer()
    server.start()
