from datetime import datetime
import logging

import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy


class FredbV2Strategy(IStrategy):
    """
    FredbV2 - RSI-dip-in-uptrend strategy for Binance spot, 15m.

    The original version bought every RSI oversold dip with no trend filter
    and a static stoploss that wasn't actually the binding constraint
    (PF 0.27: winrate 65.9% but average loss -8.18% vs average win +0.18%).
    This version fixes both sides of that:
      - Entries require a confirmed uptrend (EMA20 > EMA50 > EMA<n>, plus an
        ADX trend-strength floor) so an RSI dip is bought as a pullback
        inside a trend, not as an unfiltered falling knife.
      - The exit signal only fires on overbought RSI - it never overlaps
        with (and silently cancels) an oversold-RSI entry signal, which is
        what caused an earlier iteration of this strategy to enter 0 trades
        despite valid signals.
      - Exits use a tight ATR-based stoploss that ratchets toward
        break-even as the trade moves into profit, capping loss size
        instead of relying on a single wide static stoploss.

    Defaults below are the best epoch (PF 2.13, +1.13%, 23 trades, 0.38% max
    drawdown, 52.2% winrate) from a 500-epoch hyperopt run (ProfitFactor
    HyperOptLoss, spaces: buy sell roi stoploss trailing) over 2025-05-16 to
    2025-08-16, 15m, BTC/ETH/SOL-USDT. Re-run hyperopt against fresh data
    periodically - these numbers will drift as the market regime changes.
    """

    INTERFACE_VERSION = 3

    timeframe = "15m"
    startup_candle_count = 250
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    can_short = False
    position_adjustment_enable = False

    # PROD LOCK v1 risk envelope. Freqtrade protections are evaluated by the
    # engine and survive strategy restarts, unlike ad-hoc in-memory timers.
    @property
    def protections(self):
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 2},
            {
                "method": "StoplossGuard",
                "lookback_period_candles": 96,
                "trade_limit": 2,
                "stop_duration_candles": 16,
                "only_per_pair": False,
            },
            {
                "method": "MaxDrawdown",
                "lookback_period_candles": 192,
                "trade_limit": 12,
                "stop_duration_candles": 32,
                "max_allowed_drawdown": 0.08,
            },
        ]

    minimal_roi = {"0": 0.231, "81": 0.125, "183": 0.045, "519": 0}
    stoploss = -0.246  # hard safety net; real exits happen via custom_stoploss
    use_custom_stoploss = True

    trailing_stop = True
    trailing_stop_positive = 0.32
    trailing_stop_positive_offset = 0.381
    trailing_only_offset_is_reached = False

    LIVE_PF_FLOOR = 1.30
    LIVE_PF_MIN_TRADES = 20
    RISK_PER_TRADE = 0.01
    MAX_STAKE_EQUITY_PCT = 0.20
    EQUITY_DRAWDOWN_THROTTLE = 0.05
    DAILY_LOSS_LIMIT = -0.05
    _live_circuit_open = False
    _circuit_reason = ""
    _last_circuit_alert = ""
    logger = logging.getLogger(__name__)

    # --- Hyperopt spaces -------------------------------------------------
    buy_rsi = IntParameter(25, 45, default=40, space="buy", optimize=True)
    buy_adx = IntParameter(15, 35, default=33, space="buy", optimize=True)
    buy_ema_long = IntParameter(100, 250, default=233, space="buy", optimize=True)

    sell_rsi = IntParameter(60, 85, default=72, space="sell", optimize=True)

    stop_atr_mult = DecimalParameter(1.5, 4.0, default=3.1, decimals=1, space="sell", optimize=True)

    order_types = {
        "entry": "limit",
        "exit": "limit",
        "emergency_exit": "market",
        "force_entry": "market",
        "force_exit": "market",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)

        for length in self.buy_ema_long.range:
            dataframe[f"ema{length}"] = ta.EMA(dataframe, timeperiod=length)

        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ema_long_col = f"ema{self.buy_ema_long.value}"

        dataframe.loc[
            (
                (dataframe["rsi"] < self.buy_rsi.value)
                & (dataframe["ema20"] > dataframe["ema50"])
                & (dataframe["ema50"] > dataframe[ema_long_col])
                & (dataframe["adx"] > self.buy_adx.value)
                & (dataframe["volume"] > 0)
            ),
            "enter_long",
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Signal exit only fires on overbought RSI - downside is handled by
        # minimal_roi / trailing_stop / custom_stoploss instead, so this
        # can never coincide with (and cancel) an oversold-RSI entry signal.
        dataframe.loc[dataframe["rsi"] > self.sell_rsi.value, "exit_long"] = 1

        return dataframe

    def custom_stoploss(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> float:
        """
        ATR-based stop: caps the initial risk to `stop_atr_mult * ATR` (as a
        fraction of entry price) instead of a wide fixed percentage, which is
        what let average losses run to -8% in the original version.
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe.empty:
            return self.stoploss

        last_candle = dataframe.iloc[-1]
        atr = last_candle["atr"]
        if atr <= 0 or trade.open_rate <= 0:
            return self.stoploss

        atr_stop_pct = -(self.stop_atr_mult.value * atr) / trade.open_rate

        # Never risk more than the hard safety-net stoploss. Lock progressively
        # more profit as the trade moves in our favour; this is deterministic
        # and uses only the latest closed candle (no future information).
        atr_stop_pct = max(atr_stop_pct, self.stoploss)
        if current_profit > 0.06:
            atr_stop_pct = max(atr_stop_pct, 0.03)
        elif current_profit > 0.035:
            atr_stop_pct = max(atr_stop_pct, 0.012)
        elif current_profit > 0.02:
            atr_stop_pct = max(atr_stop_pct, -0.002)

        return atr_stop_pct

    def bot_loop_start(self, current_time: datetime, **kwargs) -> None:
        """Open a live-entry circuit when realized PF falls below 1.30."""
        runmode = self.config.get("runmode")
        if getattr(runmode, "value", runmode) in {"backtest", "hyperopt"}:
            return
        closed = list(Trade.get_trades_proxy(is_open=False))[-100:]
        today = current_time.date()
        daily_pnl = sum(
            float(t.close_profit_abs or 0)
            for t in closed
            if t.close_date and t.close_date.date() == today
        )
        equity = max(float(self.wallets.get_total_stake_amount()), 1.0)
        if daily_pnl / equity <= self.DAILY_LOSS_LIMIT:
            self._live_circuit_open = True
            self._circuit_reason = f"daily realized loss {daily_pnl / equity:.1%} <= -5.0%"
            self.logger.critical("DAILY LOSS CIRCUIT OPEN: %s", self._circuit_reason)
            if self.dp and self._last_circuit_alert != self._circuit_reason:
                self.dp.send_msg(f"🚨 Fredb DAILY LOSS CIRCUIT OPEN: {self._circuit_reason}")
                self._last_circuit_alert = self._circuit_reason
            return
        if len(closed) < self.LIVE_PF_MIN_TRADES:
            return
        wins = sum(max(float(t.close_profit_abs or 0), 0) for t in closed)
        losses = abs(sum(min(float(t.close_profit_abs or 0), 0) for t in closed))
        live_pf = wins / losses if losses > 0 else float("inf")
        self._live_circuit_open = live_pf < self.LIVE_PF_FLOOR
        self._circuit_reason = f"realized PF {live_pf:.2f} < {self.LIVE_PF_FLOOR:.2f}"
        if self._live_circuit_open:
            self.logger.error("LIVE CIRCUIT OPEN: %s", self._circuit_reason)
            if self.dp and self._last_circuit_alert != self._circuit_reason:
                self.dp.send_msg(f"🚨 Fredb LIVE PF CIRCUIT OPEN: {self._circuit_reason}")
                self._last_circuit_alert = self._circuit_reason

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float,
                            rate: float, time_in_force: str,
                            current_time: datetime, entry_tag: str | None,
                            side: str, **kwargs) -> bool:
        if self._live_circuit_open:
            self.logger.error("Entry blocked for %s: %s", pair, self._circuit_reason)
            return False
        return True

    def custom_stake_amount(self, pair: str, current_time: datetime,
                            current_rate: float, proposed_stake: float,
                            min_stake: float | None, max_stake: float,
                            leverage: float, entry_tag: str | None, side: str,
                            **kwargs) -> float:
        """ATR risk sizing, capped by equity and throttled after drawdown."""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe.empty or current_rate <= 0:
            return min(proposed_stake, max_stake)
        atr = float(dataframe.iloc[-1].get("atr", 0) or 0)
        if atr <= 0:
            return min(proposed_stake, max_stake)
        equity = float(self.wallets.get_total_stake_amount())
        risk_distance = max((self.stop_atr_mult.value * atr) / current_rate, 0.005)
        risk_sized = equity * self.RISK_PER_TRADE / risk_distance
        equity_cap = equity * self.MAX_STAKE_EQUITY_PCT
        # Throttle exposure when current equity is 5%+ below starting equity.
        start = float(self.config.get("dry_run_wallet", equity) or equity)
        throttle = 0.5 if equity < start * (1 - self.EQUITY_DRAWDOWN_THROTTLE) else 1.0
        stake = min(risk_sized, equity_cap, max_stake) * throttle
        return max(stake, min_stake or 0)
