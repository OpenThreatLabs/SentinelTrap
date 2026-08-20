"use client";

import { useState } from "react";
import { Download, FileText, Table, ShieldCheck, Database } from "lucide-react";

export default function ExportPanel() {
  const [downloading, setDownloading] = useState<string | null>(null);

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "";

  const handleDownload = async (format: "pdf" | "csv" | "json" | "stix" | "cef") => {
    try {
      setDownloading(format);

      let url = `${apiBase}/api/reports/export?format=${format}`;
      let filename = `SentinelTrap_attack_logs.${format}`;

      if (format === "pdf") {
        url = `${apiBase}/api/reports/pdf`;
        filename = "SentinelTrap_Forensic_Incident_Report.pdf";
      } else if (format === "stix") {
        url = `${apiBase}/api/reports/stix`;
        filename = "SentinelTrap_STIX21_Threat_Bundle.json";
      } else if (format === "cef") {
        url = `${apiBase}/api/reports/cef`;
        filename = "SentinelTrap_SIEM_CEF.log";
      }

      const res = await fetch(url);
      if (!res.ok) throw new Error("Export failed");

      const blob = await res.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      console.error("Failed to export report:", err);
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0b1120] p-6 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-cyan-500/10 p-2 text-cyan-400">
          <Download className="h-5 w-5" />
        </div>
        <div>
          <h2 className="font-semibold text-white">Forensic Threat Telemetry Exports</h2>
          <p className="text-xs text-slate-500">Download captured attacker logs, SIEM telemetry, and forensic PDF reports</p>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {/* PDF Report */}
        <button
          onClick={() => handleDownload("pdf")}
          disabled={downloading !== null}
          className="flex items-center justify-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-xs font-semibold text-red-400 transition hover:bg-red-500/20 disabled:opacity-50"
        >
          <FileText className="h-4 w-4" />
          {downloading === "pdf" ? "Generating..." : "Forensic PDF"}
        </button>

        {/* CSV Logs */}
        <button
          onClick={() => handleDownload("csv")}
          disabled={downloading !== null}
          className="flex items-center justify-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-xs font-semibold text-emerald-400 transition hover:bg-emerald-500/20 disabled:opacity-50"
        >
          <Table className="h-4 w-4" />
          {downloading === "csv" ? "Exporting..." : "Raw CSV Logs"}
        </button>

        {/* STIX 2.1 */}
        <button
          onClick={() => handleDownload("stix")}
          disabled={downloading !== null}
          className="flex items-center justify-center gap-2 rounded-lg border border-purple-500/20 bg-purple-500/10 px-4 py-3 text-xs font-semibold text-purple-400 transition hover:bg-purple-500/20 disabled:opacity-50"
        >
          <ShieldCheck className="h-4 w-4" />
          {downloading === "stix" ? "Building..." : "STIX 2.1 JSON"}
        </button>

        {/* CEF / Syslog */}
        <button
          onClick={() => handleDownload("cef")}
          disabled={downloading !== null}
          className="flex items-center justify-center gap-2 rounded-lg border border-cyan-500/20 bg-cyan-500/10 px-4 py-3 text-xs font-semibold text-cyan-400 transition hover:bg-cyan-500/20 disabled:opacity-50"
        >
          <Database className="h-4 w-4" />
          {downloading === "cef" ? "Exporting..." : "SIEM CEF Log"}
        </button>
      </div>
    </div>
  );
}