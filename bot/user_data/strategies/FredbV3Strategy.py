"""FredbV3: OKX USDT perpetual Donchian squeeze breakout."""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import talib.abstract as ta
from freqtrade.persistence import Trade
from freqtrade.strategy import DecimalParameter, IStrategy, IntParameter, informative, stoploss_from_absolute


class FredbV3Strategy(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1m"
    can_short = True
    process_only_new_candles = True
    startup_candle_count = 1000
    use_custom_stoploss = True
    position_adjustment_enable = True
    max_entry_position_adjustment = 2
    minimal_roi = {"0": 0.15}
    stoploss = -0.08

    order_types = {
        "entry": "limit",
        "exit": "limit",
        "emergency_exit": "market",
        "force_entry": "market",
        "force_exit": "market",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    donchian_period = IntParameter(20, 60, default=30, space="buy", optimize=False)
    squeeze_period = IntParameter(20, 100, default=50, space="buy", optimize=False)
    squeeze_thresh = DecimalParameter(0.1, 0.6, default=0.25, space="buy", optimize=False)
    adx_thresh = IntParameter(15, 30, default=20, space="buy", optimize=False)
    atr_trail = DecimalParameter(2.0, 4.5, default=3.0, space="sell", optimize=False)

    @informative("15m")
    def populate_indicators_15m(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        return dataframe

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        period = self.donchian_period.value
        dataframe["donchian_high"] = dataframe["high"].rolling(period).max()
        dataframe["donchian_low"] = dataframe["low"].rolling(period).min()
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["squeeze_std"] = dataframe["close"].rolling(self.squeeze_period.value).std()
        dataframe["squeeze_baseline"] = dataframe["squeeze_std"].rolling(20).mean()
        dataframe["rel_vol"] = dataframe["volume"] / dataframe["volume"].rolling(50).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        liquid_range = dataframe["atr_pct"].between(0.0005, 0.025)
        squeeze_now = dataframe["squeeze_std"] < (
            dataframe["squeeze_baseline"] * self.squeeze_thresh.value
        )
        squeeze_recent = squeeze_now.shift(1).rolling(30).max().fillna(0).astype(bool)
        shared = (
            squeeze_recent
            & liquid_range
            & (dataframe["adx"] > self.adx_thresh.value)
            & (dataframe["adx_15m"] > 15)
            & (dataframe["rel_vol"] > 1.1)
            & (dataframe["volume"] > 0)
        )
        long_signal = (
            shared
            & (dataframe["close"] > dataframe["donchian_high"].shift(1))
            & (dataframe["close_15m"] > dataframe["ema_fast_15m"])
            & (dataframe["ema_fast_15m"] > dataframe["ema_slow_15m"])
        )
        short_signal = (
            shared
            & (dataframe["close"] < dataframe["donchian_low"].shift(1))
            & (dataframe["close_15m"] < dataframe["ema_fast_15m"])
            & (dataframe["ema_fast_15m"] < dataframe["ema_slow_15m"])
        )
        dataframe.loc[long_signal, ["enter_long", "enter_tag"]] = (1, "breakout_long_squeeze")
        dataframe.loc[short_signal, ["enter_short", "enter_tag"]] = (1, "breakout_short_squeeze")
        return dataframe

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe

    def leverage(
        self, pair: str, current_time: datetime, current_rate: float,
        proposed_leverage: float, max_leverage: float, entry_tag: str | None,
        side: str, **kwargs,
    ) -> float:
        return min(2.0, max_leverage)

    def custom_stake_amount(
        self, pair: str, current_time: datetime, current_rate: float,
        proposed_stake: float, min_stake: float | None, max_stake: float,
        leverage: float, entry_tag: str | None, side: str, **kwargs,
    ) -> float:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair=pair, timeframe=self.timeframe)
        if dataframe.empty:
            return 0.0
        atr = float(dataframe.iloc[-1]["atr"])
        if not atr or pd.isna(atr):
            return 0.0
        equity = float(self.wallets.get_total_stake_amount())
        risk_budget = equity * 0.0035
        stop_ratio = max((atr * float(self.atr_trail.value)) / current_rate, 0.005)
        stake = risk_budget / (max(leverage, 1.0) * stop_ratio)
        lower = float(min_stake or 0.0)
        return max(lower, min(stake, max_stake, proposed_stake))

    def adjust_trade_position(
        self, trade: Trade, current_time: datetime, current_rate: float,
        current_profit: float, min_stake: float | None, max_stake: float,
        current_entry_rate: float, current_exit_rate: float,
        current_entry_profit: float, current_exit_profit: float, **kwargs,
    ) -> float | None | tuple[float | None, str | None]:
        if trade.has_open_orders:
            return None
        if current_profit >= 0.07 and trade.nr_of_successful_exits == 1:
            return -(trade.stake_amount * 0.5), "partial_profit_2"
        if current_profit >= 0.04 and trade.nr_of_successful_exits == 0:
            return -(trade.stake_amount * 0.5), "partial_profit_1"
        if current_profit <= 0:
            return None
        if current_profit >= 0.015 and trade.nr_of_successful_entries < 3:
            initial_stake = trade.stake_amount / trade.nr_of_successful_entries
            addition = min(initial_stake * 0.5, max_stake)
            if min_stake is not None and addition < min_stake:
                return None
            return addition, "winner_only_pyramid"
        return None

    def custom_stoploss(
        self, pair: str, trade: Trade, current_time: datetime,
        current_rate: float, current_profit: float, **kwargs,
    ) -> float:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair=pair, timeframe=self.timeframe)
        if dataframe.empty:
            return self.stoploss
        atr = float(dataframe.iloc[-1]["atr"])
        if not atr or pd.isna(atr):
            return self.stoploss
        distance = atr * float(self.atr_trail.value)
        stop_rate = current_rate + distance if trade.is_short else current_rate - distance
        if current_profit >= 0.03:
            locked_rate = trade.open_rate * (0.995 if trade.is_short else 1.005)
            stop_rate = min(stop_rate, locked_rate) if trade.is_short else max(stop_rate, locked_rate)
        return stoploss_from_absolute(
            stop_rate=stop_rate,
            current_rate=current_rate,
            is_short=trade.is_short,
            leverage=trade.leverage,
        )
