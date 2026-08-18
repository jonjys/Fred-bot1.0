from datetime import datetime

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

    minimal_roi = {"0": 0.231, "81": 0.125, "183": 0.045, "519": 0}
    stoploss = -0.246  # hard safety net; real exits happen via custom_stoploss
    use_custom_stoploss = True

    trailing_stop = True
    trailing_stop_positive = 0.32
    trailing_stop_positive_offset = 0.381
    trailing_only_offset_is_reached = False

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

        # Never risk more than the hard safety-net stoploss, and once in
        # profit, don't let the stop go looser than break-even.
        atr_stop_pct = max(atr_stop_pct, self.stoploss)
        if current_profit > 0.02:
            atr_stop_pct = max(atr_stop_pct, -0.002)

        return atr_stop_pct
