"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { WinLossSizes } from "../lib/types";

export default function DistributionHistogram({ data }: { data: WinLossSizes }) {
  if (data.buckets.length === 0) {
    return <div className="flex h-40 items-center justify-center text-xs text-muted">No trades yet</div>;
  }

  const chartData = data.buckets.map((b) => ({
    label: `${b.range_low}%`,
    count: b.count,
    positive: b.range_low >= 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={130}>
      <BarChart data={chartData} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
        <XAxis dataKey="label" tick={{ fontSize: 9, fill: "#9aa4b2" }} interval={1} />
        <YAxis allowDecimals={false} tick={{ fontSize: 9, fill: "#9aa4b2" }} width={24} />
        <Tooltip
          contentStyle={{ background: "#111114", border: "1px solid #222226", fontSize: 12 }}
          labelStyle={{ color: "#e6e9ef" }}
          formatter={(v: number) => [`${v} trades`, "Count"]}
        />
        <Bar dataKey="count" radius={[3, 3, 0, 0]}>
          {chartData.map((d, i) => (
            <Cell key={i} fill={d.positive ? "#3DFF8A" : "#FF5C5C"} fillOpacity={0.85} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
