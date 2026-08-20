"use client";

import { useEffect, useRef, useState } from "react";
import { Radio, Pause, Play } from "lucide-react";
import {
  categorizeEvent,
  humanizeEventType,
  type EventCategory,
} from "../lib/honeypot-events";

// ---------------------------------------------------------------------------
// Types — mirror the payloads broadcast by ConnectionManager in backend/main.py
// ---------------------------------------------------------------------------

interface RawSessionCreatedMessage {
  event_type: "session_created";
  session: {
    id: string;
    ip_address: string;
    country: string;
    city: string;
    username_attempted: string;
    started_at: string;
  };
}

interface RawSessionEndedMessage {
  event_type: "session_ended";
  session_id: string;
  ended_at: string;
}

interface RawNewEventMessage {
  event_type: "new_event";
  session_id: string;
  event: {
    id: number;
    event_type: string;
    input_data: string | null;
    output_data: string | null;
    timestamp: string;
  };
}

type RawMessage =
  | RawSessionCreatedMessage
  | RawSessionEndedMessage
  | RawNewEventMessage;

interface FeedRow {
  key: string;
  session_id: string;
  timestamp: string;
  category: EventCategory | "session_open" | "session_close";
  label: string;
  detail: string;
}

type ConnectionState = "connecting" | "open" | "closed" | "error";

const WS_URL = process.env.NEXT_PUBLIC_SENTINELTRAP_WS_URL || "";

