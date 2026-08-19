import EquityChart from "./components/EquityChart";
import FallbackBanner from "./components/FallbackBanner";
import RunBacktestButton from "./components/RunBacktestButton";
import { getSummary } from "./lib/getSummary";

// Re-read backtest-latest.json on every request instead of baking it into
// the static build, so "Run Backtest" (and a fresh CI-published file) show
// up without a full redeploy.
export const dynamic = "force-dynamic";

const CARD = "#111114";
const BORDER = "#222226";
const LIVE = "#3DFF8A";
const TEXT = "#e6e9ef";
const MUTED = "#9aa4b2";

function StatCard({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div
      style={{
        background: CARD,
        border: `1px solid ${BORDER}`,
        borderRadius: 10,
        padding: "10px 12px",
      }}
    >
      <div style={{ fontSize: 11, color: MUTED, marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 700, color: accent ?? TEXT, lineHeight: 1.1 }}>
        {value}
      </div>
    </div>
  );
}

function LiveBadge() {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: 0.5,
        color: LIVE,
        border: `1px solid ${LIVE}40`,
        background: `${LIVE}14`,
        borderRadius: 999,
        padding: "3px 8px",
      }}
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: LIVE,
          boxShadow: `0 0 6px ${LIVE}`,
        }}
      />
      LIVE
    </span>
  );
}

export default function Home() {
  const summary = getSummary();

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "16px 12px 40px", color: TEXT }}>
      <style>{`
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 8px;
        }
        @media (min-width: 560px) {
          .stats-grid { grid-template-columns: repeat(5, minmax(0, 1fr)); }
        }
        table.pairs { width: 100%; border-collapse: collapse; font-size: 12.5px; }
        table.pairs th, table.pairs td { padding: 7px 10px; white-space: nowrap; }
      `}</style>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: 10,
          marginBottom: 14,
        }}
      >
        <div style={{ minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            <h1 style={{ margin: 0, fontSize: 20 }}>Fred Bot Dashboard</h1>
            {summary && <LiveBadge />}
          </div>
          <p style={{ margin: "3px 0 0", color: MUTED, fontSize: 12 }}>
            {summary
              ? `${summary.strategy} · ${summary.exchange ?? "unknown exchange"} · ${summary.timerange}`
              : "No backtest results yet"}
          </p>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
          <RunBacktestButton />
          <span style={{ fontSize: 10, color: "#6b7280" }}>Local only</span>
        </div>
      </div>

      {!summary && (
        <div
          style={{
            background: CARD,
            border: `1px dashed ${BORDER}`,
            borderRadius: 10,
            padding: 24,
            color: MUTED,
            textAlign: "center",
            fontSize: 13,
          }}
        >
          No backtest results published yet. Push to the repo to trigger the{" "}
          <code>backtest.yml</code> GitHub Action, or run{" "}
          <code>freqtrade backtesting</code> locally and click &quot;Run Backtest&quot;.
        </div>
      )}

      {summary && summary.exchange !== "binance" && (
        <FallbackBanner exchange={summary.exchange ?? "unknown"} />
      )}

      {summary && (
        <>
          <div className="stats-grid" style={{ marginBottom: 16 }}>
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
            <StatCard label="Max DD" value={`${summary.max_drawdown_pct}%`} />
            <StatCard label="Trades" value={`${summary.total_trades}`} />
          </div>

          <section style={{ marginBottom: 16 }}>
            <h2 style={{ fontSize: 13, color: MUTED, fontWeight: 500, margin: "0 0 6px" }}>
              Equity Curve
            </h2>
            <div
              style={{
                background: CARD,
                border: `1px solid ${BORDER}`,
                borderRadius: 10,
                padding: 10,
              }}
            >
              <EquityChart data={summary.equity_curve} />
            </div>
          </section>

          <section>
            <h2 style={{ fontSize: 13, color: MUTED, fontWeight: 500, margin: "0 0 6px" }}>
              Per-pair results
            </h2>
            <div
              style={{
                background: CARD,
                border: `1px solid ${BORDER}`,
                borderRadius: 10,
                overflowX: "auto",
              }}
            >
              <table className="pairs">
                <thead>
                  <tr style={{ textAlign: "left", color: MUTED, borderBottom: `1px solid ${BORDER}` }}>
                    <th>Pair</th>
                    <th>Trades</th>
                    <th>Avg %</th>
                    <th>Total USDT</th>
                    <th>Win%</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.pairs.map((p) => (
                    <tr key={p.pair} style={{ borderBottom: `1px solid ${BORDER}` }}>
                      <td>{p.pair}</td>
                      <td>{p.trades}</td>
                      <td>{p.avg_profit_pct}%</td>
                      <td>{p.total_profit_abs}</td>
                      <td>{p.winrate_pct}%</td>
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
