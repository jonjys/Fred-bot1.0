"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { EquityPoint } from "../lib/types";

export default function EquityChart({ data }: { data: EquityPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#222226" />
        <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#9aa4b2" }} minTickGap={40} />
        <YAxis
          domain={["auto", "auto"]}
          tick={{ fontSize: 10, fill: "#9aa4b2" }}
          width={56}
        />
        <Tooltip
          contentStyle={{ background: "#111114", border: "1px solid #222226" }}
          labelStyle={{ color: "#e6e9ef" }}
        />
        <Line
          type="monotone"
          dataKey="balance"
          stroke="#4f9dff"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