const MAX_BUFFERED_ROWS = 500;
const RECONNECT_BASE_DELAY_MS = 1000;
const RECONNECT_MAX_DELAY_MS = 15000;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatClock(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString(undefined, {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return "--:--:--";
  }
}

function toFeedRow(raw: RawMessage): FeedRow | null {
  if (raw.event_type === "session_created") {
    const s = raw.session;
    return {
      key: `session-open-${s.id}`,
      session_id: s.id,
      timestamp: s.started_at,
      category: "session_open",
      label: "new session",
      detail: `${s.ip_address} (${s.city}, ${s.country}) attempted login as "${s.username_attempted}"`,
    };
  }
  if (raw.event_type === "session_ended") {
    return {
      key: `session-close-${raw.session_id}-${raw.ended_at}`,
      session_id: raw.session_id,
      timestamp: raw.ended_at,
      category: "session_close",
      label: "session closed",
      detail: "attacker disconnected",
    };
  }
  if (raw.event_type === "new_event") {
    const ev = raw.event;
    const category = categorizeEvent(ev.event_type);
    return {
      key: `event-${ev.id}`,
      session_id: raw.session_id,
      timestamp: ev.timestamp,
      category,
      label: humanizeEventType(ev.event_type),
      detail: ev.input_data || ev.output_data || "",
    };
  }
  return null;
}

function rowAccentClass(category: FeedRow["category"]): string {
  switch (category) {
    case "command":
      return "text-emerald-400";
    case "deception":
      return "text-amber-400";
    case "auth":
      return "text-sky-400";
    case "session_open":
      return "text-cyan-400";
    case "session_close":
      return "text-slate-500";
    default:
      return "text-slate-400";
  }
}

function rowGlyph(category: FeedRow["category"]): string {
  switch (category) {
    case "command":
      return "$";
    case "deception":
      return "⚠";
    case "auth":
      return "»";
    case "session_open":
      return "+";
    case "session_close":
      return "×";
    default:
      return "·";
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface LiveFeedProps {
  /** Optional filter: only show rows from this session id */
  sessionId?: string;
  /** Called when the user clicks a session id in the feed */
  onSelectSession?: (sessionId: string) => void;
  className?: string;
}

export default function LiveFeed({
  sessionId,
  onSelectSession,
  className,
}: LiveFeedProps) {
  const [rows, setRows] = useState<FeedRow[]>([]);
  const [connState, setConnState] = useState<ConnectionState>("connecting");
  const [paused, setPaused] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [pendingCount, setPendingCount] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempt = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const pendingQueue = useRef<FeedRow[]>([]);
  const pausedRef = useRef(paused);

  useEffect(() => {
    pausedRef.current = paused;
  }, [paused]);

  useEffect(() => {
    let active = true;
    let ws: WebSocket | null = null;

    const doConnect = () => {
      if (!active) return;
      setConnState("connecting");

      ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!active) return;
        reconnectAttempt.current = 0;
        setConnState("open");
      };

      ws.onmessage = (msg) => {
        if (!active) return;
        let parsed: RawMessage | null = null;
        try {
          parsed = JSON.parse(msg.data);
        } catch {
          return;
        }
        const row = parsed && toFeedRow(parsed);
        if (!row) return;

        if (pausedRef.current) {
          pendingQueue.current.push(row);
          setPendingCount(pendingQueue.current.length);
          return;
        }
        setRows((prev) => {
          const next = [...prev, row];
          if (next.length > MAX_BUFFERED_ROWS) {
            next.splice(0, next.length - MAX_BUFFERED_ROWS);
          }
          return next;
        });
      };

      ws.onerror = () => {
        if (active) setConnState("error");
      };

      ws.onclose = () => {
        if (!active) return;
        setConnState("closed");
        wsRef.current = null;
        const delay = Math.min(
          RECONNECT_BASE_DELAY_MS * 2 ** reconnectAttempt.current,
          RECONNECT_MAX_DELAY_MS
        );
        reconnectAttempt.current += 1;
        reconnectTimer.current = setTimeout(doConnect, delay);
      };
    };

    doConnect();

    return () => {
      active = false;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (ws) ws.close();
    };
  }, []);

  function togglePause() {
    setPaused((p) => {
      const next = !p;
      if (!next && pendingQueue.current.length > 0) {
        setRows((prev) => {
          const merged = [...prev, ...pendingQueue.current];
          pendingQueue.current = [];
          if (merged.length > MAX_BUFFERED_ROWS) {
            merged.splice(0, merged.length - MAX_BUFFERED_ROWS);
          }
          return merged;
        });
        setPendingCount(0);
      }
      return next;
    });
  }

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [rows, autoScroll]);

  const visibleRows = sessionId
    ? rows.filter((r) => r.session_id === sessionId)
    : rows;

  const statusDotClass =
    connState === "open"
      ? "bg-emerald-400 shadow-[0_0_6px_2px_rgba(52,211,153,0.6)]"
      : connState === "connecting"
      ? "bg-amber-400 animate-pulse"
      : "bg-red-500";

  const statusLabel =
    connState === "open"
      ? "LIVE"
      : connState === "connecting"
      ? "CONNECTING"
      : connState === "error"
      ? "ERROR"
      : "RECONNECTING";

  return (
    <div
      className={`flex flex-col overflow-hidden rounded-xl border border-slate-800 bg-[#080b12] font-mono text-sm shadow-inner ${
        className ?? ""
      }`}
    >
      {/* Header bar */}
      <div className="flex items-center justify-between border-b border-slate-800 bg-[#0b1120] px-4 py-3">
        <div className="flex items-center gap-2">
          <Radio className="h-4 w-4 text-slate-500" />
          <span className={`h-2 w-2 rounded-full ${statusDotClass}`} />
          <span className="text-[11px] tracking-widest text-slate-400">
            {statusLabel}
          </span>
          <span className="ml-2 text-xs text-slate-500">
            Live Attacker Command Feed
          </span>
        </div>
        <div className="flex items-center gap-3 text-[11px]">
          <label className="flex items-center gap-1 text-slate-500">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="accent-emerald-500"
            />
            autoscroll
          </label>
          <button
            onClick={togglePause}
            className={`flex items-center gap-1 rounded border px-2 py-1 transition-colors ${
              paused
                ? "border-amber-500/40 text-amber-400 hover:bg-amber-500/10"
                : "border-slate-700 text-slate-400 hover:bg-slate-800"
            }`}
          >
            {paused ? (
              <>
                <Play className="h-3 w-3" /> resume{pendingCount ? ` (${pendingCount})` : ""}
              </>
            ) : (
              <>
                <Pause className="h-3 w-3" /> pause
              </>
            )}
          </button>
        </div>
      </div>

      {/* Feed body */}
      <div
        ref={scrollRef}
        onScroll={(e) => {
          const el = e.currentTarget;
          const nearBottom =
            el.scrollHeight - el.scrollTop - el.clientHeight < 40;
          if (!nearBottom && autoScroll) setAutoScroll(false);
        }}
        className="h-80 overflow-y-auto px-4 py-2 leading-relaxed"
      >
        {visibleRows.length === 0 && (
          <div className="py-10 text-center text-xs text-slate-600">
            {connState === "open"
              ? "listening for attacker activity…"
              : "connecting to threat feed…"}
          </div>
        )}

        {visibleRows.map((row) => (
          <div
            key={row.key}
            className="group flex flex-wrap items-start gap-2 py-0.5 hover:bg-slate-900/50"
          >
            <span className="shrink-0 select-none text-[11px] text-slate-600">
              {formatClock(row.timestamp)}
            </span>
            <button
              onClick={() => onSelectSession?.(row.session_id)}
              className="shrink-0 select-none text-[11px] text-slate-500 underline-offset-2 hover:text-cyan-400 hover:underline"
              title="Open this session in the replayer"
            >
              {row.session_id.slice(0, 8)}
            </button>
            <span className={`shrink-0 select-none font-bold ${rowAccentClass(row.category)}`}>
              {rowGlyph(row.category)}
            </span>
            <span className="shrink-0 select-none text-[10px] uppercase tracking-wide text-slate-600">
              {row.label}
            </span>
            <span
              className={`whitespace-pre-wrap break-all ${
                row.category === "command"
                  ? "text-emerald-300"
                  : row.category === "deception"
                  ? "text-amber-300"
                  : row.category === "auth"
                  ? "text-sky-300"
                  : row.category === "session_open"
                  ? "text-cyan-300"
                  : "text-slate-400"
              }`}
            >
              {row.category === "deception" && (
                <span className="mr-1 rounded bg-amber-500/10 px-1 text-[10px] font-semibold uppercase tracking-wide text-amber-400">
                  decoy
                </span>
              )}
              {row.detail}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
