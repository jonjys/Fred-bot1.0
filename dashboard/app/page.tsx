import EquityChart from "./components/EquityChart";
import RunBacktestButton from "./components/RunBacktestButton";
import { getSummary } from "./lib/getSummary";

// Re-read backtest-latest.json on every request instead of baking it into
// the static build, so "Run Backtest" (and a fresh CI-published file) show
// up without a full redeploy.
export const dynamic = "force-dynamic";

function StatCard({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div
      style={{
        background: "#161a23",
        border: "1px solid #2a2f3a",
        borderRadius: 12,
        padding: "16px 20px",
        minWidth: 140,
      }}
    >
      <div style={{ fontSize: 12, color: "#9aa4b2", marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 700, color: accent ?? "#e6e9ef" }}>{value}</div>
    </div>
  );
}

export default function Home() {
  const summary = getSummary();

  return (
    <main style={{ maxWidth: 1000, margin: "0 auto", padding: "40px 24px" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: 16,
          marginBottom: 32,
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: 28 }}>Fred Bot Dashboard</h1>
          <p style={{ margin: "4px 0 0", color: "#9aa4b2", fontSize: 14 }}>
            {summary
              ? `${summary.strategy} · ${summary.exchange ?? "unknown exchange"} · ${summary.timerange}`
              : "No backtest results yet"}
          </p>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6 }}>
          <RunBacktestButton />
          <span style={{ fontSize: 11, color: "#6b7280" }}>
            Only works when run locally next to a freqtrade install
          </span>
        </div>
      </div>

      {!summary && (
        <div
          style={{
            background: "#161a23",
            border: "1px dashed #2a2f3a",
            borderRadius: 12,
            padding: 32,
            color: "#9aa4b2",
            textAlign: "center",
          }}
        >
          No backtest results published yet. Push to the repo to trigger the{" "}
          <code>backtest.yml</code> GitHub Action, or run{" "}
          <code>freqtrade backtesting</code> locally and click &quot;Run Backtest&quot;.
        </div>
      )}

      {summary && summary.exchange !== "binance" && (
        <div
          style={{
            background: "#2a1f0f",
            border: "1px solid #5a4020",
            borderRadius: 12,
            padding: "12px 16px",
            marginBottom: 24,
            color: "#e8c07d",
            fontSize: 13,
          }}
        >
          These numbers are from <strong>{summary.exchange}</strong>, not Binance.
          The <code>backtest.yml</code> workflow falls back to OKX when Binance
          blocks the CI runner&apos;s IP (HTTP 451) — see the README. Re-run the
          workflow, or run it yourself somewhere Binance is reachable, for
          Binance-specific numbers.
        </div>
      )}

      {summary && (
        <>
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: 12,
              marginBottom: 32,
            }}
          >
            <StatCard
              label="Total %"
              value={`${summary.total_profit_pct >= 0 ? "+" : ""}${summary.total_profit_pct}%`}
              accent={summary.total_profit_pct >= 0 ? "#3ddc97" : "#ff6b6b"}
            />
            <StatCard
              label="Profit Factor"
              value={summary.profit_factor !== null ? summary.profit_factor.toFixed(2) : "—"}
              accent={
                summary.profit_factor !== null && summary.profit_factor >= 1.5
                  ? "#3ddc97"
                  : "#ff6b6b"
              }
            />
            <StatCard label="Winrate" value={`${summary.winrate_pct}%`} />
            <StatCard label="Max Drawdown" value={`${summary.max_drawdown_pct}%`} />
            <StatCard label="Trades" value={`${summary.total_trades}`} />
          </div>

          <section style={{ marginBottom: 32 }}>
            <h2 style={{ fontSize: 16, color: "#9aa4b2", fontWeight: 500 }}>Equity Curve</h2>
            <div
              style={{
                background: "#161a23",
                border: "1px solid #2a2f3a",
                borderRadius: 12,
                padding: 16,
              }}
            >
              <EquityChart data={summary.equity_curve} />
            </div>
          </section>

          <section>
            <h2 style={{ fontSize: 16, color: "#9aa4b2", fontWeight: 500 }}>Per-pair results</h2>
            <div
              style={{
                background: "#161a23",
                border: "1px solid #2a2f3a",
                borderRadius: 12,
                overflow: "hidden",
              }}
            >
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
                <thead>
                  <tr style={{ textAlign: "left", color: "#9aa4b2", borderBottom: "1px solid #2a2f3a" }}>
                    <th style={{ padding: "10px 16px" }}>Pair</th>
                    <th style={{ padding: "10px 16px" }}>Trades</th>
                    <th style={{ padding: "10px 16px" }}>Avg %</th>
                    <th style={{ padding: "10px 16px" }}>Total USDT</th>
                    <th style={{ padding: "10px 16px" }}>Win%</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.pairs.map((p) => (
                    <tr key={p.pair} style={{ borderBottom: "1px solid #1f232c" }}>
                      <td style={{ padding: "10px 16px" }}>{p.pair}</td>
                      <td style={{ padding: "10px 16px" }}>{p.trades}</td>
                      <td style={{ padding: "10px 16px" }}>{p.avg_profit_pct}%</td>
                      <td style={{ padding: "10px 16px" }}>{p.total_profit_abs}</td>
                      <td style={{ padding: "10px 16px" }}>{p.winrate_pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </main>
  );
}
