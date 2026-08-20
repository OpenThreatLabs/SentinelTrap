"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { TerminalSquare } from "lucide-react";
import {
  categorizeEvent,
  createShellReplayState,
  humanizeEventType,
  simulateDeceptionResponse,
  simulateShellOutput,
  type HoneypotEvent,
} from "../lib/honeypot-events";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface TerminalReplayProps {
  sessionId: string | null;
  apiBaseUrl?: string;
  /** Shell prompt shown before each command line */
  prompt?: string;
  className?: string;
}

/** A single renderable line, derived from a raw HoneypotEvent. */
interface ReplayLine {
  key: string;
  timestamp: string;
  kind: "command" | "output" | "deception" | "system";
  label?: string;
  text: string;
}

type FetchState = "idle" | "loading" | "error" | "ready";

const DEFAULT_PROMPT = "root@prod-web-srv-01:~#";
const SPEED_OPTIONS = [1, 2, 4, 8] as const;
const MAX_INTER_EVENT_DELAY_MS = 2000; // cap silence between events so idle gaps don't stall playback

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

/**
 * Turns raw backend events into renderable terminal lines: a command line
 * for the input, plus a synthesized output line where the backend didn't
 * persist one (see lib/honeypot-events.ts for why that happens).
 */
function buildReplayLines(events: HoneypotEvent[]): ReplayLine[] {
  const lines: ReplayLine[] = [];
  const shellState = createShellReplayState();

  for (const ev of events) {
    const category = categorizeEvent(ev.event_type);

    if (category === "command") {
      lines.push({
        key: `${ev.id}-cmd`,
        timestamp: ev.timestamp,
        kind: "command",
        text: ev.input_data ?? "",
      });

      // If this input would have tripped the deception engine, the real
      // shell command table never ran for it (see honeypot/shell.py) — skip
      // simulating plain output here and let the paired deception_triggered
      // event (below) render what actually happened.
      const wouldDeceive = simulateDeceptionResponse(ev.input_data ?? "");

      if (ev.output_data) {
        lines.push({
          key: `${ev.id}-out`,
          timestamp: ev.timestamp,
          kind: "output",
          text: ev.output_data,
        });
      } else if (!wouldDeceive) {
        const simulated = simulateShellOutput(ev.input_data ?? "", shellState);
        if (simulated) {
          lines.push({
            key: `${ev.id}-out-sim`,
            timestamp: ev.timestamp,
            kind: "output",
            text: simulated,
          });
        }
      }
      continue;
    }

    if (category === "deception") {
      // Some honeypot modules (mysql, redis, etc.) log deception_triggered
      // as the only event for the exchange, with no prior command line.
      const alreadyShownAsCommand = lines.some(
        (l) => l.kind === "command" && l.text === ev.input_data
      );
      if (ev.input_data && !alreadyShownAsCommand) {
        lines.push({
          key: `${ev.id}-cmd`,
          timestamp: ev.timestamp,
          kind: "command",
          text: ev.input_data,
        });
      }

      // output_data usually holds a short summary ("Trap activated: <type>",
      // "Decoy Response: ERROR 1045..."); reconstruct the fuller banner text
      // for the well-known shell.py trap types when only that summary exists.
      const looksLikeGenericSummary =
        !ev.output_data || /^trap activated/i.test(ev.output_data);
      const reconstructed = looksLikeGenericSummary
        ? simulateDeceptionResponse(ev.input_data ?? "")
        : null;

      lines.push({
        key: `${ev.id}-decoy`,
        timestamp: ev.timestamp,
        kind: "deception",
        // Avoid showing the same string twice: when we reconstructed a fuller
        // banner, the short summary makes a useful tag; otherwise the tag
        // just names the event and the summary itself is the body text.
        label: reconstructed
          ? ev.output_data || humanizeEventType(ev.event_type)
          : humanizeEventType(ev.event_type),
        text: reconstructed?.output ?? ev.output_data ?? "trap activated",
      });
      continue;
    }

    if (category === "auth") {
      lines.push({
        key: `${ev.id}-auth`,
        timestamp: ev.timestamp,
        kind: "system",
        label: humanizeEventType(ev.event_type),
        text: ev.input_data ?? ev.output_data ?? "",
      });
      continue;
    }

    // system / everything else
    lines.push({
      key: `${ev.id}-sys`,
      timestamp: ev.timestamp,
      kind: "system",
      label: humanizeEventType(ev.event_type),
      text: ev.input_data ?? ev.output_data ?? "",
    });
  }

  return lines;
}

