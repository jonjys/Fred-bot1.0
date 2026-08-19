"use client";

import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { EquityPoint } from "../lib/types";

export default function DrawdownChart({ data }: { data: EquityPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={90}>
      <AreaChart data={data} margin={{ top: 4, right: 16, bottom: 0, left: 0 }}>
        <XAxis dataKey="date" hide />
        <YAxis
          reversed
          domain={[0, "dataMax"]}
          tick={{ fontSize: 9, fill: "#9aa4b2" }}
          width={40}
          tickFormatter={(v) => `${v}%`}
        />
        <Tooltip
          contentStyle={{ background: "#111114", border: "1px solid #222226", fontSize: 12 }}
          formatter={(v: number) => [`-${v}%`, "Drawdown"]}
        />
        <Area
          type="monotone"
          dataKey="drawdown_pct"
          stroke="#FF5C5C"
          strokeWidth={1.5}
          fill="#FF5C5C"
          fillOpacity={0.15}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
