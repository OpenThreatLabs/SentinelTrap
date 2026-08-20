export interface HoneypotEvent {
  id: number;
  event_type: string;
  input_data: string | null;
  output_data: string | null;
  timestamp: string;
  session_id?: string;
}

export type EventCategory = "command" | "deception" | "auth" | "system";

export function categorizeEvent(eventType: string): EventCategory {
  if (!eventType) return "system";
  const type = eventType.toLowerCase();
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
