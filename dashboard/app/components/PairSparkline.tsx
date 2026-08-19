"use client";

import { Line, LineChart, ResponsiveContainer } from "recharts";

export default function PairSparkline({ values, positive }: { values: number[]; positive: boolean }) {
  if (values.length < 2) return <span className="text-[10px] text-muted">—</span>;
  const data = values.map((v, i) => ({ i, v }));
  return (
    <ResponsiveContainer width={64} height={22}>
      <LineChart data={data} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
        <Line
          type="monotone"
          dataKey="v"
          stroke={positive ? "#3DFF8A" : "#FF5C5C"}
          strokeWidth={1.5}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
