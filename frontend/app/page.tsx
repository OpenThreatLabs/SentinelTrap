"use client";

import { useState } from "react";
import {
  LayoutDashboard,
  Users,
  Bell,
  BarChart3,
  Shield,
} from "lucide-react";

import Header from "../components/Header";
import MetricCards from "../components/MetricCards";
import SessionSidebar from "../components/SessionSidebar";
import Alerts from "../components/Alerts";
import Analytics from "../components/Analytics";

export default function Home() {
  const [activePage, setActivePage] = useState("Dashboard");

  const navigation = [
    { name: "Dashboard", icon: LayoutDashboard },
    { name: "Sessions", icon: Users },
    { name: "Alerts", icon: Bell },
    { name: "Analytics", icon: BarChart3 },
    { name: "Backend Features", icon: Shield },
  ];

  return (
    <main className="min-h-screen bg-[#070b14] text-white">

      {/* Sidebar */}
      <aside className="fixed left-0 top-0 z-20 flex h-screen w-64 flex-col border-r border-slate-800 bg-[#0b1120]">

        {/* Logo */}
        <div className="border-b border-slate-800 p-6">
          <div className="flex items-center gap-3">

            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-500/10">
              <Shield className="h-6 w-6 text-cyan-400" />
            </div>

            <div>
              <h1 className="text-xl font-bold tracking-wide text-cyan-400">
                SentinelTrap
              </h1>

              <p className="text-xs text-slate-500">
                Cyber Defense Center
              </p>
            </div>

          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-2 p-4">

          {navigation.map((item) => {
            const Icon = item.icon;

            return (
              <button
                key={item.name}
                onClick={() => setActivePage(item.name)}
                className={`flex w-full items-center gap-3 rounded-lg px-4 py-3 text-left text-sm transition ${
                  activePage === item.name
                    ? "bg-cyan-500/10 text-cyan-400"
                    : "text-slate-400 hover:bg-slate-800 hover:text-white"
                }`}
              >
                <Icon className="h-5 w-5" />
                {item.name}
              </button>
            );
          })}

        </nav>

        {/* System Status */}
        <div className="border-t border-slate-800 p-4">

          <div className="rounded-lg bg-slate-900 p-4">

            <p className="text-xs text-slate-500">
              SYSTEM STATUS
            </p>

            <div className="mt-2 flex items-center gap-2">

              <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />

              <span className="text-sm text-emerald-400">
                All systems operational
              </span>

            </div>

          </div>

        </div>

      </aside>

      {/* Main Content */}
      <section className="ml-64 min-h-screen">

        <Header />

        <div className="p-8">

          {/* Heading */}
          <div className="mb-8">

            <p className="text-sm text-slate-500">
              Security Operations
            </p>

            <h2 className="mt-1 text-2xl font-bold">
              {activePage}
            </h2>

          </div>

          {/* Dashboard */}
          {activePage === "Dashboard" && (
            <>
              <MetricCards />

              <div className="mt-8 grid gap-6 xl:grid-cols-3">

                <div className="xl:col-span-1">
                  <SessionSidebar />
                </div>

                <div className="xl:col-span-2">

                  <div className="rounded-xl border border-slate-800 bg-[#0b1120] p-8">

                    <h2 className="text-lg font-semibold">
                      Security Monitoring
                    </h2>

                    <p className="mt-2 text-sm text-slate-500">
                      SentinelTrap security monitoring workspace.
                    </p>

                    <div className="mt-8 rounded-lg border border-dashed border-slate-700 p-10 text-center">

                      <Shield className="mx-auto h-10 w-10 text-cyan-400" />

                      <p className="mt-4 text-sm text-slate-400">
                        Dashboard workspace ready.
                      </p>

                      <p className="mt-2 text-xs text-slate-600">
                        Real-time security monitoring data will appear here.
                      </p>

                    </div>

                  </div>

                </div>

              </div>
            </>
          )}

          {/* Sessions */}
          {activePage === "Sessions" && (
            <div className="max-w-5xl">
              <SessionSidebar />
            </div>
          )}

          {/* Alerts */}
          {activePage === "Alerts" && (
            <div className="max-w-5xl">
              <Alerts />
            </div>
          )}

          {/* Analytics */}
          {activePage === "Analytics" && (
            <div className="max-w-5xl">
              <Analytics />
            </div>
          )}

          {/* Backend Features */}
          {activePage === "Backend Features" && (
            <div className="max-w-5xl">

              <div className="rounded-xl border border-slate-800 bg-[#0b1120] p-8">

                <h2 className="text-xl font-semibold text-white">
                  Backend Features
                </h2>

                <p className="mt-2 text-sm text-slate-500">
                  SentinelTrap backend security services and monitoring features.
                </p>

                <div className="mt-8 grid gap-5 md:grid-cols-2">

                  {/* Geolocate */}
                  <div className="rounded-xl border border-slate-800 bg-[#080d18] p-6">
                    <h3 className="text-lg font-semibold text-cyan-400">
                      🌍 Geolocate
                    </h3>

                    <p className="mt-3 text-sm text-slate-400">
                      Identifies an attacker&apos;s IP location and provides
                      threat-intelligence information.
                    </p>
                  </div>

                  {/* Decoy */}
                  <div className="rounded-xl border border-slate-800 bg-[#080d18] p-6">
                    <h3 className="text-lg font-semibold text-cyan-400">
                      🎭 Decoy Management
                    </h3>

                    <p className="mt-3 text-sm text-slate-400">
                      Manages decoy and honeypot services used to attract
                      and monitor attackers.
                    </p>
                  </div>

                  {/* AutoShun */}
                  <div className="rounded-xl border border-slate-800 bg-[#080d18] p-6">
                    <h3 className="text-lg font-semibold text-cyan-400">
                      🛡️ AutoShun
                    </h3>

                    <p className="mt-3 text-sm text-slate-400">
                      Generates firewall rules for high-risk IP addresses
                      to block or redirect attackers.
                    </p>
                  </div>

                  {/* Middleware */}
                  <div className="rounded-xl border border-slate-800 bg-[#080d18] p-6">
                    <h3 className="text-lg font-semibold text-cyan-400">
                      ⚙️ Middleware
                    </h3>

                    <p className="mt-3 text-sm text-slate-400">
                      Provides security controls such as request auditing
                      and API rate limiting.
                    </p>
                  </div>

                  {/* FTP */}
                  <div className="rounded-xl border border-slate-800 bg-[#080d18] p-6">
                    <h3 className="text-lg font-semibold text-cyan-400">
                      📁 FTP Server
                    </h3>

                    <p className="mt-3 text-sm text-slate-400">
                      Provides a simulated FTP service for capturing and
                      monitoring attacker activity.
                    </p>
                  </div>

                  {/* Telnet */}
                  <div className="rounded-xl border border-slate-800 bg-[#080d18] p-6">
                    <h3 className="text-lg font-semibold text-cyan-400">
                      💻 Telnet
                    </h3>

                    <p className="mt-3 text-sm text-slate-400">
                      Provides a simulated Telnet service for monitoring
                      attacker login and command activity.
                    </p>
                  </div>

                </div>

              </div>

            </div>
          )}

          {/* Footer */}
          <footer className="mt-8 border-t border-slate-800 pt-6 text-center text-xs text-slate-600">
            SentinelTrap © 2026 • Cybersecurity Honeypot Monitoring Platform
          </footer>

        </div>

      </section>

    </main>
  );
}