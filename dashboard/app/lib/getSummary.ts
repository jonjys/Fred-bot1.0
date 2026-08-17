import fs from "fs";
import path from "path";
import type { BacktestSummary } from "./types";

/**
 * The dashboard reads a small, pre-flattened summary from public/, written
 * by bot/scripts/export_summary.py (see backtest.yml). public/ is always
 * bundled with the Next.js deployment, unlike the sibling bot/ directory
 * outside the dashboard's Vercel root - so this is the reliable path,
 * even though bot/user_data/backtest_results/latest.json is the real
 * source of truth the CI job generates it from.
 */
export function getSummary(): BacktestSummary | null {
  const filePath = path.join(process.cwd(), "public", "backtest-latest.json");
  if (!fs.existsSync(filePath)) {
    return null;
  }
  const raw = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(raw) as BacktestSummary;
}
