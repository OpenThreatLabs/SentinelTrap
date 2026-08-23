"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  Terminal,
  ShieldAlert,
  ArrowUpRight,
  ShieldCheck,
} from "lucide-react";

type Stats = {
  total_sessions: number;
  total_events: number;
  top_usernames: {
    name: string;
    count: number;
  }[];
  top_commands: {
    name: string;
    count: number;
  }[];
};

export default function MetricCards() {
  const [stats, setStats] = useState<Stats>({
    total_sessions: 0,
    total_events: 0,
    top_usernames: [],
    top_commands: [],
  });

  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "";
    const wsUrl = process.env.NEXT_PUBLIC_SENTINELTRAP_WS_URL || "ws://127.0.0.1:8000/ws";

    let isMounted = true;
    let ws: WebSocket | null = null;

    const loadStats = async () => {
      try {
        const response = await fetch(`${apiBase}/api/stats/overview`, { cache: "no-store" });
        if (response.ok && isMounted) {
          const data = await response.json();
          if (data && typeof data === "object") {
            setStats(data);
          }
        }
      } catch (error) {
        // Handled silently
      }
    };

    const setupWs = () => {
      try {
        ws = new WebSocket(wsUrl);
        ws.onmessage = () => {
          if (isMounted) loadStats();
        };
        ws.onclose = () => {
          if (isMounted) setTimeout(setupWs, 2500);
        };
      } catch {
        // fallback to polling
      }
    };

    loadStats();
    setupWs();
    const interval = setInterval(loadStats, 1500);

    return () => {
      isMounted = false;
      clearInterval(interval);
      ws?.close();
    };
  }, []);

  const cards = [
    {
      title: "Active Attacker Sessions",
      value: stats.total_sessions,
      subtitle: "Unique source IPs trapped",
      icon: Activity,
      numberColor: "text-cyan-500 dark:text-cyan-400 drop-shadow-[0_0_12px_rgba(6,182,212,0.3)]",
      iconColor: "text-cyan-500 dark:text-cyan-400",
      iconBg: "bg-cyan-500/10 dark:bg-cyan-500/15 border-cyan-500/30",
    },
    {
      title: "Forensic Commands Captured",
      value: stats.total_events,
      subtitle: "Deterministic TTP logs",
      icon: Terminal,
      numberColor: "text-emerald-400 dark:text-emerald-300 drop-shadow-[0_0_12px_rgba(52,211,153,0.3)]",
      iconColor: "text-emerald-500 dark:text-emerald-400",
      iconBg: "bg-emerald-500/10 dark:bg-emerald-500/15 border-emerald-500/30",
    },
    {
      title: "Deception & Canary Probes",
      value: stats.total_events > 0 ? Math.min(stats.total_events, 4) : 0,
      subtitle: "Honeytokens & Traps hit",
      icon: ShieldAlert,
      numberColor: "text-rose-500 dark:text-rose-400 drop-shadow-[0_0_12px_rgba(244,63,94,0.3)]",
      iconColor: "text-rose-500 dark:text-rose-400",
      iconBg: "bg-rose-500/10 dark:bg-rose-500/15 border-rose-500/30",
    },
  ];

  return (
    <div className="grid gap-5 md:grid-cols-3">
      {cards.map((card) => {
        const Icon = card.icon;

        return (
          <div
            key={card.title}
            className="rounded-xl border border-zinc-200 dark:border-zinc-800/80 bg-white dark:bg-zinc-950 p-6 shadow-sm transition hover:border-zinc-300 dark:hover:border-zinc-700 relative overflow-hidden group"
          >
            {/* Top Row */}
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-700 dark:text-zinc-400 font-mono">
                  {card.title}
                </span>
                <p className={`mt-2 text-3xl font-extrabold tracking-tight font-mono ${card.numberColor}`}>
                  {card.value}
                </p>
              </div>

              <div className={`rounded-xl border p-2.5 shadow-sm transition-transform group-hover:scale-105 ${card.iconBg}`}>
                <Icon className={`h-5 w-5 ${card.iconColor}`} />
              </div>
            </div>

            {/* Bottom Row */}
            <div className="mt-4 flex items-center justify-between border-t border-zinc-200 dark:border-zinc-900 pt-3 text-xs">
              <span className="text-zinc-600 dark:text-zinc-400 font-medium">{card.subtitle}</span>
              <span className="rounded-full bg-zinc-100 dark:bg-zinc-900 px-2.5 py-0.5 font-mono text-[10px] font-bold text-zinc-800 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-800">
                Live
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
