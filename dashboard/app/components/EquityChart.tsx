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
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 8, right: 24, bottom: 8, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2f3a" />
        <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#9aa4b2" }} minTickGap={40} />
        <YAxis
          domain={["auto", "auto"]}
          tick={{ fontSize: 11, fill: "#9aa4b2" }}
          width={70}
        />
        <Tooltip
          contentStyle={{ background: "#161a23", border: "1px solid #2a2f3a" }}
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
