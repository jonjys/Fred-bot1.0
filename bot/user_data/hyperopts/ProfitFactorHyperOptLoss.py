from pandas import DataFrame

from freqtrade.optimize.hyperopt_loss.hyperopt_loss_interface import IHyperOptLoss


class ProfitFactorHyperOptLoss(IHyperOptLoss):
    """
    Optimizes primarily for profit factor (gross profit / gross loss), since
    that's the metric this project targets (PF > 1.5), with a small total
    return term so hyperopt doesn't prefer a high-PF result built on very
    few, barely-profitable trades over one with similar PF and real return.
    Requires a minimum trade count so it can't "win" with a couple of lucky
    trades.
    """

    MIN_TRADES = 20

    @staticmethod
    def hyperopt_loss_function(
        results: DataFrame, trade_count: int, min_date, max_date, *args, **kwargs
    ) -> float:
        if trade_count < ProfitFactorHyperOptLoss.MIN_TRADES:
            return 100.0 + (ProfitFactorHyperOptLoss.MIN_TRADES - trade_count)

        profits = results["profit_abs"]
        gross_profit = profits[profits > 0].sum()
        gross_loss = -profits[profits < 0].sum()

        if gross_loss == 0:
            profit_factor = gross_profit if gross_profit > 0 else 0
        else:
            profit_factor = gross_profit / gross_loss

        total_return_pct = results["profit_abs"].sum() / 1000.0  # vs. dry_run_wallet

        # Lower is better for hyperopt: minimize negative (PF + small return bonus).
        return -(profit_factor + 2.0 * total_return_pct)
