export interface HoneypotEvent {
  id: number;
  event_type: string;
  input_data: string | null;
  output_data: string | null;
  timestamp: string;
  session_id?: string;
}

export type EventCategory = "command" | "deception" | "canary" | "auth" | "system";

export function categorizeEvent(eventType: string): EventCategory {
  if (!eventType) return "system";
  const type = eventType.toLowerCase();
  if (type.includes("canary") || type.includes("tripwire")) {
    return "canary";
  }
  if (type.includes("deception") || type.includes("trap") || type.includes("honeytoken")) {
    return "deception";
  }
  if (type.includes("command") || type.includes("execution") || type.includes("probe")) {
    return "command";
  }
  if (type.includes("auth") || type.includes("login") || type.includes("session")) {
    return "auth";
  }
  return "system";
}

export function humanizeEventType(eventType: string): string {
  if (!eventType) return "Unknown Event";
  return eventType
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export interface ShellReplayState {
  cwd: string;
  env: Record<string, string>;
}

export function createShellReplayState(): ShellReplayState {
  return {
    cwd: "/root",
    env: {
      USER: "root",
      HOME: "/root",
      SHELL: "/bin/bash",
    },
  };
}

export function simulateDeceptionResponse(input: string): { output: string; type: string } | null {
  const cmd = input.trim();
  if (/\.aws\/credentials|\.aws\/config/i.test(cmd)) {
    return {
      type: "canary_tripwire_aws_credentials",
      output: "[default]\naws_access_key_id = AKIAIOSFODNN7EXAMPLE\naws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n# CANARY-TRIPWIRE [AWS_CLI_KEY]: Cloud key access alerted.\n",
    };
  }
  if (/\.ssh\/id_rsa|id_ed25519/i.test(cmd)) {
    return {
      type: "canary_tripwire_ssh_private_key",
      output: "-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXktdjE... [HONEYTOKEN TRAPPED] ...\n-----END OPENSSH PRIVATE KEY-----\n# CANARY-TRIPWIRE [SSH_KEY]: Private key access alerted.\n",
    };
  }
  if (/\.git-credentials|github_token/i.test(cmd)) {
    return {
      type: "canary_tripwire_github_token",
      output: "https://sentineltrap-deploy-bot:ghp_9kL2x0Vb8M1qR3oP4zW6Y7tJ5nE0A8cCdEfG@github.com\n# CANARY-TRIPWIRE [GITHUB_PAT]: Scoped token access alerted.\n",
    };
  }
  if (/service-account\.json|\.kube\/config/i.test(cmd)) {
    return {
      type: "canary_tripwire_gcp_service_account",
      output: '{\n  "client_email": "canary-prod-agent@sentineltrap-cloud-defense.iam.gserviceaccount.com"\n}\n# CANARY-TRIPWIRE [GCP_KEY]: Service account access alerted.\n',
    };
  }
  if (/cat\s+.*passwd|grep\s+.*pass|cat\s+.*shadow/i.test(cmd)) {
    return {
      type: "credential_harvesting",
      output:
        "root:x:0:0:root:/root:/bin/bash\nadmin:x:1000:1000:admin:/home/admin:/bin/bash\ndb_backup_user:x:1001:1001::/home/db_backup_user:/bin/bash\n# HONEY-TRAP: Production API key stored in /etc/cloud/secrets.env\n",
    };
  }
  if (/mysql|psql|postgres|mongo|sqlite/i.test(cmd)) {
    return {
      type: "database_access_attempt",
      output:
        "Connecting to production database cluster at 10.0.4.18:3306...\nERROR 1045 (28000): Access denied for user 'root'@'%' (using password: NO)\n",
    };
  }
  if (/nmap|ifconfig|ip\s+a|netstat|route/i.test(cmd)) {
    return {
      type: "network_reconnaissance",
      output:
        "Kernel IP routing table\nDestination     Gateway         Genmask         Flags Metric Ref    Use Iface\n0.0.0.0         192.168.1.1     0.0.0.0         UG    100    0        0 eth0\n10.0.4.18       0.0.0.0         255.255.255.255 UH    100    0        0 vpn0 [Decoy Database Host]\n",
    };
  }
  return null;
}

export function simulateShellOutput(input: string, state: ShellReplayState): string | null {
  const cmd = input.trim();
  if (cmd === "pwd") return `${state.cwd}\n`;
  if (cmd === "whoami") return "root\n";
  if (cmd === "id") return "uid=0(root) gid=0(root) groups=0(root)\n";
  if (cmd.startsWith("cd")) {
    const target = cmd.split(" ")[1] || "/root";
    state.cwd = target;
    return null;
  }
  if (cmd === "ls" || cmd.startsWith("ls ")) {
    return "total 12\n-rw-r--r-- 1 root root  220 Aug 20 12:01 deploy.sh\n-rw-r--r-- 1 root root  450 Aug 20 12:05 notes.txt\n";
  }
  return null;
}
