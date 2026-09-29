"use client";

import { useEffect, useState } from "react";
import {
  Server,
  RefreshCw,
  Clock,
  Activity,
  ArrowRight,
  X,
  Radio,
  Terminal,
} from "lucide-react";

type ServerWakeModalProps = {
  isOffline: boolean;
  onRetry?: () => void;
};

export default function ServerWakeModal({
  isOffline,
  onRetry,
}: ServerWakeModalProps) {
  const [dismissed, setDismissed] = useState(false);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isOffline) {
      setDismissed(false);
      setElapsed(0);
      timer = setInterval(() => {
        setElapsed((prev) => prev + 1);
      }, 1000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isOffline]);

  if (!isOffline || dismissed) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-lg transition-all animate-in fade-in duration-300">
      {/* Outer Glow Card Container matching SentinelTrap Cyan/Indigo Palette */}
      <div className="relative w-full max-w-xl overflow-hidden rounded-3xl border border-cyan-500/30 bg-gradient-to-b from-zinc-950 via-zinc-950 to-black p-6 sm:p-8 shadow-[0_0_60px_-15px_rgba(6,182,212,0.25)] text-zinc-100">
        
        {/* Ambient Top Light Beam */}
        <div className="pointer-events-none absolute -top-24 left-1/2 -translate-x-1/2 h-44 w-80 rounded-full bg-gradient-to-b from-cyan-400/20 via-indigo-500/15 to-transparent blur-3xl" />
        <div className="pointer-events-none absolute -bottom-20 -right-20 h-48 w-48 rounded-full bg-fuchsia-500/10 blur-3xl" />

        {/* Top Header Row */}
        <div className="relative flex items-center justify-between pb-5 border-b border-zinc-800/80">
          <div>
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400">
              SentinelTrap Cloud Node
            </span>
            <p className="text-[10px] text-zinc-400 font-mono">Render Free Compute Tier</p>
          </div>

          <button
            onClick={() => setDismissed(true)}
            className="rounded-xl p-1.5 text-zinc-400 hover:text-white hover:bg-zinc-800/80 transition active:scale-95 border border-transparent hover:border-zinc-700/60"
            aria-label="Close modal"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Center Visual & Title */}
        <div className="relative pt-6 pb-2 text-center flex flex-col items-center">
          {/* Futuristic Concentric Radar Ring in Cyan */}
          <div className="relative mb-6 flex items-center justify-center">
            <div className="absolute h-28 w-28 rounded-full border border-cyan-500/20 animate-ping" />
            <div className="absolute h-24 w-24 rounded-full border border-cyan-500/30 animate-pulse" />
            <div className="relative flex h-18 w-18 items-center justify-center rounded-2xl border border-cyan-500/50 bg-gradient-to-b from-cyan-500/20 to-indigo-500/10 p-4 shadow-xl shadow-cyan-500/20 backdrop-blur-sm">
              <Server className="h-9 w-9 text-cyan-400 drop-shadow-[0_0_12px_rgba(6,182,212,0.6)]" />
              <span className="absolute -top-1 -right-1 flex h-3.5 w-3.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-cyan-400 border-2 border-zinc-950"></span>
              </span>
            </div>
          </div>

          <h3 className="text-2xl sm:text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-cyan-100 to-indigo-200 bg-clip-text text-transparent mb-2">
            Backend is Waking Up
          </h3>

          <p className="text-xs sm:text-sm text-zinc-400 leading-relaxed max-w-md mx-auto">
            The FastAPI backend engine was sleeping to save cloud resources. The virtual container is spinning up now and telemetry will reconnect automatically.
          </p>

          {/* Micro Status Indicators */}
          <div className="mt-5 grid grid-cols-3 gap-2 w-full max-w-md text-left">
            <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-2.5 backdrop-blur-sm">
              <div className="flex items-center gap-1.5 text-[10px] font-mono text-zinc-400 uppercase">
                <Radio className="h-3 w-3 text-cyan-400 animate-pulse" />
                Container
              </div>
              <p className="text-xs font-semibold text-zinc-200 mt-1">Booting...</p>
            </div>

            <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-2.5 backdrop-blur-sm">
              <div className="flex items-center gap-1.5 text-[10px] font-mono text-zinc-400 uppercase">
                <Terminal className="h-3 w-3 text-indigo-400" />
                Decoys
              </div>
              <p className="text-xs font-semibold text-zinc-200 mt-1">9 Listeners</p>
            </div>

            <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-2.5 backdrop-blur-sm">
              <div className="flex items-center gap-1.5 text-[10px] font-mono text-zinc-400 uppercase">
                <Clock className="h-3 w-3 text-cyan-400 animate-spin" />
                Elapsed
              </div>
              <p className="text-xs font-mono font-bold text-cyan-400 mt-1">{elapsed}s / ~40s</p>
            </div>
          </div>

          {/* Cyan / Indigo Progress Laser Track */}
          <div className="w-full max-w-md mt-6">
            <div className="flex justify-between items-center text-[11px] font-mono text-zinc-400 mb-2">
              <span className="flex items-center gap-1.5 text-cyan-400 font-medium">
                <Activity className="h-3 w-3 animate-pulse" />
                Initializing WebSocket stream...
              </span>
              <span className="text-zinc-500 text-[10px]">FastAPI + Uvicorn</span>
            </div>

            <div className="relative h-2 w-full overflow-hidden rounded-full bg-zinc-900/90 border border-zinc-800 shadow-inner">
              <div className="absolute inset-y-0 h-full w-1/3 rounded-full bg-gradient-to-r from-cyan-500 via-indigo-400 to-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.7)] animate-status-indeterminate" />
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="mt-8 pt-5 border-t border-zinc-800/80 flex flex-col-reverse sm:flex-row items-center gap-3">
          {onRetry && (
            <button
              onClick={onRetry}
              className="w-full sm:w-2/5 flex items-center justify-center gap-2 rounded-xl border border-zinc-700/80 bg-zinc-900/80 hover:bg-zinc-800 px-4 py-3 text-xs font-semibold text-zinc-300 transition hover:text-white active:scale-95 shadow-sm"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Check Status
            </button>
          )}

          <button
            onClick={() => setDismissed(true)}
            className="w-full sm:w-3/5 group relative flex items-center justify-center gap-2 overflow-hidden rounded-xl bg-gradient-to-r from-cyan-400 via-indigo-500 to-fuchsia-500 px-5 py-3 text-xs font-bold uppercase tracking-wider text-white shadow-lg shadow-cyan-500/25 transition-all hover:scale-[1.02] hover:shadow-cyan-500/40 active:scale-98"
          >
            <span>Continue to Dashboard</span>
            <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
          </button>
        </div>
      </div>
    </div>
  );
}
