"use client";

import { useEffect, useState } from "react";
import {
  Globe,
  MapPin,
  Clock,
  User,
  Shield,
  Activity,
  Terminal,
  ChevronRight,
  RefreshCw,
} from "lucide-react";

type Session = {
  id: string;
  ip_address: string;
  country: string;
  city: string;
  username_attempted: string;
  password_attempted?: string;
  started_at: string;
  ended_at?: string;
};

type SessionSidebarProps = {
  onSelectSession?: (sessionId: string) => void;
  selectedSessionId?: string | null;
};

export default function SessionSidebar({
  onSelectSession,
  selectedSessionId,
}: SessionSidebarProps) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "";
    const wsUrl = process.env.NEXT_PUBLIC_SENTINELTRAP_WS_URL || "ws://127.0.0.1:8000/ws";

    let isMounted = true;
    let ws: WebSocket | null = null;

    const loadSessions = async () => {
      try {
        const response = await fetch(`${apiBase}/api/sessions`, { cache: "no-store" });
        if (response.ok && isMounted) {
          const data = await response.json();
          if (Array.isArray(data)) {
            setSessions(data);
          }
        }
      } catch (error) {
        // Handled silently
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    const setupWs = () => {
      try {
        ws = new WebSocket(wsUrl);
        ws.onmessage = () => {
          if (isMounted) loadSessions();
        };
        ws.onclose = () => {
          if (isMounted) setTimeout(setupWs, 2500);
        };
      } catch {
        // fallback to polling
      }
    };

    loadSessions();
    setupWs();
    const interval = setInterval(loadSessions, 1500);

    return () => {
      isMounted = false;
      clearInterval(interval);
      ws?.close();
    };
  }, []);

  return (
    <aside className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 shadow-sm">
      <div className="border-b border-zinc-200 dark:border-zinc-800 p-4">
        <h3 className="font-bold text-sm text-zinc-900 dark:text-white">
          Active Attacker Sessions
        </h3>
        <p className="text-xs text-zinc-600 dark:text-zinc-400 font-medium">
          Real-time intrusion tracking
        </p>
      </div>

      <div className="max-h-[550px] overflow-y-auto divide-y divide-zinc-200/80 dark:divide-zinc-800/60">
        {loading && sessions.length === 0 ? (
          <div className="p-8 text-center text-xs text-zinc-600 dark:text-zinc-400">
            Loading sessions...
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-8 text-center text-xs text-zinc-600 dark:text-zinc-400">
            No attacker sessions recorded.
          </div>
        ) : (
          sessions.map((session) => {
            const isSelected = selectedSessionId === session.id;

            return (
              <button
                key={session.id}
                onClick={() => onSelectSession?.(session.id)}
                className={`w-full p-4 text-left transition ${
                  isSelected
                    ? "bg-cyan-500/10 dark:bg-cyan-500/10 border-l-2 border-l-cyan-500"
                    : "hover:bg-zinc-100/70 dark:hover:bg-zinc-900/50"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1.5 min-w-0 flex-1">
                    <p className={`font-mono text-xs font-bold truncate ${
                      isSelected ? "text-cyan-700 dark:text-cyan-400" : "text-zinc-900 dark:text-zinc-100"
                    }`}>
                      {session.ip_address}
                    </p>

                    <div className="flex items-center gap-3 text-xs text-zinc-700 dark:text-zinc-400 font-medium">
                      <span className="flex items-center gap-1">
                        <Globe className="h-3.5 w-3.5 text-cyan-600 dark:text-cyan-400" />
                        {session.country}
                      </span>
                      <span className="flex items-center gap-1">
                        <MapPin className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />
                        {session.city}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-xs text-zinc-700 dark:text-zinc-300 font-medium">
                      <span className="truncate">
                        User: <strong className="text-zinc-950 dark:text-white font-mono">{session.username_attempted}</strong>
                      </span>
                      <span className="text-[10px] text-zinc-500 dark:text-zinc-400 font-mono">
                        {new Date(session.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>

                  <span className={`mt-1 h-2.5 w-2.5 rounded-full shrink-0 ${session.ended_at ? "bg-zinc-400 dark:bg-zinc-600" : "bg-emerald-500 dark:bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)] animate-pulse"}`} />
                </div>
              </button>
            );
          })
        )}
      </div>
    </aside>
  );
}
