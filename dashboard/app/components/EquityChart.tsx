"use client";

import { useMemo, useState } from "react";
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

const RANGES = ["7D", "30D", "ALL"] as const;
type Range = (typeof RANGES)[number];

function filterByRange(data: EquityPoint[], range: Range): EquityPoint[] {
  if (range === "ALL" || data.length === 0) return data;
  const days = range === "7D" ? 7 : 30;
  const lastDate = new Date(data[data.length - 1].date);
  const cutoff = new Date(lastDate);
  cutoff.setDate(cutoff.getDate() - days);
  return data.filter((d) => new Date(d.date) >= cutoff);
}

export default function EquityChart({ data }: { data: EquityPoint[] }) {
  const [range, setRange] = useState<Range>("ALL");
  const filtered = useMemo(() => filterByRange(data, range), [data, range]);

  return (
    <div>
      <div className="mb-2 flex justify-end gap-1">
        {RANGES.map((r) => (
          <button
            key={r}
            onClick={() => setRange(r)}
            className={`rounded px-2 py-0.5 text-[10px] font-medium ${
              range === r ? "bg-live/15 text-live" : "text-muted hover:bg-white/5"
            }`}
          >
            {r}
          </button>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={165}>
        <LineChart data={filtered} margin={{ top: 4, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#222226" />
          <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#9aa4b2" }} minTickGap={40} />
          <YAxis domain={["auto", "auto"]} tick={{ fontSize: 10, fill: "#9aa4b2" }} width={56} />
          <Tooltip
            contentStyle={{ background: "#111114", border: "1px solid #222226" }}
            labelStyle={{ color: "#e6e9ef" }}
          />
          <Line type="monotone" dataKey="balance" stroke="#4f9dff" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
