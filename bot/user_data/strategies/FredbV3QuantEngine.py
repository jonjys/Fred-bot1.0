"""FredbV3 quantitative engine with advisory higher-timeframe market bias."""
from __future__ import annotations

import logging

import pandas as pd

from FredbV3Strategy import FredbV3Strategy


logger = logging.getLogger(__name__)


class FredbV3QuantEngine(FredbV3Strategy):
    """Trade squeeze breakouts without treating market mode as a veto.

    The 15-minute EMA regime is useful context, but a hard regime filter can
    suppress every entry around turning points.  Breakouts aligned with the
    regime use the normal Donchian threshold; counter-regime breakouts remain
    eligible at half normal position size.
    """

    counter_bias_stake_multiplier = 0.5
    debug_entry_samples = 5

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        liquid_range = dataframe["atr_pct"].between(0.0005, 0.025)
        squeeze_now = dataframe["squeeze_std"] < (
            dataframe["squeeze_baseline"] * self.squeeze_thresh.value
        )
        # Keep the d2ae1e8 behaviour: the breakout follows a prior squeeze;
        # requiring the current candle to be squeezed would make it impossible.
        squeeze_recent = squeeze_now.shift(1).rolling(30).max().fillna(0).astype(bool)
        shared = (
            squeeze_recent
            & liquid_range
            & (dataframe["adx"] > self.adx_thresh.value)
            & (dataframe["adx_15m"] > 15)
            & (dataframe["rel_vol"] > 1.1)
            & (dataframe["volume"] > 0)
        )

        bullish_bias = (
            (dataframe["close_15m"] > dataframe["ema_fast_15m"])
            & (dataframe["ema_fast_15m"] > dataframe["ema_slow_15m"])
        )
        bearish_bias = (
            (dataframe["close_15m"] < dataframe["ema_fast_15m"])
            & (dataframe["ema_fast_15m"] < dataframe["ema_slow_15m"])
        )
        long_breakout = dataframe["close"] > dataframe["donchian_high"].shift(1)
        short_breakout = dataframe["close"] < dataframe["donchian_low"].shift(1)
        # Bias is advisory: counter-bias signals retain the original breakout
        # condition and are sized down in custom_stake_amount rather than
        # removed.  This preserves enough observations for the validation gate.
        long_signal = shared & long_breakout
        short_signal = shared & short_breakout
        counter_long = long_signal & ~bullish_bias
        counter_short = short_signal & ~bearish_bias

        dataframe.loc[long_signal, ["enter_long", "enter_tag"]] = (1, "breakout_long_squeeze")
        dataframe.loc[short_signal, ["enter_short", "enter_tag"]] = (1, "breakout_short_squeeze")
        dataframe.loc[counter_long, "enter_tag"] = "breakout_long_squeeze_counter_bias"
        dataframe.loc[counter_short, "enter_tag"] = "breakout_short_squeeze_counter_bias"

        samples = dataframe.loc[long_signal | short_signal].head(self.debug_entry_samples)
        pair = metadata.get("pair", "unknown")
        for timestamp, row in samples.iterrows():
            side = "long" if bool(row.get("enter_long", 0)) else "short"
            bias = "bullish" if bullish_bias.loc[timestamp] else (
                "bearish" if bearish_bias.loc[timestamp] else "neutral"
            )
            opposed = (side == "long" and bias != "bullish") or (
                side == "short" and bias != "bearish"
            )
            logger.info(
                "V3 entry sample pair=%s time=%s side=%s bias=%s advisory_opposition=%s",
                pair, timestamp, side, bias, opposed,
            )
        return dataframe

    def custom_stake_amount(self, *args, **kwargs) -> float:
        stake = super().custom_stake_amount(*args, **kwargs)
        entry_tag = kwargs.get("entry_tag")
        if entry_tag is None and len(args) > 7:
            entry_tag = args[7]
        if entry_tag and entry_tag.endswith("_counter_bias"):
            return stake * self.counter_bias_stake_multiplier
        return stake
