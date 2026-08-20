"use client";

export default function ExportPanel() {
  const handleExport = (type: string) => {
    alert(`Exporting as ${type}... (connect this to real export logic later)`);
  };

  return (
    <div className="p-4 rounded-xl bg-neutral-900 text-white flex flex-col gap-3">
      <h2 className="text-lg font-semibold">Export Panel</h2>
      <div className="flex gap-2">
        <button
          onClick={() => handleExport("CSV")}
          className="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700"
        >
          Export CSV
        </button>
        <button
          onClick={() => handleExport("PDF")}
          className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700"
        >
          Export PDF
        </button>
      </div>
    </div>
  );
}