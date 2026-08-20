"use client";

import { useEffect, useState } from "react";
import {
  Users,
  Activity,
  Terminal,
  TrendingUp,
  BarChart3,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

type OverviewStats = {
  total_sessions: number;
  total_events: number;
  top_usernames: { name: string; count: number }[];
  top_commands: { name: string; count: number }[];
};

export default function Analytics() {
  const [stats, setStats] = useState<OverviewStats>({
    total_sessions: 0,
    total_events: 0,
    top_usernames: [],
    top_commands: [],
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const apiBase =
      process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

    const loadOverview = async () => {
      try {
        const response = await fetch(`${apiBase}/api/stats/overview`);
        if (response.ok) {
          const data = await response.json();
          if (data && typeof data === "object") {
            setStats(data);
          }
        }
      } catch (error) {
        console.warn("Analytics overview not reached yet:", error);
      } finally {
        setLoading(false);
      }
    };

    loadOverview();
    const interval = setInterval(loadOverview, 5000);
    return () => clearInterval(interval);
  }, []);

  const chartData = stats.top_commands;

  return (
    <div className="space-y-6">
      {/* Overview Stat Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-bold uppercase tracking-wider text-zinc-500 font-mono">
              Total Sessions
            </p>
            <div className="rounded-lg bg-cyan-500/10 dark:bg-cyan-500/15 p-2 text-cyan-500 dark:text-cyan-400 border border-cyan-500/30 shadow-sm shadow-cyan-500/10">
              <Users className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-3xl font-extrabold text-cyan-500 dark:text-cyan-400 font-mono drop-shadow-[0_0_10px_rgba(6,182,212,0.3)]">
            {loading ? "..." : stats.total_sessions}
          </p>
          <p className="mt-1 text-xs text-zinc-500">Trapped adversarial IPs</p>
        </div>

        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-bold uppercase tracking-wider text-zinc-500 font-mono">
              Commands Logged
            </p>
            <div className="rounded-lg bg-emerald-500/10 dark:bg-emerald-500/15 p-2 text-emerald-500 dark:text-emerald-400 border border-emerald-500/30 shadow-sm shadow-emerald-500/10">
              <Activity className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-3xl font-extrabold text-emerald-500 dark:text-emerald-400 font-mono drop-shadow-[0_0_10px_rgba(52,211,153,0.3)]">
            {loading ? "..." : stats.total_events}
          </p>
          <p className="mt-1 text-xs text-zinc-500">Deterministic TTP events</p>
        </div>

        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-bold uppercase tracking-wider text-zinc-500 font-mono">
              Deception Engine
            </p>
            <div className="rounded-lg bg-rose-500/10 dark:bg-rose-500/15 p-2 text-rose-500 dark:text-rose-400 border border-rose-500/30 shadow-sm shadow-rose-500/10">
              <TrendingUp className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-3xl font-extrabold text-rose-500 dark:text-rose-400 font-mono flex items-center gap-2 drop-shadow-[0_0_10px_rgba(244,63,94,0.3)]">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
            Active
          </p>
          <p className="mt-1 text-xs text-zinc-500">9 Listener Daemons</p>
        </div>
      </div>

      {/* Chart */}
      <div className="rounded-xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-6 shadow-sm">
        <div className="mb-6 flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800/80 pb-4">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-cyan-500/10 p-2 text-cyan-500 border border-cyan-500/30">
              <Terminal className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-zinc-900 dark:text-white">
                Top Executed Attacker Commands
              </h3>
              <p className="text-xs text-zinc-500">TTP frequency distribution across honeypots</p>
            </div>
          </div>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#71717a" opacity={0.2} vertical={false} />
              <XAxis dataKey="name" stroke="#a1a1aa" tick={{ fill: "#71717a", fontSize: 11 }} />
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
        </div>
      </div>
    </div>
  );
}
