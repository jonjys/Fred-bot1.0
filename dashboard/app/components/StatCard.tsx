import AnimatedNumber from "./AnimatedNumber";

export default function StatCard({
  id,
  label,
  value,
  decimals = 0,
  suffix = "",
  prefix = "",
  accent,
  sub,
}: {
  id?: string;
  label: string;
  value: number;
  decimals?: number;
  suffix?: string;
  prefix?: string;
  accent?: "profit" | "loss" | "neutral";
  sub?: string;
}) {
  const color =
    accent === "profit" ? "text-profit" : accent === "loss" ? "text-loss" : "text-zinc-100";

  return (
    <div id={id} className="rounded-lg border border-border bg-card p-2.5 transition-shadow">
      <div className="mb-1 truncate text-[10.5px] text-muted">{label}</div>
      <div className={`text-lg font-bold leading-tight ${color}`}>
        <AnimatedNumber value={value} decimals={decimals} suffix={suffix} prefix={prefix} />
      </div>
      {sub && <div className="mt-0.5 text-[10px] text-zinc-500">{sub}</div>}
    </div>
  );
}
