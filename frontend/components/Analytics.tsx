"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  Terminal,
  Users,
  TrendingUp,
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

export default function Analytics() {
  const [stats, setStats] = useState<Stats>({
    total_sessions: 0,
    total_events: 0,
    top_usernames: [],
    top_commands: [],
  });

  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        const response = await fetch(
          "http://127.0.0.1:8000/api/stats/overview"
        );

        if (!response.ok) {
          throw new Error("Failed to load analytics");
        }

        const data = await response.json();
        setStats(data);
      } catch (error) {
        console.error("Analytics error:", error);
      }
    };

    loadAnalytics();

    const interval = setInterval(loadAnalytics, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      {/* Overview */}
      <div className="grid gap-5 md:grid-cols-3">
        <div className="rounded-xl border border-slate-800 bg-[#0b1120] p-6">
          <Users className="h-6 w-6 text-cyan-400" />

          <p className="mt-4 text-sm text-slate-500">
            Attacker Sessions
          </p>

          <p className="mt-2 text-3xl font-bold">
            {stats.total_sessions}
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-[#0b1120] p-6">
          <Activity className="h-6 w-6 text-cyan-400" />

          <p className="mt-4 text-sm text-slate-500">
            Total Events
          </p>

          <p className="mt-2 text-3xl font-bold">
            {stats.total_events}
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-[#0b1120] p-6">
          <TrendingUp className="h-6 w-6 text-cyan-400" />

          <p className="mt-4 text-sm text-slate-500">
            Monitoring Status
          </p>

          <p className="mt-2 text-xl font-bold text-emerald-400">
            Active
          </p>
        </div>
      </div>

      {/* Top Usernames */}
      <div className="rounded-xl border border-slate-800 bg-[#0b1120] p-6">
        <div className="flex items-center gap-3">
          <Users className="h-5 w-5 text-cyan-400" />

          <h2 className="font-semibold">
            Most Targeted Usernames
          </h2>
        </div>

        {stats.top_usernames.length === 0 ? (
          <p className="mt-6 text-sm text-slate-500">
            No username attack data available.
          </p>
        ) : (
          <div className="mt-5 space-y-3">
            {stats.top_usernames.map((user) => (
              <div
                key={user.name}
                className="flex items-center justify-between rounded-lg bg-slate-900 p-4"
              >
                <span className="font-mono text-sm text-slate-300">
                  {user.name}
                </span>

                <span className="text-sm text-cyan-400">
                  {user.count} attempts
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Top Commands */}
      <div className="rounded-xl border border-slate-800 bg-[#0b1120] p-6">
        <div className="flex items-center gap-3">
          <Terminal className="h-5 w-5 text-cyan-400" />

          <h2 className="font-semibold">
            Most Executed Commands
          </h2>
        </div>

        {stats.top_commands.length === 0 ? (
          <p className="mt-6 text-sm text-slate-500">
            No command execution data available.
          </p>
        ) : (
          <div className="mt-5 space-y-3">
            {stats.top_commands.map((command) => (
              <div
                key={command.name}
                className="flex items-center justify-between rounded-lg bg-slate-900 p-4"
              >
                <span className="font-mono text-sm text-slate-300">
                  {command.name}
                </span>

                <span className="text-sm text-cyan-400">
                  {command.count} executions
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}