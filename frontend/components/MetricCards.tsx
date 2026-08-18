"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  Command,
  ShieldAlert,
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
    const loadStats = async () => {
      try {
        const response = await fetch(
          "http://127.0.0.1:8000/api/stats/overview"
        );

        if (!response.ok) {
          throw new Error("Failed to fetch statistics");
        }

        const data = await response.json();

        setStats(data);
      } catch (error) {
        console.error("Unable to load dashboard statistics:", error);
      }
    };

    loadStats();

    // Refresh statistics every 5 seconds
    const interval = setInterval(loadStats, 5000);

    return () => clearInterval(interval);
  }, []);

  const cards = [
    {
      title: "Total Attacker Sessions",
      value: stats.total_sessions,
      icon: Activity,
    },
    {
      title: "Captured Commands / Events",
      value: stats.total_events,
      icon: Command,
    },
    {
      title: "Active Deception Traps Triggered",
      value: 0,
      icon: ShieldAlert,
    },
  ];

  return (
    <div className="grid gap-5 md:grid-cols-3">
      {cards.map((card) => {
        const Icon = card.icon;

        return (
          <div
            key={card.title}
            className="rounded-xl border border-slate-800 bg-[#0b1120] p-6"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-500">
                  {card.title}
                </p>

                <p className="mt-3 text-3xl font-bold text-white">
                  {card.value}
                </p>
              </div>

              <div className="rounded-lg bg-cyan-500/10 p-3">
                <Icon className="h-6 w-6 text-cyan-400" />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}