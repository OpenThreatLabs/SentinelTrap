"use client";

import { useEffect, useState } from "react";
import { Server, RefreshCw, Activity, Clock } from "lucide-react";

type ServerStatusBannerProps = {
  isOffline: boolean;
  onRetry?: () => void;
};

export default function ServerStatusBanner({
  isOffline,
  onRetry,
}: ServerStatusBannerProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isOffline) {
      setElapsed(0);
      timer = setInterval(() => {
        setElapsed((prev) => prev + 1);
      }, 1000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isOffline]);

  if (!isOffline) return null;

  return (
    <div className="relative mb-8 overflow-hidden rounded-2xl border border-cyan-500/30 bg-gradient-to-b from-cyan-500/[0.08] via-zinc-950/90 to-zinc-950 p-6 shadow-2xl shadow-cyan-500/10 backdrop-blur-xl transition-all">
      {/* Background radial glow */}
      <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full border border-cyan-500/10 bg-cyan-500/5 blur-2xl" />
      <div className="pointer-events-none absolute left-1/3 top-0 h-40 w-40 rounded-full bg-indigo-500/5 blur-3xl" />

      <div className="relative flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        {/* Left Side */}
        <div className="flex items-start sm:items-center gap-4">
          <div className="relative flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border border-cyan-500/30 bg-cyan-500/10 text-cyan-400 shadow-inner shadow-cyan-500/20">
            <Server className="h-7 w-7 text-cyan-400" />
            <span className="absolute -top-1 -right-1 flex h-4 w-4">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-4 w-4 bg-cyan-500 border-2 border-black"></span>
            </span>
          </div>

          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-2.5 py-0.5 text-xs font-semibold text-cyan-400">
                <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
                Backend In Cold Sleep
              </span>
              <span className="rounded-md border border-zinc-700/60 bg-zinc-800/80 px-2 py-0.5 text-[11px] font-mono text-zinc-300">
                Render Free Cloud Tier
              </span>
            </div>

            <h3 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
              Spinning Up Python Telemetry Engine
            </h3>

            <p className="text-xs text-zinc-400 max-w-2xl leading-relaxed">
              To conserve free compute resources, Render automatically idles the FastAPI backend after 15 minutes of inactivity. The cluster is rebooting right now and live data feeds will resume automatically.
            </p>
          </div>
        </div>

        {/* Right Side */}
        <div className="flex flex-wrap items-center gap-3 shrink-0">
          <div className="flex items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900/80 px-3.5 py-2 text-xs font-mono text-zinc-300 shadow-sm">
            <Clock className="h-4 w-4 text-cyan-400 animate-spin" />
            <span>Waking time: <strong className="text-cyan-400">{elapsed}s</strong> / ~40s</span>
          </div>

          {onRetry && (
            <button
              onClick={onRetry}
              className="inline-flex items-center gap-2 rounded-xl border border-cyan-500/40 bg-cyan-500/20 px-4 py-2 text-xs font-semibold text-cyan-300 shadow-sm transition hover:bg-cyan-500/30 active:scale-95"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Check Now
            </button>
          )}
        </div>
      </div>

      {/* Progress Laser */}
      <div className="mt-6">
        <div className="flex justify-between text-[11px] font-mono text-zinc-400 mb-2">
          <span className="flex items-center gap-1.5 text-cyan-400/90 font-medium">
            <Activity className="h-3.5 w-3.5 animate-pulse" />
            Initializing ASGI application & honeypot daemons...
          </span>
          <span className="text-zinc-500 font-mono">https://sentineltrap-nz03.onrender.com</span>
        </div>

        <div className="relative h-2 w-full overflow-hidden rounded-full bg-zinc-900 border border-zinc-800">
          <div className="absolute inset-y-0 h-full w-2/5 rounded-full bg-gradient-to-r from-cyan-500 via-indigo-400 to-cyan-500 shadow-lg shadow-cyan-500/50 animate-status-indeterminate" />
        </div>
      </div>
    </div>
  );
}
