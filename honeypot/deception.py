#!/usr/bin/env python3
"""
SentinelTrap - Adaptive Deception Engine
Generates dynamic lure files, honeytokens, decoy credentials, and realistic
fake system responses to attract, engage, and analyze attacker behavior.
"""

import re
import json

class AdaptiveDeceptionEngine:
    def __init__(self):
        self.active_decoys = {
            "fake_credentials": True,
            "fake_database": True,
            "decoy_network": True,
            "aws_keys": True
        }

    def inspect_and_respond(self, command: str) -> tuple[str, bool, str]:
        cmd = command.strip()
        if not cmd:
            return "", False, ""

        # Pattern 1: Credential Discovery & Password Hunting
        if re.search(r'(cat\s+.*passwd|grep\s+.*pass|find\s+.*pass|cat\s+.*shadow|cat\s+.*id_rsa|cat\s+.*env)', cmd, re.IGNORECASE):
            output = (
                "root:x:0:0:root:/root:/bin/bash\n"
                "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n"
                "admin:x:1000:1000:admin:/home/admin:/bin/bash\n"
                "db_user:x:1001:1001:Database User:/home/db_user:/bin/bash\n"
                "deploy_user:x:1002:1002:Deploy Bot:/home/deploy_user:/bin/bash\n"
                "# HONEY-TRAP: Secrets stored in /var/www/html/.env\n"
            )
            return output, True, "credential_harvesting"

        # Pattern 2: Database & SQL Probing
        if re.search(r'(mysql|psql|postgres|mongo|sqlite|dump|redis-cli)', cmd, re.IGNORECASE):
            output = (
                "Connecting to production database cluster at 10.0.4.18:3306...\n"
                "ERROR 1045 (28000): Access denied for user 'root'@'%' (using password: NO)\n"
                "Try: mysql -u admin_root -pP@ssw0rd2026_prod -h 10.0.4.18\n"
            )
            return output, True, "database_access_attempt"

        # Pattern 3: Network Reconnaissance
        if re.search(r'(nmap|ping\s+|ifconfig|ip\s+a|netstat|route|arp|traceroute)', cmd, re.IGNORECASE):
            output = (
                "Kernel IP routing table\n"
                "Destination     Gateway         Genmask         Flags Metric Ref    Use Iface\n"
                "0.0.0.0         192.168.1.1     0.0.0.0         UG    100    0        0 eth0\n"
                "192.168.1.0     0.0.0.0         255.255.255.0   U     100    0        0 eth0\n"
                "10.0.4.18       0.0.0.0         255.255.255.255 UH    100    0        0 vpn0 [Decoy DB Cluster]\n"
            )
            return output, True, "network_reconnaissance"

        return "", False, ""

def get_fake_env():
    """Returns realistic decoy .env file content with honeytokens."""
    return (
        "# Acme Corp Production Environment Variables\n"
        "APP_ENV=production\n"
        "APP_DEBUG=false\n"
        "APP_SECRET=sk_live_902184918239012849102\n\n"
        "# Database Credentials Lure\n"
        "DB_HOST=10.0.8.22\n"
        "DB_PORT=3306\n"
        "DB_DATABASE=acme_prod_db\n"
        "DB_USERNAME=root\n"
        "DB_PASSWORD=P@ssw0rd2026_Prod_Secret!\n\n"
        "# AWS Cloud Lure\n"
        "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\n"
        "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n"
        "AWS_DEFAULT_REGION=us-east-1\n"
    )

def get_fake_aws_credentials():
    """Returns fake AWS IAM security credentials JSON for SSRF traps."""
    return json.dumps({
        "Code": "Success",
        "LastUpdated": "2026-07-28T22:00:00Z",
        "Type": "AWS-HMAC",
        "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
        "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "Token": "IQoJb3JpZ2luX2VjEAAAaHR0cHM6Ly9hd3MuYW1hem9uLmNvbS9zZWNyZXRz...",
        "Expiration": "2026-07-29T06:00:00Z"
    }, indent=2)

def get_fake_shadow():
    """Returns decoy shadow hash entries."""
    return (
        "root:$6$vQ9xL2a$mP1.3O9pW8z8X4kL1j0/9u2L0u1P2o3Q4r5S6t7U8v9W0x1Y2z3A4b5C6d7E8f9G0:19500:0:99999:7:::\n"
        "admin:$6$kL8mN9p$x1Y2z3A4b5C6d7E8f9G0h1I2j3K4l5M6n7O8p9Q0r1S2t3U4v5W6x7Y8z9A0b1:19500:0:99999:7:::\n"
    )
