"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const data = [
  { name: "Mon", events: 12 },
  { name: "Tue", events: 19 },
  { name: "Wed", events: 8 },
  { name: "Thu", events: 25 },
  { name: "Fri", events: 14 },
];

export default function Analytics() {
  return (
    <div className="p-4 rounded-xl bg-neutral-900 text-white">
      <h2 className="text-lg font-semibold mb-4">Analytics</h2>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data}>
          <XAxis dataKey="name" stroke="#aaa" />
          <YAxis stroke="#aaa" />
          <Tooltip />
          <Bar dataKey="events" fill="#22c55e" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}