"use client";

import { useState } from "react";
import {
  Shield,
  FileText,
  Database,
  Cpu,
  Lock,
  Globe,
  Flame,
  Zap,
  CheckCircle,
  Copy,
  Check,
  Download,
  Trash2,
  AlertTriangle,
} from "lucide-react";

export default function BackendFeaturesView() {
  const [copiedRule, setCopiedRule] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [clearing, setClearing] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [clearSuccess, setClearSuccess] = useState<string | null>(null);

  // Adaptive Server Persona State (Anti-Fingerprinting)
  const [activePersona, setActivePersona] = useState<string>("all_mesh");
  const [switchingPersona, setSwitchingPersona] = useState(false);

  const personas: Record<string, { id: string; name: string; description: string; active_ports: number[]; active_decoys: string[]; simulated_os: string }> = {
    web_app: {
      id: "web_app",
      name: "Cloud Web App Server (LAMP/Nginx)",
      description: "Exposes public HTTP & SSH tiers while masking all database and backend services.",
      active_ports: [8080, 2222],
      active_decoys: ["SSH Honeypot", "Web Application Trap"],
      simulated_os: "Debian 11 / Apache 2.4.56"
    },
    database_cluster: {
      id: "database_cluster",
      name: "Internal Database Node (MySQL/Redis)",
      description: "Simulates an internal backend data cluster. Conceals web and edge mail services.",
      active_ports: [3306, 6379, 2222],
      active_decoys: ["SSH Honeypot", "MySQL Decoy", "Redis Decoy"],
      simulated_os: "Ubuntu 22.04 LTS / MySQL 8.0 & Redis 7.0"
    },
    mail_gateway: {
      id: "mail_gateway",
      name: "Edge Mail & DNS Gateway",
      description: "Presents an authoritative perimeter router. Exposes strictly SMTP, DNS, and SSH.",
      active_ports: [2525, 5353, 2222],
      active_decoys: ["SSH Honeypot", "SMTP Honeypot", "DNS Honeypot"],
      simulated_os: "CentOS 7 / Postfix 3.5.8"
    },
    iot_router: {
      id: "iot_router",
      name: "IoT Edge Router (BusyBox/Telnet)",
      description: "Embedded IoT network gateway. Traps automated Mirai/Mozi botnet brute-forcing on Telnet.",
      active_ports: [2223, 8080],
      active_decoys: ["Telnet Trap", "Web Application Trap"],
      simulated_os: "Embedded Linux / BusyBox v1.33"
    },
    all_mesh: {
      id: "all_mesh",
      name: "Full Deception Mesh (Global Research)",
      description: "Simulates all 9 protocol services concurrently for wide-spectrum threat collection.",
      active_ports: [2222, 2223, 8080, 2121, 2525, 3306, 6379, 5353, 3389],
      active_decoys: [
        "SSH Honeypot", "Telnet Trap", "Web Application Trap",
        "FTP Honeypot", "SMTP Honeypot", "MySQL Decoy",
        "Redis Decoy", "DNS Honeypot", "Port Scanner / RDP"
      ],
      simulated_os: "Unified Multi-Layer Deception Matrix"
    }
  };

  const handleSwitchPersona = async (personaId: string) => {
    setSwitchingPersona(true);
    try {
      const res = await fetch(`${apiBase}/api/decoys/personas/${personaId}`, { method: "POST" });
      if (res.ok) {
        setActivePersona(personaId);
      } else {
        // Fallback local state switch
        setActivePersona(personaId);
      }
    } catch {
      setActivePersona(personaId);
    } finally {
      setSwitchingPersona(false);
    }
  };

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "";

  const handleConfirmClear = async () => {
    setClearing(true);
    setClearSuccess(null);
    try {
      const res = await fetch(`${apiBase}/api/data/clear`, { method: "DELETE" });
      if (res.ok) {
        setIsConfirmOpen(false);
        setClearSuccess("All captured attacker telemetry purged successfully!");
        setTimeout(() => {
          setClearSuccess(null);
        }, 3000);
      } else {
        alert("Failed to clear data. Ensure backend is running.");
      }
    } catch (err) {
      console.error("Error clearing telemetry:", err);
      alert("Error reaching backend.");
    } finally {
      setClearing(false);
    }
  };

  const handleSimulateAttack = async () => {
    setSimulating(true);
    setClearSuccess(null);
    try {
      const res = await fetch(`${apiBase}/api/data/simulate-attack?persona=${activePersona}`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        const rule = data.autoshun_mitigation?.firewall_rule || `iptables -A INPUT -s ${data.ip_address} -j DROP`;
        const personaName = personas[data.persona_used]?.name.split(" (")[0] || data.persona_used;
        setClearSuccess(`Live attack [Persona: ${personaName}, Proto: ${data.protocol}] simulated from ${data.ip_address}! Canary tripped -> AutoShun: ${rule}`);
        setTimeout(() => {
          setClearSuccess(null);
        }, 8000);
      } else {
        alert("Failed to simulate live attack. Ensure backend is running.");
      }
    } catch (err) {
      console.error("Error simulating attack:", err);
      alert("Error reaching backend.");
    } finally {
      setSimulating(false);
    }
  };

  const firewallRules = [
    "sudo iptables -A INPUT -s 192.168.1.105 -j DROP",
    "sudo ufw deny from 192.168.1.105 to any",
    "sudo iptables -t nat -A PREROUTING -p tcp --dport 22 -j REDIRECT --to-port 2222",
  ];

  const handleCopy = (rule: string) => {
    navigator.clipboard.writeText(rule);
    setCopiedRule(rule);
    setTimeout(() => setCopiedRule(null), 2000);
  };

  const handleExport = async (format: "pdf" | "csv" | "stix" | "cef") => {
    setDownloading(format);
    try {
      let endpoint = "";
      let defaultFilename = "report";

      if (format === "pdf") {
        endpoint = `${apiBase}/api/reports/pdf/summary`;
        defaultFilename = "sentineltrap_soc_summary_report.pdf";
      } else if (format === "csv") {
        endpoint = `${apiBase}/api/reports/csv`;
        defaultFilename = "sentineltrap_threat_events.csv";
      } else if (format === "stix") {
        endpoint = `${apiBase}/api/reports/stix`;
        defaultFilename = "sentineltrap_stix2.1_bundle.json";
      } else if (format === "cef") {
        endpoint = `${apiBase}/api/reports/cef`;
        defaultFilename = "sentineltrap_events.cef";
      }

      const res = await fetch(endpoint);
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = defaultFilename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(`Export failed for format ${format}:`, err);
    } finally {
      setTimeout(() => setDownloading(null), 800);
    }
  };

  const decoyNodes = [
    { name: "SSH Honeypot", port: 2222, protocol: "TCP", status: "Active", description: "Paramiko virtual SSH server with interactive Debian shell and in-memory VFS." },
    { name: "Telnet Trap", port: 2223, protocol: "TCP", status: "Active", description: "ANSI terminal emulator trapping IoT botnet brute-forcing attacks." },
    { name: "Web Application Trap", port: 8080, protocol: "TCP", status: "Active", description: "Simulated Apache server capturing SQLi, XSS, and path traversal probes." },
    { name: "FTP Honeypot", port: 2121, protocol: "TCP", status: "Active", description: "Virtual FTP daemon recording authentication and anonymous reconnaissance." },
    { name: "SMTP Honeypot", port: 2525, protocol: "TCP", status: "Active", description: "Mail gateway trapping spam campaigns, relay tests, and malicious payloads." },
    { name: "MySQL Decoy", port: 3306, protocol: "TCP", status: "Active", description: "Database trap responding with authentic MySQL binary protocol handshakes." },
    { name: "Redis Decoy", port: 6379, protocol: "TCP", status: "Active", description: "In-memory database decoy trapping unauthenticated INFO, CONFIG, and KEYS scans." },
    { name: "DNS Honeypot", port: 5353, protocol: "UDP", status: "Active", description: "UDP DNS responder capturing domain enumeration and zone transfer attempts." },
    { name: "Port Scanner / RDP", port: 3389, protocol: "TCP", status: "Active", description: "Multi-port probe detector capturing SYN stealth scans and RDP probes." },
  ];

  return (
    <div className="space-y-8">
      {/* 1. System Engine Health Banner */}
      <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-emerald-500/10 dark:bg-emerald-500/20 p-2.5 text-emerald-600 dark:text-emerald-400">
              <Shield className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-base font-bold text-zinc-900 dark:text-white">
                Multi-Protocol Deception Mesh (Active)
              </h2>
              <p className="text-xs text-zinc-500">
                Supervised by In-Memory Virtual File System (VFS) & Shell State Machine
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
              <CheckCircle className="h-3.5 w-3.5" />
              9 Decoy Services Active
            </span>
          </div>
        </div>

        {/* Database Management & Purge Data Action */}
        <div className="mt-6 border-t border-zinc-100 dark:border-zinc-900 pt-5 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-700 dark:text-zinc-300 font-mono">
              Live Threat Simulation &amp; Ingress Defense
            </h4>
            <p className="text-xs text-zinc-500 mt-0.5">
              Launch a live adversarial ingress attack with Canary Honeytoken tripwires streamed to SOC, or reset the dashboard to 0.
            </p>
            {clearSuccess && (
              <p className="text-xs font-bold text-emerald-500 mt-1">
                ✔ {clearSuccess}
              </p>
            )}
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleSimulateAttack}
              disabled={simulating || clearing}
              className="flex items-center gap-2 rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-2 text-xs font-bold text-amber-500 hover:bg-amber-500/20 transition active:scale-95 disabled:opacity-50 shadow-sm hover:shadow-amber-500/10"
              title={`Simulates a live adversarial attack against the active '${personas[activePersona]?.name.split(" (")[0]}' persona architecture.`}
            >
              <Zap className={`h-4 w-4 text-amber-500 ${simulating ? "animate-bounce" : ""}`} />
              {simulating ? "Simulating Live Ingress..." : `Simulate Attack (${personas[activePersona]?.name.split(" (")[0] || "Active"})`}
            </button>

            <button
              onClick={() => setIsConfirmOpen(true)}
              disabled={clearing || simulating}
              className="flex items-center gap-2 rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-2 text-xs font-bold text-rose-600 dark:text-rose-400 hover:bg-rose-500/20 transition active:scale-95 disabled:opacity-50"
            >
              <Trash2 className="h-4 w-4" />
              Clear Captured Data
            </button>
          </div>
        </div>
      </div>

      {/* Centered Modal Popup for Data Purge Confirmation (True Fullscreen Coverage) */}
      {isConfirmOpen && (
        <div className="fixed inset-0 top-0 left-0 w-screen h-screen z-[100] flex items-center justify-center bg-black/60 dark:bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
          <div className="relative w-full max-w-md rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-6 shadow-2xl space-y-5 animate-in zoom-in-95 duration-150">
            <div className="flex items-start gap-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-rose-500/10 dark:bg-rose-500/20 text-rose-600 dark:text-rose-400 border border-rose-500/20">
                <AlertTriangle className="h-6 w-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-base font-bold text-zinc-900 dark:text-white">
                  Purge Attacker Telemetry?
                </h3>
                <p className="text-xs leading-relaxed text-zinc-600 dark:text-zinc-400">
                  This will permanently delete all recorded attacker sessions, keystrokes, and honeypot telemetry from the database. All dashboard counters will reset to <span className="font-bold text-rose-500">0</span>.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setIsConfirmOpen(false)}
                disabled={clearing}
                className="rounded-xl border border-zinc-200 dark:border-zinc-800 px-4 py-2.5 text-xs font-semibold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-900 transition disabled:opacity-50"
              >
                Cancel
              </button>

              <button
                type="button"
                onClick={handleConfirmClear}
                disabled={clearing}
                className="flex items-center gap-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white px-5 py-2.5 text-xs font-bold shadow-lg shadow-rose-600/20 transition active:scale-95 disabled:opacity-50"
              >
                <Trash2 className="h-4 w-4" />
                {clearing ? "Purging Logs..." : "Yes, Purge Everything"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 2. Core Security Services Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* IP Threat Intelligence */}
        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-blue-50 dark:bg-blue-500/10 p-2 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-500/20">
                <Globe className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-zinc-900 dark:text-white text-sm">IP Threat Intelligence & Geolocation</h3>
            </div>
            <p className="mt-3 text-xs leading-relaxed text-zinc-600 dark:text-zinc-400">
              Autonomous IP enrichment engine querying maxmind/ip-api telemetry. Resolves attacker Country, City, Coordinates, ISP, ASN, and proxy/VPN flags with in-memory LRU caching.
            </p>
          </div>
          <div className="mt-5 rounded-lg bg-zinc-50 dark:bg-zinc-900 p-3 border border-zinc-200 dark:border-zinc-800 font-mono text-[11px] text-blue-600 dark:text-blue-400">
            GET /api/threat-intel/ip/&#123;ip_address&#125;
          </div>
        </div>

        {/* AutoShun Firewall Engine */}
        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-red-50 dark:bg-red-500/10 p-2 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-500/20">
                <Flame className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-zinc-900 dark:text-white text-sm">Auto-Shun Firewall Generator</h3>
            </div>
            <p className="mt-3 text-xs leading-relaxed text-zinc-600 dark:text-zinc-400">
              Calculates dynamic Attacker Risk Scores (0-100). Automatically generates <code className="text-red-500 font-mono">iptables</code>, <code className="text-red-500 font-mono">ufw</code>, and decoy NAT redirection rules when an attacker exceeds the risk threshold.
            </p>
          </div>
          <div className="mt-5 space-y-1.5">
            {firewallRules.map((rule, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between rounded bg-zinc-50 dark:bg-zinc-900 px-3 py-1.5 font-mono text-[10px] text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-800"
              >
                <span className="truncate">{rule}</span>
                <button
                  onClick={() => handleCopy(rule)}
                  className="ml-2 text-zinc-400 hover:text-zinc-900 dark:hover:text-white"
                  title="Copy Rule"
                >
                  {copiedRule === rule ? <Check className="h-3 w-3 text-emerald-500" /> : <Copy className="h-3 w-3" />}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Security Audit & Rate Limiting */}
        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-purple-50 dark:bg-purple-500/10 p-2 text-purple-600 dark:text-purple-400 border border-purple-200 dark:border-purple-500/20">
                <Lock className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-zinc-900 dark:text-white text-sm">Security Audit & Rate Limiting</h3>
            </div>
            <p className="mt-3 text-xs leading-relaxed text-zinc-600 dark:text-zinc-400">
              Enterprise Starlette middleware enforcing a 300 req/min rate limit per IP. Injects enterprise defense response headers (<code className="text-purple-600 dark:text-purple-400 font-mono">X-Frame-Options: DENY</code>, <code className="text-purple-600 dark:text-purple-400 font-mono">X-Content-Type-Options: nosniff</code>).
            </p>
          </div>
          <div className="mt-5 rounded-lg bg-zinc-50 dark:bg-zinc-900 p-3 border border-zinc-200 dark:border-zinc-800 font-mono text-[11px] text-purple-600 dark:text-purple-400">
            backend/middleware.py • SecurityAuditMiddleware
          </div>
        </div>

        {/* Deterministic MITRE ATT&CK */}
        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-emerald-50 dark:bg-emerald-500/10 p-2 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
                <Shield className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-zinc-900 dark:text-white text-sm">Deterministic MITRE ATT&CK Engine</h3>
            </div>
            <p className="mt-3 text-xs leading-relaxed text-zinc-600 dark:text-zinc-400">
              100% deterministic, rule-based cybersecurity analysis engine without external AI dependencies. Automatically maps captured payloads to Technique IDs (<code className="text-emerald-600 dark:text-emerald-400 font-mono">T1003</code>, <code className="text-emerald-600 dark:text-emerald-400 font-mono">T1213</code>, <code className="text-emerald-600 dark:text-emerald-400 font-mono">T1046</code>, <code className="text-emerald-600 dark:text-emerald-400 font-mono">T1059.004</code>).
            </p>
          </div>
          <div className="mt-5 rounded-lg bg-zinc-50 dark:bg-zinc-900 p-3 border border-zinc-200 dark:border-zinc-800 font-mono text-[11px] text-emerald-600 dark:text-emerald-400">
            GET /api/threat-intel/mitre/&#123;session_id&#125;
          </div>
        </div>
      </div>

      {/* 3. Multi-Protocol Honeypot Decoy Nodes & Adaptive Persona Engine */}
      <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-6 shadow-sm space-y-6">
        <div className="flex flex-wrap items-center justify-between border-b border-zinc-100 dark:border-zinc-800/80 pb-4 gap-4">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-blue-50 dark:bg-blue-500/10 p-2 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-500/20">
              <Database className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-semibold text-zinc-900 dark:text-white text-sm">Adaptive Server Personas & Decoy Mesh</h3>
              <p className="text-xs text-zinc-500">Anti-Fingerprinting Engine: dynamically mimics realistic single-purpose server architectures</p>
            </div>
          </div>

          {/* Active Persona Badge */}
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-zinc-500 uppercase tracking-wider">Active Persona:</span>
            <span className="rounded-lg bg-cyan-500/10 border border-cyan-500/30 px-3 py-1 font-mono text-xs font-bold text-cyan-600 dark:text-cyan-400">
              {personas[activePersona]?.name.split(" (")[0] || "Adaptive"}
            </span>
          </div>
        </div>

        {/* Adaptive Persona Switcher Controls */}
        <div className="rounded-xl bg-zinc-50 dark:bg-zinc-900/60 p-4 border border-zinc-200 dark:border-zinc-800">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-zinc-700 dark:text-zinc-300 flex items-center gap-1.5">
              <Shield className="h-3.5 w-3.5 text-cyan-500" />
              Switch Target Server Persona (Solves Honeypot Fingerprinting)
            </span>
            <span className="text-[10px] font-mono text-zinc-400">
              {personas[activePersona]?.simulated_os}
            </span>
          </div>

          <div className="grid gap-2.5 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-5">
            {Object.values(personas).map((p) => {
              const isSelected = activePersona === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => handleSwitchPersona(p.id)}
                  disabled={switchingPersona}
                  className={`p-3 text-left rounded-xl border transition-all text-xs flex flex-col justify-between space-y-2 ${
                    isSelected
                      ? "bg-cyan-500/10 border-cyan-500 text-cyan-900 dark:text-cyan-300 shadow-sm"
                      : "bg-white dark:bg-zinc-950 border-zinc-200 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-700 text-zinc-700 dark:text-zinc-300"
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="font-bold">{p.name.split(" (")[0]}</span>
                      {isSelected && (
                        <span className="h-2 w-2 rounded-full bg-cyan-500 animate-pulse" />
                      )}
                    </div>
                    <p className="mt-1 text-[11px] opacity-80 leading-relaxed line-clamp-2">
                      {p.description}
                    </p>
                  </div>
                  <div className="font-mono text-[10px] text-zinc-500 pt-1 border-t border-zinc-200/50 dark:border-zinc-800/60">
                    Ports: {p.active_ports.join(", ")}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Decoy Nodes Grid */}
        <div className="grid gap-3 sm:grid-cols-3">
          {decoyNodes.map((node) => {
            const isExposed = personas[activePersona]?.active_decoys.includes(node.name);
            return (
              <div
                key={node.name}
                className={`rounded-lg border p-4 space-y-2 transition-all ${
                  isExposed
                    ? "border-emerald-500/40 bg-zinc-50 dark:bg-zinc-900/60"
                    : "border-zinc-200 dark:border-zinc-800/50 bg-zinc-100/40 dark:bg-zinc-950/40 opacity-40"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-xs text-zinc-900 dark:text-white">{node.name}</span>
                  <span
                    className={`rounded px-2 py-0.5 font-mono text-[10px] font-bold border ${
                      isExposed
                        ? "bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-900/40"
                        : "bg-zinc-100 dark:bg-zinc-800 text-zinc-500 border-zinc-300 dark:border-zinc-700"
                    }`}
                  >
                    {isExposed ? "Listening" : "Masked"}
                  </span>
                </div>
                <div className="font-mono text-xs text-zinc-600 dark:text-zinc-400">
                  Port {node.port} / {node.protocol}
                </div>
                <p className="text-[11px] leading-relaxed text-zinc-600 dark:text-zinc-400">
                  {node.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* 4. Forensic Telemetry Exporters */}
      <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="rounded-lg bg-zinc-100 dark:bg-zinc-900 p-2 text-zinc-900 dark:text-zinc-100">
            <Download className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-semibold text-zinc-900 dark:text-white text-sm">Threat Intelligence Exporters & SIEM Integrations</h3>
            <p className="text-xs text-zinc-500">One-click downloads for SOC incident investigations</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <button
            onClick={() => handleExport("pdf")}
            disabled={downloading !== null}
            className="flex items-center justify-center gap-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 px-4 py-3 text-xs font-semibold text-zinc-800 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition disabled:opacity-50"
          >
            <FileText className="h-4 w-4" />
            {downloading === "pdf" ? "Generating..." : "Forensic PDF"}
          </button>

          <button
            onClick={() => handleExport("csv")}
            disabled={downloading !== null}
            className="flex items-center justify-center gap-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 px-4 py-3 text-xs font-semibold text-zinc-800 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition disabled:opacity-50"
          >
            <Database className="h-4 w-4" />
            {downloading === "csv" ? "Exporting..." : "Raw CSV Logs"}
          </button>

          <button
            onClick={() => handleExport("stix")}
            disabled={downloading !== null}
            className="flex items-center justify-center gap-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 px-4 py-3 text-xs font-semibold text-zinc-800 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition disabled:opacity-50"
          >
            <Shield className="h-4 w-4" />
            {downloading === "stix" ? "Building..." : "STIX 2.1 JSON"}
          </button>

          <button
            onClick={() => handleExport("cef")}
            disabled={downloading !== null}
            className="flex items-center justify-center gap-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 px-4 py-3 text-xs font-semibold text-zinc-800 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition disabled:opacity-50"
          >
            <Cpu className="h-4 w-4" />
            {downloading === "cef" ? "Exporting..." : "SIEM CEF Log"}
          </button>
        </div>
      </div>
    </div>
  );
}
