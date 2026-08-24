"use client";

import { useEffect, useState } from "react";
import {
  Search,
  Globe,
  MapPin,
  Clock,
  User,
  Activity,
  Terminal,
  FileText,
  AlertTriangle,
  RefreshCw,
  ChevronRight,
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

type EventItem = {
  id: string;
  session_id: string;
  event_type: string;
  input_data: string;
  output_data: string;
  timestamp: string;
};

export default function SessionsView() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<"all" | "active" | "closed">("all");

  const apiBase =
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

  const loadSessions = async () => {
    try {
      const res = await fetch(`${apiBase}/api/sessions`, { cache: "no-store" });
      if (res.ok) {
        const data: Session[] = await res.json();
        if (Array.isArray(data)) {
          setSessions(data);
          // Only auto-select the first session if none was selected yet
          setSelectedSession((prev) => {
            if (!prev && data.length > 0) return data[0];
            if (prev) {
              const stillExists = data.find((s) => s.id === prev.id);
              return stillExists || (data.length > 0 ? data[0] : null);
            }
            return null;
          });
        }
      }
    } catch (err) {
      // handled silently
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_SENTINELTRAP_WS_URL || "ws://127.0.0.1:8000/ws";
    let isMounted = true;
    let ws: WebSocket | null = null;

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

  const selectedSessionId = selectedSession?.id;

  useEffect(() => {
    if (!selectedSessionId) {
      setEvents([]);
      return;
    }

    let isMounted = true;

    const loadEvents = async (showLoader = false) => {
      if (showLoader) setEventsLoading(true);
      try {
        const res = await fetch(`${apiBase}/api/events/session/${selectedSessionId}`, { cache: "no-store" });
        if (res.ok && isMounted) {
          const data = await res.json();
          if (Array.isArray(data)) {
            setEvents(data);
          }
        }
      } catch (err) {
        // handled silently
      } finally {
        if (isMounted && showLoader) setEventsLoading(false);
      }
    };

    // Show spinner only on initial session click, then silently sync in background
    loadEvents(true);
    const interval = setInterval(() => loadEvents(false), 2000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [selectedSessionId]);

  const filteredSessions = sessions.filter((s) => {
    const query = searchQuery.toLowerCase();
    const matchesSearch =
      s.ip_address.toLowerCase().includes(query) ||
      s.username_attempted.toLowerCase().includes(query) ||
      s.country.toLowerCase().includes(query) ||
      s.city.toLowerCase().includes(query);

    if (!matchesSearch) return false;
    if (filterType === "active") return !s.ended_at;
    if (filterType === "closed") return !!s.ended_at;
    return true;
  });

  const handleDownloadPdf = (sessionId: string) => {
    window.open(`${apiBase}/api/export/pdf/${sessionId}`, "_blank");
  };

  return (
    <div className="space-y-6">
      {/* Search & Filter Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-4 shadow-sm">
        {/* Search Input */}
        <div className="relative flex-1 min-w-[260px]">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
          <input
            type="text"
            placeholder="Search by IP, username, country, city..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 pl-10 pr-4 py-2 text-xs text-zinc-900 dark:text-white placeholder-zinc-400 focus:border-zinc-500 focus:outline-none"
          />
        </div>

        {/* Filter Pills & Refresh */}
        <div className="flex items-center gap-2">
          <div className="flex rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-100 dark:bg-zinc-900 p-1">
            {(["all", "active", "closed"] as const).map((type) => (
              <button
                key={type}
                onClick={() => setFilterType(type)}
                className={`rounded-md px-3 py-1 text-xs font-semibold capitalize transition ${
                  filterType === type
                    ? "bg-white dark:bg-zinc-800 text-zinc-900 dark:text-white shadow-sm"
                    : "text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white"
                }`}
              >
                {type}
              </button>
            ))}
          </div>

          <button
            onClick={loadSessions}
            title="Refresh Sessions"
            className="rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-2 text-zinc-500 hover:text-zinc-900 dark:hover:text-white"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Main 2-Column Grid */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Left Column: Sessions List (5 Cols) */}
        <div className="lg:col-span-5 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 overflow-hidden flex flex-col h-[650px] shadow-sm">
          <div className="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/50 px-5 py-3.5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-zinc-700 dark:text-zinc-300" />
              <h3 className="font-semibold text-xs text-zinc-900 dark:text-white">
                Recorded Sessions ({filteredSessions.length})
              </h3>
            </div>
            <span className="text-[10px] uppercase font-semibold text-zinc-500 font-mono">
              Live Database
            </span>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-zinc-100 dark:divide-zinc-800/60">
            {loading ? (
              <div className="py-16 text-center text-xs text-zinc-500">
                Loading captured sessions...
              </div>
            ) : filteredSessions.length === 0 ? (
              <div className="py-16 text-center text-xs text-zinc-500">
                No matching attacker sessions found.
              </div>
            ) : (
              filteredSessions.map((session) => {
                const isSelected = selectedSession?.id === session.id;
                return (
                  <button
                    key={session.id}
                    onClick={() => setSelectedSession(session)}
                    className={`w-full p-4 text-left transition flex items-center justify-between gap-3 ${
                      isSelected
                        ? "bg-zinc-100 dark:bg-zinc-900 border-l-2 border-l-zinc-900 dark:border-l-white"
                        : "hover:bg-zinc-50 dark:hover:bg-zinc-900/50"
                    }`}
                  >
                    <div className="space-y-1.5 min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-zinc-900 dark:text-zinc-100 truncate">
                          {session.ip_address}
                        </span>
                        <span
                          className={`h-2 w-2 rounded-full shrink-0 ${
                            session.ended_at ? "bg-zinc-400 dark:bg-zinc-600" : "bg-emerald-500"
                          }`}
                          title={session.ended_at ? "Closed" : "Active Session"}
                        />
                      </div>

                      <div className="flex items-center gap-3 text-xs text-zinc-500 dark:text-zinc-400">
                        <span className="flex items-center gap-1">
                          <Globe className="h-3.5 w-3.5" />
                          {session.country}
                        </span>
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3.5 w-3.5" />
                          {session.city}
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-xs text-zinc-600 dark:text-zinc-400">
                        <span className="truncate">
                          User: <strong className="text-zinc-900 dark:text-white font-mono">{session.username_attempted}</strong>
                        </span>
                        <span className="text-[10px] text-zinc-400 font-mono">
                          {new Date(session.started_at).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>
                    </div>

                    <ChevronRight className={`h-4 w-4 shrink-0 transition ${isSelected ? "text-zinc-900 dark:text-white" : "text-zinc-400"}`} />
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Session Deep-Dive & Forensic Timeline (7 Cols) */}
        <div className="lg:col-span-7 space-y-6">
          {selectedSession ? (
            <>
              {/* Session Summary Card */}
              <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-6 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-4 border-b border-zinc-100 dark:border-zinc-800/80 pb-5">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-mono text-xl font-bold text-zinc-900 dark:text-white">
                        {selectedSession.ip_address}
                      </h3>
                      <span className="rounded-md bg-zinc-100 dark:bg-zinc-900 px-2.5 py-0.5 font-mono text-[10px] font-semibold text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-800">
                        ID: {selectedSession.id.slice(0, 8)}…
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-zinc-500">
                      {selectedSession.city}, {selectedSession.country}
                    </p>
                  </div>

                  {/* PDF Download Button */}
                  <button
                    onClick={() => handleDownloadPdf(selectedSession.id)}
                    className="flex items-center gap-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 px-3.5 py-2 text-xs font-semibold text-zinc-800 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition"
                  >
                    <FileText className="h-4 w-4" />
                    Forensic PDF
                  </button>
                </div>

                {/* Metadata Grid */}
                <div className="mt-5 grid grid-cols-2 gap-4 text-xs sm:grid-cols-4">
                  <div className="rounded-lg bg-zinc-100/70 dark:bg-zinc-900/80 p-3 border border-zinc-200 dark:border-zinc-800">
                    <p className="text-[10px] uppercase font-bold text-zinc-600 dark:text-zinc-400">Attempted User</p>
                    <p className="mt-1 font-mono font-bold text-zinc-950 dark:text-zinc-100 truncate">
                      {selectedSession.username_attempted}
                    </p>
                  </div>

                  <div className="rounded-lg bg-zinc-100/70 dark:bg-zinc-900/80 p-3 border border-zinc-200 dark:border-zinc-800">
                    <p className="text-[10px] uppercase font-bold text-zinc-600 dark:text-zinc-400">Password Used</p>
                    <p className="mt-1 font-mono font-bold text-zinc-950 dark:text-zinc-100 truncate">
                      {selectedSession.password_attempted || "••••••••"}
                    </p>
                  </div>

                  <div className="rounded-lg bg-zinc-100/70 dark:bg-zinc-900/80 p-3 border border-zinc-200 dark:border-zinc-800">
                    <p className="text-[10px] uppercase font-bold text-zinc-600 dark:text-zinc-400">Started At</p>
                    <p className="mt-1 font-mono font-bold text-zinc-950 dark:text-zinc-100">
                      {new Date(selectedSession.started_at).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>

                  <div className="rounded-lg bg-zinc-100/70 dark:bg-zinc-900/80 p-3 border border-zinc-200 dark:border-zinc-800">
                    <p className="text-[10px] uppercase font-bold text-zinc-600 dark:text-zinc-400">Session Status</p>
                    <p className={`mt-1 font-bold font-mono text-xs ${selectedSession.ended_at ? "text-zinc-600 dark:text-zinc-400" : "text-emerald-600 dark:text-emerald-400"}`}>
                      {selectedSession.ended_at ? "Terminated" : "Active"}
                    </p>
                  </div>
                </div>
              </div>

              {/* Event Timeline / Command Log */}
              <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-6 shadow-sm">
                <div className="flex items-center gap-2 border-b border-zinc-100 dark:border-zinc-800/80 pb-4">
                  <Terminal className="h-4 w-4 text-zinc-700 dark:text-zinc-300" />
                  <h4 className="font-semibold text-xs text-zinc-900 dark:text-white">
                    Forensic Command Stream & Deception Triggers
                  </h4>
                </div>

                <div className="mt-5 space-y-3 max-h-[380px] overflow-y-auto">
                  {eventsLoading ? (
                    <div className="py-12 text-center text-xs text-zinc-500">
                      Fetching attacker timeline...
                    </div>
                  ) : events.length === 0 ? (
                    <div className="py-12 text-center text-xs text-zinc-500">
                      <AlertTriangle className="mx-auto h-6 w-6 text-zinc-400 mb-2" />
                      No commands or deception events recorded for this session.
                    </div>
                  ) : (
                    events.map((ev, idx) => (
                      <div
                        key={ev.id || idx}
                        className="rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/90 p-3.5 space-y-2"
                      >
                        <div className="flex items-center justify-between text-xs">
                          <span className="rounded bg-zinc-100 dark:bg-zinc-800 px-2 py-0.5 font-mono text-[10px] font-semibold text-zinc-800 dark:text-zinc-200 uppercase border border-zinc-200 dark:border-zinc-700">
                            {ev.event_type}
                          </span>
                          <span className="text-[10px] text-zinc-400 font-mono">
                            {new Date(ev.timestamp).toLocaleTimeString()}
                          </span>
                        </div>

                        {ev.input_data && (
                          <div className="rounded bg-zinc-900 dark:bg-black px-3 py-1.5 font-mono text-xs text-emerald-400 border border-zinc-800">
                            $ {ev.input_data}
                          </div>
                        )}

                        {ev.output_data && (
                          <div className="rounded bg-zinc-900/90 dark:bg-black/90 px-3 py-1.5 font-mono text-[11px] text-amber-400 whitespace-pre-wrap border border-zinc-800">
                            {ev.output_data}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="rounded-xl border border-dashed border-zinc-200 dark:border-zinc-800 p-16 text-center text-zinc-500 bg-white dark:bg-zinc-950">
              <User className="mx-auto h-8 w-8 text-zinc-400 mb-3" />
              <p className="font-semibold text-xs text-zinc-700 dark:text-zinc-300">
                No Attacker Session Selected
              </p>
              <p className="mt-1 text-[11px] text-zinc-500">
                Select an IP session from the list on the left to inspect forensic logs.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
