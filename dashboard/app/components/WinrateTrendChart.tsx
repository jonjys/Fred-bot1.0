"use client";

import { Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { WinrateTrendPoint } from "../lib/types";

export default function WinrateTrendChart({ data }: { data: WinrateTrendPoint[] }) {
  if (data.length === 0) {
    return <div className="flex h-32 items-center justify-center text-xs text-muted">No trades yet</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={110}>
      <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
        <XAxis dataKey="index" tick={{ fontSize: 9, fill: "#9aa4b2" }} hide />
        <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: "#9aa4b2" }} width={28} />
        <ReferenceLine y={50} stroke="#222226" strokeDasharray="3 3" />
        <Tooltip
          contentStyle={{ background: "#111114", border: "1px solid #222226", fontSize: 12 }}
          labelFormatter={(i) => `Trade #${i}`}
          formatter={(v: number) => [`${v}%`, "Rolling winrate"]}
        />
        <Line type="monotone" dataKey="winrate_pct" stroke="#3DFF8A" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
