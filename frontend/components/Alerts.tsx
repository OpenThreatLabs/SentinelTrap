"use client";

import { useEffect, useState } from "react";
import {
  Bell,
  ShieldAlert,
  AlertTriangle,
  Clock,
  Terminal,
  Search,
  Filter,
  RefreshCw,
} from "lucide-react";

type AlertItem = {
  id: string;
  session_id: string;
  event_type: string;
  input_data: string;
  output_data: string;
  timestamp: string;
  ip_address?: string;
};

export default function Alerts() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [severityFilter, setSeverityFilter] = useState<"ALL" | "CRITICAL" | "HIGH" | "MEDIUM" | "LOW">("ALL");

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "";

  const loadAlerts = async () => {
    try {
      const res = await fetch(`${apiBase}/api/events/alerts`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          setAlerts(data);
        }
      }
    } catch (err) {
      console.warn("Failed to load alerts feed:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
    const interval = setInterval(loadAlerts, 5000);
    return () => clearInterval(interval);
  }, []);

  const getSeverity = (eventType: string, inputData: string = "") => {
    const input = inputData.toLowerCase();
    if (
      eventType.includes("breach") ||
      eventType.includes("exploit") ||
      input.includes("sudo") ||
      input.includes("/etc/shadow") ||
      input.includes("rm -rf") ||
      input.includes("wget")
    ) {
      return {
        level: "CRITICAL",
        badge: "bg-red-500",
        color: "border-red-200 dark:border-red-500/20 bg-red-50/50 dark:bg-red-500/5",
        textColor: "text-red-600 dark:text-red-400",
      };
    }
    if (
      eventType.includes("unauthorized") ||
      input.includes("cat /etc/passwd") ||
      input.includes("nmap") ||
      input.includes("ssh") ||
      input.includes("sql")
    ) {
      return {
        level: "HIGH",
        badge: "bg-amber-500",
        color: "border-amber-200 dark:border-amber-500/20 bg-amber-50/50 dark:bg-amber-500/5",
        textColor: "text-amber-600 dark:text-amber-400",
      };
    }
    if (eventType.includes("scan") || input.includes("whoami") || input.includes("uname")) {
      return {
        level: "MEDIUM",
        badge: "bg-blue-500",
        color: "border-blue-200 dark:border-blue-500/20 bg-blue-50/50 dark:bg-blue-500/5",
        textColor: "text-blue-600 dark:text-blue-400",
      };
    }
    return {
      level: "LOW",
      badge: "bg-slate-400",
      color: "border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0f172a]",
      textColor: "text-slate-600 dark:text-slate-400",
    };
  };

  const filteredAlerts = alerts.filter((alert) => {
    const severity = getSeverity(alert.event_type, alert.input_data);
    const query = searchQuery.toLowerCase();

    const matchesQuery =
      alert.event_type.toLowerCase().includes(query) ||
      alert.input_data?.toLowerCase().includes(query) ||
      alert.output_data?.toLowerCase().includes(query) ||
      alert.ip_address?.toLowerCase().includes(query);

    if (!matchesQuery) return false;
    if (severityFilter !== "ALL" && severity.level !== severityFilter) return false;
    return true;
  });

  const criticalCount = alerts.filter((a) => getSeverity(a.event_type, a.input_data).level === "CRITICAL").length;
  const highCount = alerts.filter((a) => getSeverity(a.event_type, a.input_data).level === "HIGH").length;

  return (
    <div className="space-y-6">
      {/* Alert KPI Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-zinc-500 uppercase tracking-wider font-mono">
              Total Incident Alerts
            </span>
            <div className="rounded-lg bg-cyan-500/10 dark:bg-cyan-500/15 p-2 text-cyan-500 dark:text-cyan-400 border border-cyan-500/30 shadow-sm shadow-cyan-500/10">
              <Bell className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-3xl font-extrabold text-cyan-500 dark:text-cyan-400 font-mono drop-shadow-[0_0_10px_rgba(6,182,212,0.3)]">{alerts.length}</p>
        </div>

        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-rose-500 uppercase tracking-wider font-mono">
              Critical Threats
            </span>
            <div className="rounded-lg bg-rose-500/10 dark:bg-rose-500/15 p-2 text-rose-500 dark:text-rose-400 border border-rose-500/30 shadow-sm shadow-rose-500/10">
              <ShieldAlert className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-3xl font-extrabold text-rose-500 dark:text-rose-400 font-mono drop-shadow-[0_0_10px_rgba(244,63,94,0.3)]">{criticalCount}</p>
        </div>

        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-amber-500 uppercase tracking-wider font-mono">
              High Severity Probes
            </span>
            <div className="rounded-lg bg-amber-500/10 dark:bg-amber-500/15 p-2 text-amber-500 dark:text-amber-400 border border-amber-500/30 shadow-sm shadow-amber-500/10">
              <AlertTriangle className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-3xl font-extrabold text-amber-500 dark:text-amber-400 font-mono drop-shadow-[0_0_10px_rgba(245,158,11,0.3)]">{highCount}</p>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-4 shadow-sm">
        <div className="relative flex-1 min-w-[260px]">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            placeholder="Filter alerts by attack type, command, IP, or payload..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-zinc-300 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 pl-10 pr-4 py-2 text-xs text-zinc-900 dark:text-white placeholder-zinc-500 focus:border-cyan-500 focus:outline-none font-medium"
          />
        </div>

        {/* Severity Filter Pills */}
        <div className="flex items-center gap-2">
          <div className="flex rounded-lg border border-zinc-300 dark:border-zinc-800 bg-zinc-100 dark:bg-zinc-900 p-1">
            {(["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"] as const).map((lvl) => (
              <button
                key={lvl}
                onClick={() => setSeverityFilter(lvl)}
                className={`rounded-md px-2.5 py-1 text-[11px] font-bold transition ${
                  severityFilter === lvl
                    ? "bg-white dark:bg-zinc-800 text-cyan-700 dark:text-cyan-300 shadow-sm border border-zinc-200 dark:border-zinc-700"
                    : "text-zinc-700 dark:text-zinc-400 hover:text-zinc-950 dark:hover:text-white"
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>

          <button
            onClick={loadAlerts}
            title="Refresh Incident Alerts"
            className="rounded-lg border border-zinc-300 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-2 text-zinc-700 dark:text-zinc-300 hover:text-zinc-950 dark:hover:text-white"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Alert Feed Cards */}
      <div className="space-y-3">
        {loading && alerts.length === 0 ? (
          <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 py-16 text-center text-sm text-zinc-600 dark:text-zinc-400 font-medium">
            Scanning honeypot node security logs...
          </div>
        ) : filteredAlerts.length === 0 ? (
          <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 py-16 text-center text-sm text-zinc-600 dark:text-zinc-400">
            <AlertTriangle className="mx-auto h-8 w-8 text-zinc-400 mb-2" />
            <p className="font-semibold text-zinc-800 dark:text-zinc-200">No matching security alerts found.</p>
            <p className="mt-1 text-xs text-zinc-600 dark:text-zinc-400">
              Alerts populate in real-time when intrusion attempts occur.
            </p>
          </div>
        ) : (
          filteredAlerts.map((alert) => {
            const severity = getSeverity(alert.event_type, alert.input_data);

            return (
              <div
                key={alert.id}
                className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-5 transition shadow-sm hover:border-zinc-300 dark:hover:border-zinc-700"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-2 flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="flex items-center gap-1.5 font-bold text-xs text-zinc-900 dark:text-white">
                        <span className={`h-2 w-2 rounded-full ${severity.badge}`} />
                        {alert.event_type.replace(/_/g, " ").toUpperCase()}
                      </span>

                      <span className="rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-zinc-100 dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 border border-zinc-300 dark:border-zinc-800 font-mono">
                        {severity.level}
                      </span>

                      {alert.ip_address && (
                        <span className="font-mono text-xs font-bold text-zinc-900 dark:text-zinc-100 bg-zinc-100 dark:bg-zinc-900 px-2 py-0.5 rounded border border-zinc-300 dark:border-zinc-800">
                          Source: {alert.ip_address}
                        </span>
                      )}
                    </div>

                    {alert.input_data && (
                      <div className="flex items-center gap-2 rounded bg-zinc-900 dark:bg-black px-3 py-2 font-mono text-xs text-emerald-400 border border-zinc-800">
                        <Terminal className="h-3.5 w-3.5 shrink-0 text-zinc-400" />
                        <span className="truncate">{alert.input_data}</span>
                      </div>
                    )}

                    {alert.output_data && (
                      <div className="rounded bg-zinc-900/95 dark:bg-black/90 px-3 py-2 font-mono text-[11px] text-amber-400 whitespace-pre-wrap border border-zinc-800">
                        {alert.output_data}
                      </div>
                    )}

                    <div className="flex items-center gap-2 text-[11px] text-zinc-600 dark:text-zinc-400 font-mono font-medium">
                      <Clock className="h-3 w-3 text-zinc-500" />
                      <span>{new Date(alert.timestamp).toLocaleString()}</span>
                      <span>•</span>
                      <span className="text-[10px]">Session {alert.session_id.slice(0, 8)}…</span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
