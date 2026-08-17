import { exec } from "child_process";
import { promises as fs } from "fs";
import path from "path";
import { promisify } from "util";
import { NextResponse } from "next/server";

const execAsync = promisify(exec);

/**
 * Re-runs the backtest and republishes the dashboard's summary. This shells
 * out to a local `freqtrade` install, so it only works when the dashboard
 * is run next to the bot (e.g. `npm run dev` on your own machine) - it is
 * not something a Vercel serverless function can do, since Vercel has no
 * Python/freqtrade runtime and a read-only filesystem outside /tmp.
 */
export async function POST() {
  const botDir = path.join(process.cwd(), "..", "bot");
  const timerange = "20250516-20250816";

  try {
    await execAsync(
      `freqtrade backtesting --strategy FredbV2Strategy --timerange ${timerange} --export trades`,
      { cwd: botDir },
    );
    await execAsync("python3 scripts/export_summary.py", { cwd: botDir });

    const summaryPath = path.join(botDir, "user_data", "backtest_results", "latest.json");
    const publicPath = path.join(process.cwd(), "public", "backtest-latest.json");
    await fs.copyFile(summaryPath, publicPath);

    return NextResponse.json({ ok: true });
  } catch (err) {
    return NextResponse.json(
      { ok: false, error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
