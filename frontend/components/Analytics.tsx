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

  useEffect(() => {
    const apiBase =
      process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
    const wsUrl =
      process.env.NEXT_PUBLIC_SENTINELTRAP_WS_URL || "ws://127.0.0.1:8000/ws";

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
  }, []);

  const protocolData = stats.protocol_distribution && stats.protocol_distribution.length > 0
    ? stats.protocol_distribution
    : [{ name: "SSH", value: 1 }];

  return (
    <div className="space-y-6">
      {/* 1. Primary Metrics Header Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total Attacker Sessions */}
        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-bold uppercase tracking-wider text-zinc-500 font-mono">
              Attacker Sessions
            </p>
            <div className="rounded-lg bg-cyan-500/10 dark:bg-cyan-500/15 p-2 text-cyan-500 dark:text-cyan-400 border border-cyan-500/30">
              <Users className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-3xl font-extrabold text-cyan-500 dark:text-cyan-400 font-mono drop-shadow-[0_0_10px_rgba(6,182,212,0.3)]">
            {loading ? "..." : stats.total_sessions}
          </p>
          <p className="mt-1 text-xs text-zinc-500">Trapped unique adversary entries</p>
        </div>

        {/* Total Forensic Commands */}
        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-bold uppercase tracking-wider text-zinc-500 font-mono">
              Forensic TTP Events
            </p>
            <div className="rounded-lg bg-emerald-500/10 dark:bg-emerald-500/15 p-2 text-emerald-500 dark:text-emerald-400 border border-emerald-500/30">
              <Activity className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-3xl font-extrabold text-emerald-500 dark:text-emerald-400 font-mono drop-shadow-[0_0_10px_rgba(52,211,153,0.3)]">
            {loading ? "..." : stats.total_events}
          </p>
          <p className="mt-1 text-xs text-zinc-500">MITRE-tagged telemetry keystrokes</p>
        </div>

        {/* Canary Honeytoken Tripwires */}
        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-bold uppercase tracking-wider text-zinc-500 font-mono">
              Canary Tripwires
            </p>
            <div className="rounded-lg bg-rose-500/10 dark:bg-rose-500/15 p-2 text-rose-500 dark:text-rose-400 border border-rose-500/30">
              <Key className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-3xl font-extrabold text-rose-500 dark:text-rose-400 font-mono drop-shadow-[0_0_10px_rgba(244,63,94,0.3)]">
            {loading ? "..." : stats.canary_tripped || 0}
          </p>
          <p className="mt-1 text-xs text-zinc-500">Exfiltration beacons dispatched</p>
        </div>

        {/* Multi-Protocol Decoy Mesh Status */}
        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-bold uppercase tracking-wider text-zinc-500 font-mono">
              Deception Mesh
            </p>
            <div className="rounded-lg bg-amber-500/10 dark:bg-amber-500/15 p-2 text-amber-500 dark:text-amber-400 border border-amber-500/30">
              <Radio className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-2xl font-extrabold text-zinc-900 dark:text-white font-mono flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
            9 Decoys Active
          </p>
          <p className="mt-1 text-xs text-zinc-500">VFS &amp; Adaptive Server Personas</p>
        </div>
      </div>

      {/* 2. Charts Row: Top Attacker Commands & Protocol Surface Distribution */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Top Commands Bar Chart (7 Cols) */}
        <div className="lg:col-span-7 rounded-xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="mb-4 flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800/80 pb-4">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-cyan-500/10 p-2 text-cyan-500 border border-cyan-500/30">
                  <Terminal className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-zinc-900 dark:text-white">
                    Top Executed Attacker Ingress Payloads
                  </h3>
                  <p className="text-xs text-zinc-500">TTP frequency distribution across in-memory sandbox</p>
                </div>
              </div>
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
          </div>
        </div>

        {/* Attack Vector Protocol Distribution (5 Cols) */}
        <div className="lg:col-span-5 rounded-xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="mb-4 flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800/80 pb-4">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-blue-500/10 p-2 text-blue-500 border border-blue-500/30">
                  <Layers className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-zinc-900 dark:text-white">
                    Protocol Attack Vectors
                  </h3>
                  <p className="text-xs text-zinc-500">Distribution across decoy listener ports</p>
                </div>
              </div>
            </div>

            <div className="h-64 w-full flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={protocolData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
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
            </div>

            {/* Protocol Legend */}
            <div className="flex flex-wrap items-center justify-center gap-3 pt-2 text-xs">
              {protocolData.map((item) => (
                <div key={item.name} className="flex items-center gap-1.5 font-mono text-[11px]">
                  <span
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: PROTOCOL_COLORS[item.name] || "#06b6d4" }}
                  />
                  <span className="text-zinc-700 dark:text-zinc-300 font-semibold">{item.name}</span>
                  <span className="text-zinc-400">({item.value})</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 3. Deep Threat Tables: Top Targeted Usernames & Global Adversary Origins */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Top Targeted Usernames */}
        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-6 shadow-sm">
          <div className="flex items-center gap-3 border-b border-zinc-100 dark:border-zinc-800/80 pb-4 mb-4">
            <div className="rounded-lg bg-amber-500/10 p-2 text-amber-500 border border-amber-500/30">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-zinc-900 dark:text-white">
                Top Targeted User Accounts
              </h3>
              <p className="text-xs text-zinc-500">Adversary dictionary &amp; brute-force targets</p>
            </div>
          </div>

          <div className="space-y-2.5">
            {stats.top_usernames.length === 0 ? (
              <p className="text-xs text-zinc-500 py-6 text-center">No authentication attempts recorded.</p>
            ) : (
              stats.top_usernames.map((u, i) => (
                <div
                  key={u.name || i}
                  className="flex items-center justify-between rounded-lg bg-zinc-50 dark:bg-zinc-900/70 px-3.5 py-2 border border-zinc-200 dark:border-zinc-800 text-xs"
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

        {/* Global Adversary Origins */}
        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-6 shadow-sm">
          <div className="flex items-center gap-3 border-b border-zinc-100 dark:border-zinc-800/80 pb-4 mb-4">
            <div className="rounded-lg bg-blue-500/10 p-2 text-blue-500 border border-blue-500/30">
              <Globe className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-zinc-900 dark:text-white">
                Top Adversary Geo Origins
              </h3>
              <p className="text-xs text-zinc-500">Origin countries identified via MaxMind/IP-API intelligence</p>
            </div>
          </div>

          <div className="space-y-2.5">
            {!stats.top_countries || stats.top_countries.length === 0 ? (
              <p className="text-xs text-zinc-500 py-6 text-center">No geographic locations resolved yet.</p>
            ) : (
              stats.top_countries.map((c, i) => (
                <div
                  key={c.country || i}
                  className="flex items-center justify-between rounded-lg bg-zinc-50 dark:bg-zinc-900/70 px-3.5 py-2 border border-zinc-200 dark:border-zinc-800 text-xs"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="font-mono text-[10px] text-zinc-400 font-bold">#{i + 1}</span>
                    <span className="font-semibold text-zinc-900 dark:text-zinc-100">{c.country}</span>
                  </div>
                  <span className="rounded bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 font-mono text-[10px] font-semibold text-emerald-600 dark:text-emerald-400">
                    {c.count} {c.count === 1 ? "source IP" : "source IPs"}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
