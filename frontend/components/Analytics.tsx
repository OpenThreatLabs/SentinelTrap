"use client";

import { useEffect, useState } from "react";
import {
  Users,
  Activity,
  Terminal,
  ShieldAlert,
  Globe,
  Radio,
  Zap,
  Layers,
  Key,
  ShieldCheck,
  Download,
  FileText,
  Table,
  Database,
  ArrowUpRight,
  Wifi,
  Crosshair,
  Server,
  Lock,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import CobeGlobe from "./CobeGlobe";

type OverviewStats = {
  total_sessions: number;
  total_events: number;
  top_usernames: { name: string; count: number }[];
  top_commands: { name: string; count: number }[];
  protocol_distribution?: { name: string; value: number }[];
  top_countries?: { country: string; count: number }[];
  canary_tripped?: number;
  deception_tripped?: number;
};

const PROTOCOL_COLORS: Record<string, string> = {
  SSH: "#06b6d4",
  HTTP: "#3b82f6",
  MySQL: "#f59e0b",
  Redis: "#ef4444",
  Telnet: "#8b5cf6",
  FTP: "#10b981",
  SMTP: "#ec4899",
  DNS: "#6366f1",
  RDP: "#14b8a6",
};

// Known MITRE ATT&CK Technique mappings for honeypot payloads
const MITRE_MAP: Record<string, { id: string; name: string }> = {
  "whoami": { id: "T1033", name: "System Owner/User Discovery" },
  "uname -a": { id: "T1082", name: "System Information Discovery" },
  "cat /etc/passwd": { id: "T1087.001", name: "Local Accounts Discovery" },
  "cat /etc/shadow": { id: "T1003.008", name: "/etc/passwd & /etc/shadow Credential Dumping" },
  "cat /root/.aws/credentials": { id: "T1552.001", name: "Credentials in Files (AWS)" },
  "crontab -l": { id: "T1053.003", name: "Scheduled Task/Cron Persistence" },
  "SHOW DATABASES;": { id: "T1082", name: "Database Structure Discovery" },
  "SAVE": { id: "T1565", name: "Data Manipulation / Persistence" },
};

export default function Analytics() {
  const [stats, setStats] = useState<OverviewStats>({
    total_sessions: 0,
    total_events: 0,
    top_usernames: [],
    top_commands: [],
    protocol_distribution: [],
    top_countries: [],
    canary_tripped: 0,
    deception_tripped: 0,
  });
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState<string | null>(null);

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "";
  const wsUrl =
    process.env.NEXT_PUBLIC_SENTINELTRAP_WS_URL ||
    (typeof window !== "undefined"
      ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/ws`
      : "");

  useEffect(() => {
    let isMounted = true;
    let ws: WebSocket | null = null;

    const loadOverview = async () => {
      try {
        const response = await fetch(`${apiBase}/api/stats/overview`, { cache: "no-store" });
        if (response.ok && isMounted) {
          const data = await response.json();
          if (data && typeof data === "object") {
            setStats(data);
          }
        }
      } catch {
        // Handled silently
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    const setupWs = () => {
      try {
        ws = new WebSocket(wsUrl);
        ws.onmessage = () => {
          if (isMounted) loadOverview();
        };
        ws.onclose = () => {
          if (isMounted) setTimeout(setupWs, 2500);
        };
      } catch {
        // fallback to polling
      }
    };

    loadOverview();
    setupWs();
    const interval = setInterval(loadOverview, 2000);

    return () => {
      isMounted = false;
      clearInterval(interval);
      ws?.close();
    };
  }, [apiBase, wsUrl]);

  const handleDownload = async (format: "pdf" | "csv" | "stix" | "cef") => {
    try {
      setDownloading(format);
      let url = `${apiBase}/api/reports/export?format=${format}`;
      let filename = `SentinelTrap_attack_logs.${format}`;

      if (format === "pdf") {
        url = `${apiBase}/api/reports/pdf`;
        filename = "SentinelTrap_Forensic_Incident_Report.pdf";
      } else if (format === "stix") {
        url = `${apiBase}/api/reports/stix`;
        filename = "SentinelTrap_STIX21_Threat_Bundle.json";
      } else if (format === "cef") {
        url = `${apiBase}/api/reports/cef`;
        filename = "SentinelTrap_SIEM_CEF.log";
      }

      const res = await fetch(url);
      if (!res.ok) throw new Error("Export failed");

      const blob = await res.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      console.error("Export failed:", err);
    } finally {
      setDownloading(null);
    }
  };

  const protocolData =
    stats.protocol_distribution && stats.protocol_distribution.length > 0
      ? stats.protocol_distribution.filter((p) => p.value > 0)
      : [];

  const totalThreatHits = stats.top_countries?.reduce((acc, c) => acc + c.count, 0) || 1;

  return (
    <div className="space-y-6">
      {/* 1. PRIMARY EXECUTIVE KPI METRIC CARDS */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total Attacker Sessions */}
        <div style={{ animationDelay: "0ms" }} className="animate-item-fade rounded-xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-5 shadow-sm transition-all duration-300 hover:border-cyan-500/40 hover:-translate-y-1 hover:shadow-lg hover:shadow-cyan-500/5 group">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-bold uppercase tracking-wider text-zinc-500 font-mono">
              Intercepted Adversaries
            </p>
            <div className="rounded-lg bg-cyan-500/10 dark:bg-cyan-500/15 p-2 text-cyan-500 dark:text-cyan-400 border border-cyan-500/30 transition-transform group-hover:scale-110">
              <Users className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-3xl font-extrabold text-cyan-500 dark:text-cyan-400 font-mono drop-shadow-[0_0_12px_rgba(6,182,212,0.3)]">
            {loading ? "..." : stats.total_sessions}
          </p>
          <div className="mt-2 flex items-center justify-between text-xs text-zinc-500 border-t border-zinc-100 dark:border-zinc-900 pt-2">
            <span>Trapped unique remote IPs</span>
            <span className="font-mono text-cyan-500 font-semibold">100% Ingress</span>
          </div>
        </div>

        {/* Forensic Keystrokes & TTP Events */}
        <div style={{ animationDelay: "80ms" }} className="animate-item-fade rounded-xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-5 shadow-sm transition-all duration-300 hover:border-emerald-500/40 hover:-translate-y-1 hover:shadow-lg hover:shadow-emerald-500/5 group">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-bold uppercase tracking-wider text-zinc-500 font-mono">
              Forensic TTP Events
            </p>
            <div className="rounded-lg bg-emerald-500/10 dark:bg-emerald-500/15 p-2 text-emerald-500 dark:text-emerald-400 border border-emerald-500/30 transition-transform group-hover:scale-110">
              <Activity className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-3xl font-extrabold text-emerald-500 dark:text-emerald-400 font-mono drop-shadow-[0_0_12px_rgba(52,211,153,0.3)]">
            {loading ? "..." : stats.total_events}
          </p>
          <div className="mt-2 flex items-center justify-between text-xs text-zinc-500 border-t border-zinc-100 dark:border-zinc-900 pt-2">
            <span>Deterministic TTP logs</span>
            <span className="font-mono text-emerald-500 font-semibold">Sandbox Active</span>
          </div>
        </div>

        {/* Canary Honeytoken Tripwires */}
        <div style={{ animationDelay: "160ms" }} className="animate-item-fade rounded-xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-5 shadow-sm transition-all duration-300 hover:border-rose-500/40 hover:-translate-y-1 hover:shadow-lg hover:shadow-rose-500/5 group">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-bold uppercase tracking-wider text-zinc-500 font-mono">
              Canary Tripwires
            </p>
            <div className="rounded-lg bg-rose-500/10 dark:bg-rose-500/15 p-2 text-rose-500 dark:text-rose-400 border border-rose-500/30 transition-transform group-hover:scale-110">
              <Key className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-3xl font-extrabold text-rose-500 dark:text-rose-400 font-mono drop-shadow-[0_0_12px_rgba(244,63,94,0.3)]">
            {loading ? "..." : stats.canary_tripped || 0}
          </p>
          <div className="mt-2 flex items-center justify-between text-xs text-zinc-500 border-t border-zinc-100 dark:border-zinc-900 pt-2">
            <span>Honeytoken alarms tripped</span>
            <span className="font-mono text-rose-500 font-semibold">Exfil Alert</span>
          </div>
        </div>

        {/* Deception Mesh Personas */}
        <div style={{ animationDelay: "240ms" }} className="animate-item-fade rounded-xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-5 shadow-sm transition-all duration-300 hover:border-amber-500/40 hover:-translate-y-1 hover:shadow-lg hover:shadow-amber-500/5 group">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-bold uppercase tracking-wider text-zinc-500 font-mono">
              Deception Mesh
            </p>
            <div className="rounded-lg bg-amber-500/10 dark:bg-amber-500/15 p-2 text-amber-500 dark:text-amber-400 border border-amber-500/30 transition-transform group-hover:scale-110">
              <Radio className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-3xl font-extrabold text-zinc-900 dark:text-white font-mono flex items-center gap-2">
            9 <span className="text-sm font-normal text-zinc-400 font-sans">Decoys</span>
          </p>
          <div className="mt-2 flex items-center justify-between text-xs text-zinc-500 border-t border-zinc-100 dark:border-zinc-900 pt-2">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              All Listeners Active
            </span>
            <span className="font-mono text-emerald-400 font-semibold">:22-:3389</span>
          </div>
        </div>
      </div>

      {/* 2. 3D THREAT GLOBE WITH PROTOCOL ATTACK SURFACE & GEOGRAPHIC INGRESS TELEMETRY ON THE RIGHT */}
      <div className="grid gap-6 lg:grid-cols-12 items-start">
        {/* Left Column (7 cols): 3D Threat Globe */}
        <div className="lg:col-span-7">
          <CobeGlobe className="h-full" />
        </div>

        {/* Right Column (5 cols): Protocol Attack Surface on top, Geographic Ingress Origins below */}
        <div className="lg:col-span-5 space-y-6">
          {/* Attack Vector Protocol Surface */}
          <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800/80 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="rounded-lg bg-blue-500/10 p-2 text-blue-500 border border-blue-500/30">
                  <Layers className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-zinc-900 dark:text-white">
                    Protocol Attack Surface
                  </h3>
                  <p className="text-[11px] text-zinc-500">Distribution across active decoy listeners</p>
                </div>
              </div>
              <span className="text-[10px] font-mono font-bold text-blue-400 bg-blue-500/10 border border-blue-500/30 px-2.5 py-0.5 rounded-full">
                {protocolData.length} Active {protocolData.length === 1 ? "Vector" : "Vectors"}
              </span>
            </div>

            <div className="h-48 w-full flex items-center justify-center">
              {protocolData.length === 0 ? (
                <div className="flex flex-col items-center justify-center text-xs text-zinc-500 text-center px-4">
                  <Layers className="h-7 w-7 text-zinc-600 mb-2 opacity-40" />
                  No protocol breaches captured yet.
                  <p className="text-[11px] text-zinc-600 mt-0.5">
                    Listeners on :22, :80, :3306, :6379 are armed and awaiting attacker ingress.
                  </p>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={protocolData}
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={70}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {protocolData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={PROTOCOL_COLORS[entry.name] || "#06b6d4"}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#09090b",
                        borderColor: "#27272a",
                        borderRadius: "8px",
                        color: "#ffffff",
                        fontSize: "12px",
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Protocol Legend */}
            {protocolData.length > 0 && (
              <div className="flex flex-wrap items-center justify-center gap-2.5 pt-3 text-xs border-t border-zinc-100 dark:border-zinc-800/80">
                {protocolData.map((item) => (
                  <div key={item.name} className="flex items-center gap-1.5 font-mono text-[11px]">
                    <span
                      className="h-2 w-2 rounded-full"
                      style={{ backgroundColor: PROTOCOL_COLORS[item.name] || "#06b6d4" }}
                    />
                    <span className="text-zinc-700 dark:text-zinc-300 font-semibold">{item.name}</span>
                    <span className="text-zinc-400">({item.value})</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Geographic Ingress Origins (Below Protocol Attack Surface) */}
          <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-5 shadow-sm">
            <div className="flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800/80 pb-3 mb-4">
              <div className="flex items-center gap-2.5">
                <div className="rounded-lg bg-blue-500/10 p-2 text-blue-500 border border-blue-500/30">
                  <Globe className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-zinc-900 dark:text-white">
                    Geographic Ingress Origins
                  </h3>
                  <p className="text-[11px] text-zinc-500">Adversary sources targeting India decoy</p>
                </div>
              </div>
              <span className="text-[10px] font-mono font-bold text-blue-400 bg-blue-500/10 border border-blue-500/30 px-2.5 py-0.5 rounded-full">
                {stats.top_countries?.length || 0} Nations
              </span>
            </div>

            {/* Origins List / Empty State */}
            {!stats.top_countries || stats.top_countries.length === 0 ? (
              <div className="py-8 text-center text-xs text-zinc-500">
                <Globe className="mx-auto h-7 w-7 text-zinc-600 mb-2 opacity-50" />
                No geographic coordinates resolved yet.
                <p className="text-[11px] text-zinc-600 mt-1">
                  Trigger an attack or wait for live decoy telemetry.
                </p>
              </div>
            ) : (
              <div className="space-y-3 max-h-[320px] overflow-y-auto pr-1">
                {stats.top_countries.map((c, i) => {
                  const pct = Math.round((c.count / totalThreatHits) * 100);
                  return (
                    <div
                      key={c.country || i}
                      className="rounded-xl border border-zinc-100 dark:border-zinc-800/80 bg-zinc-50/70 dark:bg-zinc-900/50 p-3 flex flex-col gap-2"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[10px] text-zinc-400 font-bold">#{i + 1}</span>
                          <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                            {c.country}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 font-mono text-[11px]">
                          <span className="text-emerald-500 dark:text-emerald-400 font-bold">
                            {c.count} {c.count === 1 ? "IP" : "IPs"}
                          </span>
                          <span className="text-zinc-400 text-[10px]">({pct}%)</span>
                        </div>
                      </div>
                      <div className="h-1.5 w-full rounded-full bg-zinc-200 dark:bg-zinc-800 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-emerald-400 transition-all duration-500"
                          style={{ width: `${Math.max(10, pct)}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 3. MITRE ATT&CK COMMAND PAYLOADS */}
      <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800/80 pb-4">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-cyan-500/10 p-2 text-cyan-500 border border-cyan-500/30">
              <Terminal className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-zinc-900 dark:text-white">
                Top Executed Attacker Ingress Payloads
              </h3>
              <p className="text-xs text-zinc-500">TTP frequency distribution correlated to MITRE ATT&amp;CK</p>
            </div>
          </div>
          <span className="rounded-full bg-cyan-500/10 border border-cyan-500/30 px-2.5 py-0.5 text-[10px] font-mono font-bold text-cyan-400">
            In-Memory VFS
          </span>
        </div>

        <div className="h-64 w-full">
          {stats.top_commands.length === 0 ? (
            <div className="flex h-full items-center justify-center text-xs text-zinc-500">
              No forensic commands recorded yet. Launch a simulated attack to view live data.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.top_commands} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#71717a" opacity={0.2} vertical={false} />
                <XAxis dataKey="name" stroke="#a1a1aa" tick={{ fill: "#71717a", fontSize: 10 }} interval={0} angle={-15} textAnchor="end" />
                <YAxis stroke="#a1a1aa" tick={{ fill: "#71717a", fontSize: 11 }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#09090b",
                    borderColor: "#27272a",
                    borderRadius: "8px",
                    color: "#ffffff",
                    fontSize: "12px",
                  }}
                />
                <Bar dataKey="count" fill="#06b6d4" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* MITRE ATT&CK Tagged Command Badges */}
        {stats.top_commands.length > 0 && (
          <div className="mt-4 pt-3 border-t border-zinc-100 dark:border-zinc-800/80 flex flex-wrap gap-2">
            {stats.top_commands.slice(0, 8).map((cmd) => {
              const mitre = MITRE_MAP[cmd.name];
              return (
                <div
                  key={cmd.name}
                  className="flex items-center gap-1.5 rounded bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 px-2 py-1 text-[10px] font-mono"
                >
                  <span className="font-bold text-zinc-800 dark:text-zinc-200">{cmd.name}</span>
                  {mitre ? (
                    <span className="rounded bg-rose-500/15 text-rose-400 px-1 py-0.2 font-semibold">
                      {mitre.id}
                    </span>
                  ) : (
                    <span className="rounded bg-zinc-800 text-zinc-400 px-1 py-0.2">
                      T1059
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 5. CREDENTIAL INGRESS & CANARY HONEYTOKEN AUDIT */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Top Targeted User Accounts */}
        <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-6 shadow-sm">
          <div className="flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800/80 pb-4 mb-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-amber-500/10 p-2 text-amber-500 border border-amber-500/30">
                <ShieldAlert className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-zinc-900 dark:text-white">
                  Top Targeted User Accounts
                </h3>
                <p className="text-xs text-zinc-500">Adversary brute-force dictionary reconnaissance</p>
              </div>
            </div>
            <span className="text-[10px] font-mono font-bold text-amber-500 bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded-full">
              Auth Ingress
            </span>
          </div>

          <div className="space-y-2.5">
            {stats.top_usernames.length === 0 ? (
              <p className="text-xs text-zinc-500 py-6 text-center">No authentication attempts recorded.</p>
            ) : (
              stats.top_usernames.map((u, i) => (
                <div
                  key={u.name || i}
                  className="flex items-center justify-between rounded-lg bg-zinc-50 dark:bg-zinc-900/70 px-3.5 py-2.5 border border-zinc-200 dark:border-zinc-800 text-xs"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="font-mono text-[10px] text-zinc-400 font-bold">#{i + 1}</span>
                    <span className="font-mono font-bold text-zinc-900 dark:text-zinc-100">{u.name}</span>
                  </div>
                  <span className="rounded bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 font-mono text-[10px] font-semibold text-cyan-600 dark:text-cyan-400">
                    {u.count} {u.count === 1 ? "attempt" : "attempts"}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Canary Honeytoken Tripwire Audit */}
        <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-6 shadow-sm">
          <div className="flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800/80 pb-4 mb-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-rose-500/10 p-2 text-rose-500 border border-rose-500/30">
                <Key className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-zinc-900 dark:text-white">
                  Canary Honeytoken Traps &amp; Tripwires
                </h3>
                <p className="text-xs text-zinc-500">Automated sensitive file access detection</p>
              </div>
            </div>
            <span className="text-[10px] font-mono font-bold text-rose-400 bg-rose-500/10 border border-rose-500/30 px-2 py-0.5 rounded-full">
              {stats.canary_tripped || 0} Tripped
            </span>
          </div>

          <div className="space-y-3 text-xs">
            {/* AWS Canary */}
            <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800">
              <div className="flex items-center gap-2.5">
                <span className="h-2 w-2 rounded-full bg-rose-500" />
                <div>
                  <div className="font-mono font-bold text-zinc-900 dark:text-zinc-100">
                    /root/.aws/credentials
                  </div>
                  <div className="text-[11px] text-zinc-500">AWS Access Key ID / Secret Exfiltration Token</div>
                </div>
              </div>
              <span className="font-mono text-[10px] text-rose-400 font-semibold bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded">
                Active Trap
              </span>
            </div>

            {/* DB Canary */}
            <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800">
              <div className="flex items-center gap-2.5">
                <span className="h-2 w-2 rounded-full bg-amber-500" />
                <div>
                  <div className="font-mono font-bold text-zinc-900 dark:text-zinc-100">
                    payments_db.credit_cards
                  </div>
                  <div className="text-[11px] text-zinc-500">Canary SQL Table with Honey-Records</div>
                </div>
              </div>
              <span className="font-mono text-[10px] text-amber-400 font-semibold bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded">
                Active Trap
              </span>
            </div>

            {/* Cron Persistence Canary */}
            <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800">
              <div className="flex items-center gap-2.5">
                <span className="h-2 w-2 rounded-full bg-cyan-500" />
                <div>
                  <div className="font-mono font-bold text-zinc-900 dark:text-zinc-100">
                    /var/spool/cron/crontabs
                  </div>
                  <div className="text-[11px] text-zinc-500">Persistence Mechanism Unauthorized Write Trap</div>
                </div>
              </div>
              <span className="font-mono text-[10px] text-cyan-400 font-semibold bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 rounded">
                Active Trap
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 5. SOC THREAT INTELLIGENCE & FORENSIC EXPORTS (AT BOTTOM) */}
      <div className="flex flex-col gap-4 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-5 shadow-sm md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3.5">
          <div className="relative flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shadow-[0_0_20px_rgba(6,182,212,0.25)]">
            <Crosshair className="h-6 w-6 animate-pulse" />
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500" />
            </span>
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-base font-bold tracking-tight text-zinc-900 dark:text-white">
                SOC Threat Intelligence &amp; Analytics
              </h2>
              <span
                className={`rounded-full px-2.5 py-0.5 text-[10px] font-mono font-bold border ${
                  stats.total_sessions > 0
                    ? "bg-rose-500/15 border-rose-500/40 text-rose-400"
                    : "bg-emerald-500/15 border-emerald-500/40 text-emerald-400"
                }`}
              >
                {stats.total_sessions > 0 ? "DEFCON 2 • ELEVATED INGRESS" : "DEFCON 5 • MONITORING"}
              </span>
            </div>
            <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
              Real-time multi-protocol honeypot telemetry, MITRE ATT&amp;CK mapping, and canary token forensics.
            </p>
          </div>
        </div>

        {/* Quick SIEM / Forensic Exports */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => handleDownload("pdf")}
            disabled={downloading !== null}
            className="flex items-center gap-1.5 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-1.5 text-xs font-mono font-semibold text-rose-400 transition-all hover:bg-rose-500/20 disabled:opacity-50 cursor-pointer"
          >
            <FileText className="h-3.5 w-3.5" />
            {downloading === "pdf" ? "Exporting..." : "Forensic PDF"}
          </button>
          <button
            onClick={() => handleDownload("stix")}
            disabled={downloading !== null}
            className="flex items-center gap-1.5 rounded-lg border border-purple-500/30 bg-purple-500/10 px-3 py-1.5 text-xs font-mono font-semibold text-purple-400 transition-all hover:bg-purple-500/20 disabled:opacity-50 cursor-pointer"
          >
            <ShieldCheck className="h-3.5 w-3.5" />
            {downloading === "stix" ? "Building..." : "STIX 2.1"}
          </button>
          <button
            onClick={() => handleDownload("cef")}
            disabled={downloading !== null}
            className="flex items-center gap-1.5 rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-3 py-1.5 text-xs font-mono font-semibold text-cyan-400 transition-all hover:bg-cyan-500/20 disabled:opacity-50 cursor-pointer"
          >
            <Database className="h-3.5 w-3.5" />
            {downloading === "cef" ? "Exporting..." : "SIEM CEF"}
          </button>
          <button
            onClick={() => handleDownload("csv")}
            disabled={downloading !== null}
            className="flex items-center gap-1.5 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-mono font-semibold text-emerald-400 transition-all hover:bg-emerald-500/20 disabled:opacity-50 cursor-pointer"
          >
            <Table className="h-3.5 w-3.5" />
            {downloading === "csv" ? "Exporting..." : "Raw CSV"}
          </button>
        </div>
      </div>
    </div>
  );
}
