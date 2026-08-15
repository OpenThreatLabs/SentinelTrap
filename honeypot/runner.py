import os
import sys
import time
import threading

# Import all multi-protocol honeypot server modules
from server import main as start_ssh
from telnet_server import TelnetHoneypotServer
from web_trap import main as start_web
from ftp_server import FTPHoneypotServer
from smtp_honeypot import SMTPHoneypotServer
from mysql_honeypot import MySQLHoneypotServer
from redis_honeypot import RedisHoneypotServer
from dns_honeypot import DNSHoneypotServer
from port_scanner_trap import PortScannerHoneypotTrap

class MultiProtocolHoneypotRunner:
    """
    Multi-Protocol Honeypot Orchestrator
    Launches and supervises all 9 honeypot server nodes concurrently in background threads:
    SSH (2222), Telnet (2223), HTTP (8080), FTP (2121), SMTP (2525), MySQL (3306),
    Redis (6379), DNS (5353), RDP/Port Scanner Trap (3389).
    """

    @staticmethod
    def run_thread(target_fn, name: str):
        try:
            print(f"[+] Launching {name} thread...")
            target_fn()
        except Exception as e:
            print(f"[-] {name} thread encountered an error: {e}")

    def start_all(self):
        print("==========================================================")
        print("🛡️  SentinelTrap Multi-Protocol Honeypot Suite (OpenThreatLabs)")
        print("==========================================================")

        listeners = [
            ("SSH Honeypot Server (:2222)", start_ssh),
            ("Telnet Honeypot Server (:2223)", lambda: TelnetHoneypotServer().start()),
            ("HTTP Web Trap Server (:8080)", start_web),
            ("FTP Honeypot Server (:2121)", lambda: FTPHoneypotServer().start()),
            ("SMTP Mail Honeypot Server (:2525)", lambda: SMTPHoneypotServer().start()),
            ("MySQL Database Honeypot Server (:3306)", lambda: MySQLHoneypotServer().start()),
            ("Redis Database Honeypot Server (:6379)", lambda: RedisHoneypotServer().start()),
            ("DNS Reconnaissance Honeypot Server (:5353)", lambda: DNSHoneypotServer().start()),
            ("Port Scanner / RDP Probe Trap (:3389)", lambda: PortScannerHoneypotTrap().start())
        ]

        threads = []
        for name, fn in listeners:
            t = threading.Thread(target=self.run_thread, args=(fn, name), daemon=True)
            t.start()
            threads.append(t)
            time.sleep(0.2)

        print("==========================================================")
        print("[*] All 9 Multi-Protocol Honeypot Nodes are active & listening.")
        print("==========================================================")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[*] Shutting down SentinelTrap Honeypot Suite...")
            sys.exit(0)

if __name__ == '__main__':
    runner = MultiProtocolHoneypotRunner()
    runner.start_all()
