import os
import sys
import socket
import select
import threading
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
DNS_PORT = int(os.getenv("DNS_PORT", "5353"))
DNS_HOST = os.getenv("DNS_HOST", "0.0.0.0")

class DNSHoneypotServer:
    """
    DNS Honeypot Server
    Captures DNS amplification attack probes, DNS tunneling activity,
    AXFR zone transfer attempts, and domain reconnaissance queries.
    """

    def __init__(self, host: str = DNS_HOST, port: int = DNS_PORT):
        self.host = host
        self.port = port
        self.sockets = []
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

        # Slicing Question section:
        # Question section starts at offset 12 and ends after QNAME + 2 bytes QTYPE + 2 bytes QCLASS.
        # Do not use data[12:] as queries with EDNS0 contain additional records (OPT RR)
        # that would corrupt the Answer section layout per RFC 1035 / RFC 6891.
        idx = 12
        while idx < len(data):
            length = data[idx]
            if length == 0:
                break
            idx += 1 + length
        question_end = min(idx + 5, len(data))
        question = data[12:question_end]

        # Answer Section (Name pointer + Type A + Class IN + TTL 300 + IP 10.0.4.18)
        answer = b"\xc0\x0c\x00\x01\x00\x01\x00\x00\x01\x2c\x00\x04\x0a\x00\x04\x12"

        return header + question + answer

    def _create_sockets(self):
        bind_addrs = set()
        if self.host and self.host != "0.0.0.0":
            bind_addrs.add(self.host)
        else:
            # On Windows, Dnscache (mDNS) binds 0.0.0.0:5353 with SO_REUSEADDR.
            # Wildcard sockets do not receive incoming unicast traffic already claimed by Dnscache.
            # Binding to specific interface IPs takes precedence under Winsock rules.
            try:
                hostname = socket.gethostname()
                for ip in socket.gethostbyname_ex(hostname)[2]:
                    if ip:
                        bind_addrs.add(ip)
            except Exception:
                pass
            bind_addrs.add("127.0.0.1")
            bind_addrs.add("0.0.0.0")

        sockets = []
        for ip in sorted(bind_addrs):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((ip, self.port))
                sockets.append(sock)
            except Exception:
                pass
        return sockets

    def start(self):
        try:
            self.sockets = self._create_sockets()
            if not self.sockets:
                raise RuntimeError(f"Could not bind to port {self.port} on any address")
            self.server_socket = self.sockets[0]
            print(f"[*] DNS Honeypot listening on UDP port {self.port}...")
            
            while True:
                readable, _, _ = select.select(self.sockets, [], [])
                for sock in readable:
                    data, addr = sock.recvfrom(1024)
                    client_ip = addr[0]
                    qname = self.parse_dns_qname(data)

                    print(f"[+] DNS Query Probe: IP={client_ip} | Domain={qname}")

                    # Send Decoy Response immediately
                    response_bytes = self.build_dns_response(data, qname)
                    if response_bytes:
                        sock.sendto(response_bytes, addr)

                    # Register session with FastAPI Backend
                    session_id = None
                    try:
                        r = requests.post(
                            f"{BACKEND_URL}/api/sessions",
                            json={
                                "ip_address": client_ip,
                                "username_attempted": "dns_query",
                                "password_attempted": qname[:50],
                                "protocol": "DNS"
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

                        try:
                            requests.patch(f"{BACKEND_URL}/api/sessions/{session_id}", timeout=2)
                        except Exception:
                            pass

        except KeyboardInterrupt:
            print("\n[*] Stopping DNS Honeypot server.")
        except Exception as e:
            print(f"[-] DNS Server error: {e}")
            sys.exit(1)
        finally:
            for s in self.sockets:
                try:
                    s.close()
                except Exception:
                    pass


if __name__ == '__main__':
    server = DNSHoneypotServer()
    server.start()
