"use client";

import { useState, useEffect } from "react";
import {
  ShieldCheck,
  LayoutDashboard,
  Users,
  Bell,
  BarChart3,
  Shield,
  Sun,
  Moon,
  Wifi,
  WifiOff,
} from "lucide-react";

type HeaderProps = {
  activePage: string;
  setActivePage: (page: string) => void;
  isDark: boolean;
  setIsDark: (dark: boolean) => void;
};

export default function Header({
  activePage,
  setActivePage,
  isDark,
  setIsDark,
}: HeaderProps) {
  const [connected, setConnected] = useState(false);

  const navigation = [
    { name: "Dashboard", icon: LayoutDashboard },
    { name: "Sessions", icon: Users },
    { name: "Alerts", icon: Bell },
    { name: "Analytics", icon: BarChart3 },
    { name: "Backend Features", icon: Shield },
  ];

  useEffect(() => {
    const wsUrl =
      process.env.NEXT_PUBLIC_SENTINELTRAP_WS_URL || "ws://127.0.0.1:8000/ws";
    const apiBase =
      process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

    let socket: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout;
    let isSubscribed = true;

    // Dual-check: WebSocket + HTTP health check fallback
    const checkHttpHealth = async () => {
      try {
        const res = await fetch(`${apiBase}/api/stats/overview`, { cache: "no-store" });
        if (res.ok && isSubscribed) {
          setConnected(true);
        }
      } catch {
        // Handled by WebSocket status
      }
    };

    const connectWebSocket = () => {
      if (!isSubscribed) return;
      try {
        socket = new WebSocket(wsUrl);
        socket.onopen = () => {
          if (isSubscribed) setConnected(true);
        };
        socket.onclose = () => {
          checkHttpHealth();
          if (isSubscribed) {
            reconnectTimeout = setTimeout(connectWebSocket, 3000);
          }
        };
        socket.onerror = () => {
          checkHttpHealth();
          socket?.close();
        };
      } catch {
        checkHttpHealth();
      }
    };

    checkHttpHealth();
    connectWebSocket();

    const healthInterval = setInterval(checkHttpHealth, 4000);

    return () => {
      isSubscribed = false;
      clearInterval(healthInterval);
      clearTimeout(reconnectTimeout);
      socket?.close();
    };
  }, []);

  const toggleTheme = () => {
    const newMode = !isDark;
    setIsDark(newMode);
    if (newMode) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full bg-zinc-50/80 dark:bg-black/80 px-6 py-4 backdrop-blur-md transition-colors duration-200">
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        {/* Brand Logo */}
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-cyan-400 via-indigo-500 to-fuchsia-500 text-black font-bold shadow-lg shadow-cyan-500/25">
            <ShieldCheck className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-extrabold tracking-tight bg-gradient-to-r from-zinc-900 via-zinc-800 to-zinc-700 dark:from-white dark:via-zinc-200 dark:to-zinc-400 bg-clip-text text-transparent">
              SentinelTrap
            </h1>
            <p className="text-[10px] font-bold text-cyan-600 dark:text-cyan-400 uppercase tracking-widest font-mono">
              OpenThreatLabs
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 rounded-xl border border-zinc-300/80 dark:border-zinc-800/80 bg-zinc-200/60 dark:bg-zinc-900/90 p-1">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.name;

            return (
              <button
                key={item.name}
                onClick={() => setActivePage(item.name)}
                className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-xs font-semibold transition ${
                  isActive
                    ? "bg-white dark:bg-zinc-800 text-cyan-600 dark:text-cyan-300 shadow-sm border border-zinc-200/80 dark:border-zinc-700/60 font-bold"
                    : "text-zinc-700 dark:text-zinc-400 hover:text-zinc-950 dark:hover:text-white"
                }`}
              >
                <Icon className={`h-3.5 w-3.5 ${isActive ? "text-cyan-600 dark:text-cyan-400" : "text-zinc-500 dark:text-zinc-400"}`} />
                {item.name}
              </button>
            );
          })}
        </nav>

        {/* Right Controls: Live Pill */}
        <div className="flex items-center gap-3">
          {/* Live Node Pill */}
          <div
            className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold ${
              connected
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 shadow-sm shadow-emerald-500/10"
                : "border-rose-500/30 bg-rose-500/10 text-rose-600 dark:text-rose-400"
            }`}
          >
            <span className={`h-2 w-2 rounded-full ${connected ? "bg-emerald-400 animate-pulse" : "bg-rose-500"}`} />
            <span className="text-[11px] font-mono uppercase tracking-wider">{connected ? "Live" : "Offline"}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
