"use client";

import { useState, useEffect } from "react";
import { Shield, Sun, Moon } from "lucide-react";

import Header from "../components/Header";
import MetricCards from "../components/MetricCards";
import SessionSidebar from "../components/SessionSidebar";
import Alerts from "../components/Alerts";
import Analytics from "../components/Analytics";
import SessionsView from "../components/SessionsView";
import BackendFeaturesView from "../components/BackendFeaturesView";

export default function Home() {
  const [activePage, setActivePage] = useState("Dashboard");
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "light") {
      setIsDark(false);
      document.documentElement.classList.remove("dark");
    } else {
      setIsDark(true);
      document.documentElement.classList.add("dark");
    }
  }, []);

  const toggleTheme = () => {
    const newMode = !isDark;
    setIsDark(newMode);
    if (newMode) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  };

  return (
    <main className="min-h-screen bg-zinc-50 dark:bg-black text-zinc-900 dark:text-zinc-100 transition-colors duration-200 relative">
      {/* Top Navbar */}
      <Header
        activePage={activePage}
        setActivePage={setActivePage}
        isDark={isDark}
        setIsDark={setIsDark}
      />

      {/* Main Content Container */}
      <section className="mx-auto max-w-7xl px-6 py-8">
        {/* Page Heading */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500 font-mono">
              Security Operations Center
            </p>
            <h2 className="mt-1 text-2xl font-bold tracking-tight text-zinc-900 dark:text-white">
              {activePage}
            </h2>
          </div>
        </div>

        {/* Dashboard View */}
        {activePage === "Dashboard" && (
          <>
            <MetricCards />

            <div className="mt-8 grid gap-6 xl:grid-cols-3">
              <div className="xl:col-span-1">
                <SessionSidebar />
              </div>

              <div className="xl:col-span-2">
                <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-8 shadow-sm">
                  <h3 className="text-sm font-semibold text-zinc-900 dark:text-white">
                    Security Monitoring Workspace
                  </h3>
                  <p className="mt-1 text-xs text-zinc-500">
                    Real-time decoy listening telemetry and automated honeytoken analysis.
                  </p>

                  <div className="mt-8 rounded-lg border border-dashed border-zinc-200 dark:border-zinc-800 p-12 text-center">
                    <Shield className="mx-auto h-8 w-8 text-zinc-400" />
                    <p className="mt-4 text-xs font-semibold text-zinc-800 dark:text-zinc-200">
                      Security Engine Armed
                    </p>
                    <p className="mt-1 text-[11px] text-zinc-500">
                      All 9 honeypot listener daemons are monitoring incoming adversarial traffic.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Sessions */}
        {activePage === "Sessions" && <SessionsView />}

        {/* Alerts */}
        {activePage === "Alerts" && <Alerts />}

        {/* Analytics */}
        {activePage === "Analytics" && <Analytics />}

        {/* Backend Features */}
        {activePage === "Backend Features" && <BackendFeaturesView />}
      </section>

      {/* Floating Circular Day / Light Toggle Button in Bottom Right Corner */}
      <button
        onClick={toggleTheme}
        aria-label="Toggle light/dark theme"
        title={isDark ? "Switch to Day Mode" : "Switch to Dark Mode"}
        className="fixed bottom-6 right-6 z-50 flex h-12 w-12 items-center justify-center rounded-full border border-zinc-200 dark:border-zinc-800 bg-white/90 dark:bg-zinc-900/90 text-zinc-800 dark:text-zinc-200 shadow-xl shadow-black/10 dark:shadow-cyan-500/10 backdrop-blur-md transition-all hover:scale-110 active:scale-95 hover:border-cyan-400/60"
      >
        {isDark ? (
          <Sun className="h-5 w-5 text-amber-400 transition-transform duration-300 hover:rotate-45" />
        ) : (
          <Moon className="h-5 w-5 text-indigo-600 transition-transform duration-300 hover:-rotate-12" />
        )}
      </button>
    </main>
  );
}
