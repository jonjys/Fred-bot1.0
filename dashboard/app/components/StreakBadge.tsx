import type { CurrentStreak } from "../lib/types";

export default function StreakBadge({ streak }: { streak: CurrentStreak }) {
  if (!streak.type || streak.count === 0) {
    return <span className="text-lg font-bold text-zinc-400">—</span>;
  }
  const isWin = streak.type === "win";
  return (
    <span className={`text-lg font-bold ${isWin ? "text-profit" : "text-loss"}`}>
      {streak.count} {isWin ? "W" : "L"} {isWin ? "▲" : "▼"}
    </span>
  );
}
