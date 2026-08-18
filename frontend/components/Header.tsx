"use client";

import { useEffect, useState } from "react";
import { ShieldCheck, Wifi, WifiOff } from "lucide-react";

export default function Header() {
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: NodeJS.Timeout;

    const connect = () => {
      ws = new WebSocket("ws://127.0.0.1:8000/ws");

      ws.onopen = () => {
        console.log("WebSocket connected");
        setConnected(true);
      };

      ws.onclose = () => {
        console.log("WebSocket disconnected");
        setConnected(false);

        // Try to reconnect after 2 seconds
        reconnectTimer = setTimeout(connect, 2000);
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setConnected(false);
      };
    };

    connect();

    return () => {
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }

      if (ws) {
        ws.close();
      }
    };
  }, []);

  return (
    <header className="flex h-20 items-center justify-between border-b border-slate-800 bg-[#080d18] px-8">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/10">
          <ShieldCheck className="h-6 w-6 text-cyan-400" />
        </div>

        <div>
          <p className="text-sm text-slate-500">
            Security Operations
          </p>

          <h1 className="text-xl font-bold text-white">
            SentinelTrap
          </h1>
        </div>
      </div>

      <div
        className={`flex items-center gap-2 rounded-full border px-4 py-2 text-sm ${
          connected
            ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400"
            : "border-red-500/20 bg-red-500/10 text-red-400"
        }`}
      >
        {connected ? (
          <Wifi className="h-4 w-4" />
        ) : (
          <WifiOff className="h-4 w-4" />
        )}

        <span>
          {connected ? "Live Connected" : "Disconnected"}
        </span>
      </div>
    </header>
  );
}