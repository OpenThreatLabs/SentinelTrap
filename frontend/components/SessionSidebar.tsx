"use client";

import { useEffect, useState } from "react";
import { MapPin, User, Clock, Globe } from "lucide-react";

type Session = {
  id: string;
  ip_address: string;
  country: string;
  city: string;
  username_attempted: string;
  password_attempted?: string;
  started_at: string;
};

export default function SessionSidebar() {
  const [sessions, setSessions] = useState<Session[]>([]);

  useEffect(() => {
    fetch("http://localhost:8000/api/sessions")
      .then((response) => response.json())
      .then((data) => {
        setSessions(data);
      })
      .catch(() => {
        console.log("Backend is not connected yet.");
      });
  }, []);

  return (
    <aside className="rounded-xl border border-slate-800 bg-[#0b1120]">
      <div className="border-b border-slate-800 p-5">
        <h2 className="font-semibold text-white">
          Attacker Sessions
        </h2>

        <p className="mt-1 text-xs text-slate-500">
          Captured attacker activity
        </p>
      </div>

      <div className="max-h-[600px] overflow-y-auto">
        {sessions.length === 0 ? (
          <div className="p-6 text-center text-sm text-slate-500">
            No attacker sessions available.
          </div>
        ) : (
          sessions.map((session) => (
            <button
              key={session.id}
              className="w-full border-b border-slate-800 p-5 text-left transition hover:bg-slate-900"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-mono text-sm font-semibold text-cyan-400">
                    {session.ip_address}
                  </p>

                  <div className="mt-2 flex items-center gap-2 text-xs text-slate-400">
                    <Globe className="h-3.5 w-3.5" />
                    {session.country}
                  </div>

                  <div className="mt-1 flex items-center gap-2 text-xs text-slate-400">
                    <MapPin className="h-3.5 w-3.5" />
                    {session.city}
                  </div>

                  <div className="mt-2 flex items-center gap-2 text-xs text-slate-400">
                    <User className="h-3.5 w-3.5" />
                    Username:{" "}
                    <span className="text-slate-200">
                      {session.username_attempted}
                    </span>
                  </div>

                  {session.password_attempted && (
                    <div className="mt-1 text-xs text-slate-500">
                      Password attempted:{" "}
                      {session.password_attempted}
                    </div>
                  )}

                  <div className="mt-2 flex items-center gap-2 text-xs text-slate-500">
                    <Clock className="h-3.5 w-3.5" />
                    {new Date(session.started_at).toLocaleString()}
                  </div>
                </div>

                <span className="mt-1 h-2.5 w-2.5 rounded-full bg-red-400" />
              </div>
            </button>
          ))
        )}
      </div>
    </aside>
  );
}