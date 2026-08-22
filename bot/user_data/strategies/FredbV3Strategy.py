from datetime import timedelta

import talib.abstract as ta
from pandas import DataFrame

from freqtrade.exchange import timeframe_to_minutes
from freqtrade.persistence import Trade
from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy, informative


class FredbV3Strategy(IStrategy):
    """
    FredbV3 - EXPERIMENTAL. Not prod. Lives only under FredbV3Strategy /
    FredbV3Strategy.json until it clears the same walk-forward gate V2 did,
    with real numbers, on its own branch.

    Origin: the brief was "beat a Polymarket Up/Down scalping bot doing
    ~6 trades/hour at 52% winrate via continuous EV recalculation and
    staggered entry/hedge". That bot's actual edge is delta-hedged
    market-making against a binary CLOB on Polygon - no OHLCV history, no
    ccxt adapter, no simultaneous long+hedge leg model in Freqtrade's
    position engine. Cloning it literally isn't a Freqtrade strategy, it's
    a different product. What follows is what a Freqtrade strategy *can*
    genuinely do that rhymes with the same underlying idea:

      - "EV recalculated continuously" -> a volatility-band filter that
        refuses to enter outside the regime the edge was measured in,
        instead of firing on every raw signal.
      - "staggered entry" -> one bounded, thesis-confirming DCA re-entry
        (adjust_trade_position), never a blind martingale add.
      - "hedge when odds shift" -> a partial scale-out at the first
        R-target (locks in profit while the setup is still live) plus an
        early "regime_flip" exit that bails before the hard stop if the
        1h trend turns against the position - the closest Freqtrade
        analogue to de-risking a position that hasn't hit its target yet.
      - both directions (long AND short, `can_short=True`) - V2 was
        spot-long-only, so this alone roughly doubles the opportunity set
        per pair before any edge-quality argument.

    Regime + entry: 1h EMA50/EMA100 sets a bull/bear/neutral filter (only
    take longs when 1h isn't in a confirmed downtrend, shorts when it
    isn't in a confirmed uptrend), and 1h ADX above `regime_adx_ceiling`
    blocks new entries entirely on that pair - don't mean-revert into a
    trend that's still accelerating. Inside an allowed regime, entry is a
    5m Bollinger %B extreme + RSI(7) extreme + a StochRSI turn (not just a
    level - the cross has to just happen), gated by an ATR% volatility
    band (reject both dead and blown-out conditions) and an above-average
    volume check.

    Exit machinery, deliberately NOT signal-based (populate_exit_trend is
    unused here on purpose - V2's original bug was an entry/exit signal
    overlap silently cancelling trades; this strategy avoids that whole
    bug class by doing every exit decision in custom_stoploss/custom_exit
    instead): an ATR-sized stop that ratchets to near-breakeven once
    `breakeven_trigger` is cleared, a max-holding-time bailout so a scalp
    can't quietly become an unintended swing bag-hold, and the regime-flip
    early exit described above.

    No numbers are baked into the defaults below as "the answer" - unlike
    FredbV2Strategy, this file has not had a hyperopt run committed into
    it yet. Defaults are reasonable starting points for hyperopt/backtest
    to work from, not a claimed result.
    """

    INTERFACE_VERSION = 3

    timeframe = "5m"
    # Capped just under OKX's 5x-per-request sanity limit for 5m (1499).
    # EMA100 (not EMA200) on the 1h informative timeframe is the direct
    # consequence: 100 hourly candles = 1200 5m-equivalent candles, which
    # fits comfortably inside that cap with headroom for the 5m indicators.
    startup_candle_count = 1400
    process_only_new_candles = True
    use_exit_signal = False
    can_short = True
    trading_mode = "futures"
    margin_mode = "isolated"

    position_adjustment_enable = True
    max_entry_position_adjustment = 1

    minimal_roi = {"0": 0.04, "30": 0.02, "90": 0.01, "240": 0}
    stoploss = -0.06  # hard safety net; real exits happen via custom_stoploss
    use_custom_stoploss = True

    trailing_stop = True
    trailing_stop_positive = 0.015
    trailing_stop_positive_offset = 0.025
    trailing_only_offset_is_reached = True

    # Circuit breakers (see the class docstring's prod-plan companion doc):
    # cool down after any close, halt a pair after clustered stoplosses,
    # halt everything if account drawdown breaches the 8% DD target itself.
    protections = [
        {"method": "CooldownPeriod", "stop_duration_candles": 3},
        {
            "method": "StoplossGuard",
            "lookback_period_candles": 96,
            "trade_limit": 3,
            "stop_duration_candles": 24,
            "only_per_pair": True,
        },
        {
            "method": "MaxDrawdown",
            "lookback_period_candles": 288,
            "trade_limit": 10,
            "stop_duration_candles": 12,
            "max_allowed_drawdown": 0.08,
        },
    ]

    # --- Fixed risk controls (not hyperopted - deliberate, not tuned away) ---
    FIXED_LEVERAGE = 2.0
    MAX_SIZE_MULT = 1.5
    MIN_SIZE_MULT = 0.5
    # A pure ATR(14) stop can imply a sub-0.1% stop distance in the calmest
    # part of the vol_min/vol_max band - tighter than round-trip fees plus
    # normal 5m noise, which just farms stopouts regardless of entry
    # quality. Floor it so the stop can be wider than ATR implies, never
    # tighter.
    MIN_STOP_PCT = 0.003

    # --- Hyperopt spaces -------------------------------------------------
    buy_rsi = IntParameter(15, 35, default=25, space="buy", optimize=True)
    buy_bb_percent = DecimalParameter(0.0, 0.35, default=0.15, decimals=2, space="buy", optimize=True)
    regime_adx_ceiling = IntParameter(25, 45, default=35, space="buy", optimize=True)
    vol_min = DecimalParameter(0.0005, 0.003, default=0.0008, decimals=4, space="buy", optimize=True)
    vol_max = DecimalParameter(0.01, 0.04, default=0.02, decimals=3, space="buy", optimize=True)
    min_volume_mult = DecimalParameter(0.5, 1.5, default=0.8, decimals=2, space="buy", optimize=True)
    dca_atr_mult = DecimalParameter(0.5, 2.0, default=1.0, decimals=1, space="buy", optimize=True)
    dca_fraction = DecimalParameter(0.3, 1.0, default=0.5, decimals=1, space="buy", optimize=True)

    sell_rsi = IntParameter(65, 85, default=75, space="sell", optimize=True)
    sell_bb_percent = DecimalParameter(0.65, 1.0, default=0.85, decimals=2, space="sell", optimize=True)
    stop_atr_mult = DecimalParameter(1.0, 5.0, default=2.5, decimals=1, space="sell", optimize=True)
    breakeven_trigger = DecimalParameter(0.01, 0.04, default=0.015, decimals=3, space="sell", optimize=True)
    partial_tp_r_mult = DecimalParameter(0.5, 1.5, default=1.0, decimals=1, space="sell", optimize=True)
    partial_tp_fraction = DecimalParameter(0.3, 0.7, default=0.5, decimals=1, space="sell", optimize=True)
    max_hold_candles = IntParameter(24, 96, default=48, space="sell", optimize=True)

    order_types = {
        "entry": "limit",
        "exit": "limit",
        "emergency_exit": "market",
        "force_entry": "market",
        "force_exit": "market",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    @informative("1h")
    def populate_indicators_1h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema100"] = ta.EMA(dataframe, timeperiod=100)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=7)

        bollinger = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe["bb_upper"] = bollinger["upperband"]
        dataframe["bb_lower"] = bollinger["lowerband"]
        band_width = (dataframe["bb_upper"] - dataframe["bb_lower"]).replace(0, float("nan"))
        dataframe["bb_percent"] = (dataframe["close"] - dataframe["bb_lower"]) / band_width

        stochrsi = ta.STOCHRSI(dataframe, timeperiod=14, fastk_period=3, fastd_period=3)
        dataframe["stochrsi_k"] = stochrsi["fastk"]
        dataframe["stochrsi_d"] = stochrsi["fastd"]

        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["atr_pct_avg"] = dataframe["atr_pct"].rolling(96, min_periods=48).mean()
        dataframe["volume_avg"] = dataframe["volume"].rolling(20, min_periods=10).mean()

        # Regime, from the already-merged 1h informative columns.
        dataframe["regime_bull"] = dataframe["ema50_1h"] > dataframe["ema100_1h"]
        dataframe["regime_bear"] = dataframe["ema50_1h"] < dataframe["ema100_1h"]
        dataframe["trend_extreme_1h"] = dataframe["adx_1h"] > self.regime_adx_ceiling.value

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        vol_ok = (dataframe["atr_pct"] > self.vol_min.value) & (dataframe["atr_pct"] < self.vol_max.value)
        volume_ok = dataframe["volume"] > dataframe["volume_avg"] * self.min_volume_mult.value

        stochrsi_turn_up = (dataframe["stochrsi_k"] > dataframe["stochrsi_d"]) & (
            dataframe["stochrsi_k"].shift(1) <= dataframe["stochrsi_d"].shift(1)
        )
        stochrsi_turn_down = (dataframe["stochrsi_k"] < dataframe["stochrsi_d"]) & (
            dataframe["stochrsi_k"].shift(1) >= dataframe["stochrsi_d"].shift(1)
        )

        long_cond = (
            (~dataframe["regime_bear"])
            & (~dataframe["trend_extreme_1h"])
            & (dataframe["bb_percent"] < self.buy_bb_percent.value)
            & (dataframe["rsi"] < self.buy_rsi.value)
            & stochrsi_turn_up
            & (dataframe["stochrsi_k"] < 40)
            & vol_ok
            & volume_ok
            & (dataframe["volume"] > 0)
        )

        short_cond = (
            (~dataframe["regime_bull"])
            & (~dataframe["trend_extreme_1h"])
            & (dataframe["bb_percent"] > self.sell_bb_percent.value)
            & (dataframe["rsi"] > self.sell_rsi.value)
            & stochrsi_turn_down
            & (dataframe["stochrsi_k"] > 60)
            & vol_ok
            & volume_ok
            & (dataframe["volume"] > 0)
        )

        dataframe.loc[long_cond & ~short_cond, ["enter_long", "enter_tag"]] = (1, "mr_long")
        dataframe.loc[short_cond & ~long_cond, ["enter_short", "enter_tag"]] = (1, "mr_short")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Deliberately empty - see class docstring. All exits are decided in
        # custom_stoploss/custom_exit so an entry and exit signal can never
        # land on the same candle and silently cancel each other out.
        return dataframe

    def leverage(
        self,
        pair: str,
        current_time,
        current_rate: float,
        proposed_leverage: float,
        max_leverage: float,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> float:
        return min(self.FIXED_LEVERAGE, max_leverage)

    def custom_stake_amount(
        self,
        pair: str,
        current_time,
        current_rate: float,
        proposed_stake: float,
        min_stake: float | None,
        max_stake: float,
        leverage: float,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> float:
        """Vol-targeted sizing: smaller stake when this pair is currently
        more volatile than its own recent average, larger when it's calmer -
        an approximation of "size to constant risk" rather than constant
        notional."""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe.empty:
            return proposed_stake

        last_candle = dataframe.iloc[-1]
        atr_pct = last_candle["atr_pct"]
        atr_pct_avg = last_candle["atr_pct_avg"]
        if not atr_pct or not atr_pct_avg or atr_pct_avg <= 0:
            return proposed_stake

        vol_ratio = atr_pct_avg / atr_pct
        scaled = proposed_stake * vol_ratio
        scaled = max(min(scaled, proposed_stake * self.MAX_SIZE_MULT), proposed_stake * self.MIN_SIZE_MULT)
        if min_stake:
            scaled = max(scaled, min_stake)
        return min(scaled, max_stake)

    def custom_stoploss(
        self,
        pair: str,
        trade: Trade,
        current_time,
        current_rate: float,
        current_profit: float,
        after_fill: bool,
        **kwargs,
    ) -> float | None:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe.empty:
            return self.stoploss

        last_candle = dataframe.iloc[-1]
        atr = last_candle["atr"]
        if atr <= 0 or trade.open_rate <= 0:
            return self.stoploss

        atr_stop_pct = -(self.stop_atr_mult.value * atr) / trade.open_rate
        atr_stop_pct = min(atr_stop_pct, -self.MIN_STOP_PCT)
        atr_stop_pct = max(atr_stop_pct, self.stoploss)
        if current_profit > self.breakeven_trigger.value:
            atr_stop_pct = max(atr_stop_pct, -0.001)
        return atr_stop_pct

    def custom_exit(
        self,
        pair: str,
        trade: Trade,
        current_time,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> str | bool | None:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe.empty:
            return None

        last_candle = dataframe.iloc[-1]

        # Bail before the hard stop if the 1h trend turns against the
        # position and isn't just a strong trend we'd rather not fade back
        # into (trend_extreme_1h already kept us out of new entries there).
        if trade.is_short and last_candle["regime_bull"] and not last_candle["trend_extreme_1h"]:
            return "regime_flip"
        if (not trade.is_short) and last_candle["regime_bear"] and not last_candle["trend_extreme_1h"]:
            return "regime_flip"

        minutes_open = (current_time - trade.open_date_utc).total_seconds() / 60
        candles_open = minutes_open / timeframe_to_minutes(self.timeframe)
        if candles_open > self.max_hold_candles.value and current_profit < 0.002:
            return "time_exit"

        return None

    def adjust_trade_position(
        self,
        trade: Trade,
        current_time,
        current_rate: float,
        current_profit: float,
        min_stake: float | None,
        max_stake: float,
        current_entry_rate: float,
        current_exit_rate: float,
        current_entry_profit: float,
        current_exit_profit: float,
        **kwargs,
    ) -> float | None | tuple[float | None, str | None]:
        dataframe, _ = self.dp.get_analyzed_dataframe(trade.pair, self.timeframe)
        if dataframe.empty:
            return None

        last_candle = dataframe.iloc[-1]
        atr = last_candle["atr"]
        if atr <= 0 or trade.open_rate <= 0:
            return None

        r_unit = atr / trade.open_rate

        # Partial scale-out at the first R-target: lock in profit on part of
        # the position while the setup is still live, let the rest ride on
        # the trailing stop. This is the "position isn't final, hedge when
        # odds shift" behaviour, done once per trade.
        if not trade.get_custom_data("partial_tp_done", False):
            if current_profit >= self.partial_tp_r_mult.value * r_unit:
                trade.set_custom_data("partial_tp_done", True)
                return -(trade.stake_amount * self.partial_tp_fraction.value), "partial_tp"

        # One bounded DCA re-entry, only if price has moved against the
        # trade AND the original thesis (oscillator side + regime) still
        # holds - never a blind average-down.
        if not trade.get_custom_data("dca_done", False):
            adverse = -current_profit
            if adverse >= self.dca_atr_mult.value * r_unit:
                thesis_holds = (
                    (not trade.is_short and not last_candle["regime_bear"] and last_candle["rsi"] < self.buy_rsi.value)
                    or (trade.is_short and not last_candle["regime_bull"] and last_candle["rsi"] > self.sell_rsi.value)
                )
                if thesis_holds:
                    trade.set_custom_data("dca_done", True)
                    return trade.stake_amount * self.dca_fraction.value, "dca_in"

        return None
