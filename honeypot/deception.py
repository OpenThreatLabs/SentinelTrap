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
            "network_exposed": False,
            "canary_tripwire_triggered": False
        }

    def inspect_and_respond(self, command: str) -> tuple[str, bool, str]:
        cmd = command.strip()
        if not cmd:
            return "", False, ""

        # Canary Honeytoken Tripwire 1: AWS / Cloud Credentials (/root/.aws/credentials, config, s3)
        if re.search(r'(\.aws/credentials|\.aws/config|aws_access_key|s3cfg|\.boto)', cmd, re.IGNORECASE):
            self.decoys["canary_tripwire_triggered"] = True
            self.decoys["credentials_exposed"] = True
            output = (
                "[default]\n"
                "aws_access_key_id = AKIAIOSFODNN7EXAMPLE\n"
                "aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n"
                "region = us-east-1\n"
                "output = json\n"
            )
            return output, True, "canary_tripwire_aws_credentials"

        # Canary Honeytoken Tripwire 2: SSH Private Keys (/root/.ssh/id_rsa, id_ed25519)
        if re.search(r'(\.ssh/id_rsa|\.ssh/id_ed25519|\.ssh/authorized_keys|id_rsa|id_dsa)', cmd, re.IGNORECASE):
            self.decoys["canary_tripwire_triggered"] = True
            self.decoys["credentials_exposed"] = True
            output = (
                "-----BEGIN OPENSSH PRIVATE KEY-----\n"
                "b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn\n"
                "NhAAAAAwEAAQAAAYEAt4pM7KjQ3v8kZ9Lv3QW7KzM9Lq4X8V1b9C2x1Z6w\n"
                "6Qx34p+q9JkHh398Kj2Kj4k32mK23k4j==\n"
                "-----END OPENSSH PRIVATE KEY-----\n"
            )
            return output, True, "canary_tripwire_ssh_private_key"

        # Canary Honeytoken Tripwire 3: GitHub / GitLab Personal Access Tokens (.git-credentials, .npmrc, .git/config)
        if re.search(r'(\.git-credentials|\.gitconfig|\.npmrc|github_token|ghp_)', cmd, re.IGNORECASE):
            self.decoys["canary_tripwire_triggered"] = True
            self.decoys["credentials_exposed"] = True
            output = (
                "https://prod-deploy-bot:ghp_9kL2x0Vb8M1qR3oP4zW6Y7tJ5nE0A8cCdEfG@github.com\n"
            )
            return output, True, "canary_tripwire_github_token"

        # Canary Honeytoken Tripwire 4: GCP Service Account Key & Kubernetes Token (/etc/gcp/service-account.json, kube/config)
        if re.search(r'(service-account\.json|gcp.*\.json|\.kube/config|kubernetes)', cmd, re.IGNORECASE):
            self.decoys["canary_tripwire_triggered"] = True
            self.decoys["credentials_exposed"] = True
            output = (
                "{\n"
                '  "type": "service_account",\n'
                '  "project_id": "prod-core-infra",\n'
                '  "private_key_id": "8f3b20c99a4e8d3170b",\n'
                '  "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...==\\n-----END PRIVATE KEY-----\\n",\n'
                '  "client_email": "svc-deploy@prod-core-infra.iam.gserviceaccount.com",\n'
                '  "client_id": "109827346152839102948"\n'
                "}\n"
            )
            return output, True, "canary_tripwire_gcp_service_account"

        # Canary Honeytoken Tripwire 5: Web App & DB Secrets (/var/www/html/config.php, wp-config.php, .env)
        if re.search(r'(config\.php|wp-config\.php|\.env|database\.yml|settings\.py|secrets\.env)', cmd, re.IGNORECASE):
            self.decoys["canary_tripwire_triggered"] = True
            self.decoys["credentials_exposed"] = True
            output = (
                "<?php\n"
                "// Database Production Configuration\n"
                "define('DB_NAME', 'prod_customer_vault');\n"
                "define('DB_USER', 'db_vault_admin');\n"
                "define('DB_PASSWORD', 'V4ult#Pr0d!9982');\n"
                "define('DB_HOST', '10.0.4.18:3306');\n"
                "define('API_SECRET', 'sec_live_99812497184912');\n"
                "?>\n"
            )
            return output, True, "canary_tripwire_web_config"

        # Canary Honeytoken Tripwire 6: Passwords file (/home/admin/passwords.txt, /root/passwords.txt)
        if re.search(r'(passwords?\.txt|creds?\.txt|accounts?\.txt)', cmd, re.IGNORECASE):
            self.decoys["canary_tripwire_triggered"] = True
            self.decoys["credentials_exposed"] = True
            output = (
                "=== INTERNAL CREDENTIALS VAULT ===\n"
                "admin : Tr@pM@ster2024! [SSH/Web]\n"
                "db_backup : B@ckup9090# [MySQL]\n"
                "infra_vpn : Vpn#Tunnel990 [WireGuard]\n"
                "aws_root : RootMaster#2024! [Cloud Console]\n"
            )
            return output, True, "canary_tripwire_passwords_file"

        # Credential hunting attempts (passwd, shadow, id_rsa, etc.)
        if re.search(r'(cat\s+.*passwd|grep\s+.*pass|find\s+.*pass|cat\s+.*shadow|cat\s+.*id_rsa)', cmd, re.IGNORECASE):
            self.decoys["credentials_exposed"] = True
            output = (
                "root:x:0:0:root:/root:/bin/bash\n"
                "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n"
                "admin:x:1000:1000:admin:/home/admin:/bin/bash\n"
                "db_backup_user:x:1001:1001::/home/db_backup_user:/bin/bash\n"
                "deploy_user:x:1002:1002::/home/deploy_user:/bin/bash\n"
                "# Internal service accounts\n"
            )
            return output, True, "credential_harvesting"

        # Database connection attempts (mysql, psql, mongo, dump)
        if re.search(r'(mysql|psql|postgres|mongo|sqlite|dump|redis-cli)', cmd, re.IGNORECASE):
            self.decoys["database_exposed"] = True
            output = (
                "Connecting to production database cluster at 10.0.4.18:3306...\n"
                "ERROR 1045 (28000): Access denied for user 'root'@'%' (using password: NO)\n"
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
                "10.0.4.18       0.0.0.0         255.255.255.255 UH    100    0        0 vpn0\n"
                "10.0.4.25       0.0.0.0         255.255.255.255 UH    100    0        0 vpn0\n"
            )
            return output, True, "network_reconnaissance"

        return "", False, ""
