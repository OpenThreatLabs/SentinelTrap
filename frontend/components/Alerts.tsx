"use client";

import { useEffect, useState } from "react";
import { Bell, AlertTriangle } from "lucide-react";

type Alert = {
  id: string;
  event_type: string;
  input_data?: string;
  output_data?: string;
  timestamp: string;
  session_id: string;
};

type Session = {
  id: string;
  ip_address: string;
};

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAlerts = async () => {
      try {
        setLoading(true);

        // Get all sessions
        const sessionsResponse = await fetch(
          "http://127.0.0.1:8000/api/sessions"
        );

        if (!sessionsResponse.ok) {
          throw new Error("Failed to load sessions");
        }

        const sessions: Session[] =
          await sessionsResponse.json();

        // Get events for every session
        const eventRequests = sessions.map(async (session) => {
          try {
            const response = await fetch(
              `http://127.0.0.1:8000/api/sessions/${session.id}/events`
            );

            if (!response.ok) {
              return [];
            }

            const events = await response.json();

            return events.map((event: any) => ({
              id: event.id,
              event_type: event.event_type,
              input_data: event.input_data,
              output_data: event.output_data,
              timestamp: event.timestamp,
              session_id: session.id,
            }));
          } catch {
            return [];
          }
        });

        const results = await Promise.all(eventRequests);

        const allEvents = results
          .flat()
          .sort(
            (a, b) =>
              new Date(b.timestamp).getTime() -
              new Date(a.timestamp).getTime()
          );

        setAlerts(allEvents);
      } catch (error) {
        console.error("Unable to load alerts:", error);
      } finally {
        setLoading(false);
      }
    };

    loadAlerts();

    // Refresh alerts every 5 seconds
    const interval = setInterval(loadAlerts, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0b1120] p-6">

      {/* Header */}
      <div className="flex items-center gap-3">

        <div className="rounded-lg bg-cyan-500/10 p-2">
          <Bell className="h-5 w-5 text-cyan-400" />
        </div>

        <div>
          <h2 className="font-semibold text-white">
            Security Alerts
          </h2>

          <p className="text-xs text-slate-500">
            Detected attacker activity
          </p>
        </div>

      </div>

      {/* Loading */}
      {loading && (
        <div className="mt-8 text-center text-sm text-slate-500">
          Loading security alerts...
        </div>
      )}

      {/* No Alerts */}
      {!loading && alerts.length === 0 && (
        <div className="mt-8 text-center text-sm text-slate-500">

          <AlertTriangle className="mx-auto h-8 w-8 text-slate-600" />

          <p className="mt-3">
            No security alerts available.
          </p>

          <p className="mt-1 text-xs text-slate-600">
            Alerts will appear when attacker events are detected.
          </p>

        </div>
      )}

      {/* Alerts */}
      {!loading && alerts.length > 0 && (
        <div className="mt-6 space-y-3">

          {alerts.map((alert) => (
            <div
              key={alert.id}
              className="rounded-lg border border-red-500/20 bg-red-500/5 p-4"
            >

              <div className="flex items-start justify-between gap-4">

                <div>

                  <p className="text-sm font-semibold text-red-400">
                    {alert.event_type}
                  </p>

                  {alert.input_data && (
                    <p className="mt-2 font-mono text-xs text-slate-300">
                      Command/Input: {alert.input_data}
                    </p>
                  )}

                  {alert.output_data && (
                    <p className="mt-1 text-xs text-slate-500">
                      Output: {alert.output_data}
                    </p>
                  )}

                  <p className="mt-2 text-xs text-slate-600">
                    {new Date(alert.timestamp).toLocaleString()}
                  </p>

                </div>

                <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-red-400" />

              </div>

            </div>
          ))}

        </div>
      )}

    </div>
  );
}