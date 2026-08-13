import re

class AdaptiveDeceptionEngine:
    """
    Adaptive Deception Engine
    Analyzes shell input patterns to dynamically generate honey responses,
    fake credential files, and simulated database errors.
    """

    def __init__(self):
        self.decoys = {
            "credentials_exposed": False,
            "database_exposed": False,
            "network_exposed": False
        }

    def inspect_and_respond(self, command: str) -> tuple[str, bool, str]:
        cmd = command.strip()
        if not cmd:
            return "", False, ""

        # Credential hunting attempts (passwd, shadow, id_rsa, etc.)
        if re.search(r'(cat\s+.*passwd|grep\s+.*pass|find\s+.*pass|cat\s+.*shadow|cat\s+.*id_rsa)', cmd, re.IGNORECASE):
            self.decoys["credentials_exposed"] = True
            output = (
                "root:x:0:0:root:/root:/bin/bash\n"
                "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n"
                "admin:x:1000:1000:admin:/home/admin:/bin/bash\n"
                "db_backup_user:x:1001:1001::/home/db_backup_user:/bin/bash\n"
                "deploy_user:x:1002:1002::/home/deploy_user:/bin/bash\n"
                "# HONEY-TRAP: Production API key stored in /etc/cloud/secrets.env\n"
            )
            return output, True, "credential_harvesting"

        # Database connection attempts (mysql, psql, mongo, dump)
        if re.search(r'(mysql|psql|postgres|mongo|sqlite|dump|redis-cli)', cmd, re.IGNORECASE):
            self.decoys["database_exposed"] = True
            output = (
                "Connecting to production database cluster at 10.0.4.18:3306...\n"
                "ERROR 1045 (28000): Access denied for user 'root'@'%' (using password: NO)\n"
                "Warning: Automated vulnerability report dispatched to SecOps team.\n"
            )
            return output, True, "database_access_attempt"

        # Network topology & port scanning (nmap, ping, ifconfig, netstat)
        if re.search(r'(nmap|ping\s+|ifconfig|ip\s+a|netstat|route|arp|traceroute)', cmd, re.IGNORECASE):
            self.decoys["network_exposed"] = True
            output = (
                "Kernel IP routing table\n"
                "Destination     Gateway         Genmask         Flags Metric Ref    Use Iface\n"
                "0.0.0.0         192.168.1.1     0.0.0.0         UG    100    0        0 eth0\n"
                "192.168.1.0     0.0.0.0         255.255.255.0   U     100    0        0 eth0\n"
                "10.0.4.18       0.0.0.0         255.255.255.255 UH    100    0        0 vpn0 [Decoy Database Host]\n"
                "10.0.4.25       0.0.0.0         255.255.255.255 UH    100    0        0 vpn0 [Decoy Auth Gateway]\n"
            )
            return output, True, "network_reconnaissance"

        return "", False, ""