function computeDelays(lines: ReplayLine[]): number[] {
  const delays: number[] = [];
  for (let i = 0; i < lines.length; i++) {
    if (i === 0) {
      delays.push(0);
      continue;
    }
    const prev = new Date(lines[i - 1].timestamp).getTime();
    const cur = new Date(lines[i].timestamp).getTime();
    const raw = Number.isFinite(prev) && Number.isFinite(cur) ? cur - prev : 250;
    // Synthesized output lines share their command's timestamp — keep those instant.
    delays.push(Math.max(0, Math.min(raw, MAX_INTER_EVENT_DELAY_MS)));
  }
  return delays;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function TerminalReplay({
  sessionId,
  apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "",
  prompt = DEFAULT_PROMPT,
  className,
}: TerminalReplayProps) {
  const [state, setState] = useState<FetchState>("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [lines, setLines] = useState<ReplayLine[]>([]);

  const [cursor, setCursor] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState<(typeof SPEED_OPTIONS)[number]>(2);

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const bodyRef = useRef<HTMLDivElement | null>(null);

  const delays = useMemo(() => computeDelays(lines), [lines]);

  // Fetch session history whenever a new session is selected.
  useEffect(() => {
    if (!sessionId) {
      const timer = setTimeout(() => {
        setLines([]);
        setCursor(0);
        setState("idle");
      }, 0);
      return () => clearTimeout(timer);
    }

    let active = true;
    const controller = new AbortController();

    const fetchSession = async () => {
      setState("loading");
      setErrorMsg(null);
      setCursor(0);
      setPlaying(false);

      try {
        const res = await fetch(`${apiBaseUrl}/api/sessions/${sessionId}/events`, {
          signal: controller.signal,
        });
        if (!res.ok) {
          throw new Error(`Server returned ${res.status} ${res.statusText}`);
        }
        const data: HoneypotEvent[] = await res.json();
        if (active) {
          const events = Array.isArray(data) ? data : [];
          setLines(buildReplayLines(events));
          setState("ready");
        }
      } catch (err: unknown) {
        if (!active || controller.signal.aborted) return;
        setErrorMsg(err instanceof Error ? err.message : "Failed to load session");
        setState("error");
      }
    };

    fetchSession();

    return () => {
      active = false;
      controller.abort();
    };
  }, [sessionId, apiBaseUrl]);

  // Playback loop: reveal one line at a time, paced by inter-event delay / speed.
  useEffect(() => {
    if (!playing) return;
    if (cursor >= lines.length) {
      const stopTimer = setTimeout(() => setPlaying(false), 0);
      return () => clearTimeout(stopTimer);
    }
    const delay = (delays[cursor] ?? 250) / speed;
    timerRef.current = setTimeout(() => setCursor((c) => c + 1), delay);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [playing, cursor, lines.length, delays, speed]);

  useEffect(() => {
    if (bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [cursor]);

  const visible = lines.slice(0, cursor);
  const atEnd = cursor >= lines.length && lines.length > 0;

  function handlePlayPause() {
    if (atEnd) {
      setCursor(0);
      setPlaying(true);
      return;
    }
    setPlaying((p) => !p);
  }

  function handleStep() {
    setPlaying(false);
    setCursor((c) => Math.min(c + 1, lines.length));
  }

  function handleScrub(value: number) {
    setPlaying(false);
    setCursor(value);
  }

  return (
    <div
      className={`flex flex-col overflow-hidden rounded-xl border border-slate-800 bg-[#080b12] font-mono text-sm shadow-inner ${
        className ?? ""
      }`}
    >
      {/* Title bar */}
      <div className="flex items-center gap-2 border-b border-slate-800 bg-[#0b1120] px-4 py-3">
        <TerminalSquare className="h-4 w-4 text-slate-500" />
        <span className="h-2.5 w-2.5 rounded-full bg-red-500/70" />
        <span className="h-2.5 w-2.5 rounded-full bg-amber-500/70" />
        <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/70" />
        <span className="ml-2 truncate text-[11px] text-slate-500">
          {sessionId ? `session ${sessionId} — replay` : "no session selected"}
        </span>
      </div>

      {/* Body */}
      <div ref={bodyRef} className="h-96 overflow-y-auto px-4 py-3 leading-relaxed">
        {state === "idle" && (
          <div className="py-10 text-center text-xs text-slate-600">
            select a session from the sidebar to replay it
          </div>
        )}

        {state === "loading" && (
          <div className="py-10 text-center text-xs text-slate-500">
            loading session history…
          </div>
        )}

        {state === "error" && (
          <div className="py-10 text-center text-xs text-red-400">
            failed to load session: {errorMsg}
          </div>
        )}

        {state === "ready" && lines.length === 0 && (
          <div className="py-10 text-center text-xs text-slate-600">
            this session has no recorded events
          </div>
        )}

        {state === "ready" &&
          visible.map((line) => {
            if (line.kind === "command") {
              return (
                <div key={line.key} className="flex flex-wrap items-start gap-x-2 py-0.5">
                  <span className="select-none text-[11px] text-slate-600">
                    {formatClock(line.timestamp)}
                  </span>
                  <span className="select-none font-semibold text-emerald-400">
                    {prompt}
                  </span>
                  <span className="whitespace-pre-wrap break-all text-emerald-300">
                    {line.text}
                  </span>
                </div>
              );
            }
            if (line.kind === "deception") {
              return (
                <div key={line.key} className="flex items-start gap-2 py-0.5 pl-4">
                  <span className="mt-0.5 shrink-0 rounded bg-amber-500/10 px-1 text-[10px] font-semibold uppercase tracking-wide text-amber-400">
                    {line.label ?? "decoy"}
                  </span>
                  <span className="whitespace-pre-wrap break-all text-amber-300">
                    {line.text}
                  </span>
                </div>
              );
            }
            if (line.kind === "system") {
              return (
                <div key={line.key} className="flex items-start gap-2 py-0.5 pl-4 text-slate-500">
                  {line.label && (
                    <span className="shrink-0 text-[10px] uppercase tracking-wide text-slate-600">
                      [{line.label}]
                    </span>
                  )}
                  <span className="whitespace-pre-wrap break-all">{line.text}</span>
                </div>
              );
            }
            return (
              <div key={line.key} className="whitespace-pre-wrap break-all py-0.5 pl-4 text-slate-300">
                {line.text}
              </div>
            );
          })}

        {playing && !atEnd && (
          <span className="ml-4 inline-block h-3.5 w-2 animate-pulse bg-emerald-400/80 align-middle" />
        )}
      </div>

      {/* Transport controls */}
      {state === "ready" && lines.length > 0 && (
        <div className="flex items-center gap-3 border-t border-slate-800 bg-[#0b1120] px-4 py-2 text-[11px] text-slate-400">
          <button
            onClick={handlePlayPause}
            className="rounded border border-slate-700 px-2 py-1 text-slate-300 hover:bg-slate-800"
          >
            {playing ? "pause" : atEnd ? "replay" : "play"}
          </button>
          <button
            onClick={handleStep}
            disabled={atEnd}
            className="rounded border border-slate-700 px-2 py-1 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
          >
            step
          </button>

          <input
            type="range"
            min={0}
            max={lines.length}
            value={cursor}
            onChange={(e) => handleScrub(Number(e.target.value))}
            className="mx-1 h-1 flex-1 cursor-pointer accent-emerald-500"
          />

          <span className="w-14 shrink-0 text-right tabular-nums">
            {cursor}/{lines.length}
          </span>

          <div className="flex items-center gap-1 border-l border-slate-800 pl-3">
            {SPEED_OPTIONS.map((s) => (
              <button
                key={s}
                onClick={() => setSpeed(s)}
                className={`rounded px-1.5 py-0.5 ${
                  speed === s
                    ? "bg-emerald-500/20 text-emerald-400"
                    : "text-slate-500 hover:text-slate-300"
                }`}
              >
                {s}×
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
