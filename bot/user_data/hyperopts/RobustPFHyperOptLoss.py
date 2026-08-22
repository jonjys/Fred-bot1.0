from freqtrade.data.metrics import calculate_max_drawdown
from freqtrade.optimize.hyperopt import IHyperOptLoss


class RobustPFHyperOptLoss(IHyperOptLoss):
    """
    Loss function for FredbV3: unlike ProfitFactorHyperOptLoss (V2, which
    optimizes profit factor with only a trade-count floor), this explicitly
    penalizes drawdown - the brief asked to prioritize robust PF and low DD
    over winrate, and a pure-PF loss will happily pick a high-PF/high-DD
    epoch since PF alone is blind to drawdown shape.

    - Below MIN_TRADES, reject outright (same reasoning as V2's loss: a
      "high PF" on a handful of trades is noise, not edge).
    - Above the floor: score = profit_factor - drawdown_penalty + small
      total-return term (return term is a tie-breaker between similar-PF
      epochs, not the primary objective - kept an order of magnitude
      smaller than the PF/DD terms on purpose).
    - drawdown_penalty is zero up to 4% max drawdown, then ramps up -
      this lets hyperopt use the DD headroom up to the 8% target instead
      of over-penalizing every epoch that isn't literally DD-free, while
      still making anything past ~8% a large negative.
    """

    MIN_TRADES = 60
    DD_FREE_PCT = 4.0
    DD_PENALTY_WEIGHT = 0.35

    @staticmethod
    def hyperopt_loss_function(
        results, trade_count, min_date, max_date, starting_balance, *args, **kwargs
    ) -> float:
        if trade_count < RobustPFHyperOptLoss.MIN_TRADES:
            return 100.0 + (RobustPFHyperOptLoss.MIN_TRADES - trade_count)

        profits = results["profit_abs"]
        gross_profit = profits[profits > 0].sum()
        gross_loss = -profits[profits < 0].sum()
        profit_factor = gross_profit / gross_loss if gross_loss != 0 else (gross_profit if gross_profit > 0 else 0)

        try:
            dd = calculate_max_drawdown(results, starting_balance=starting_balance, relative=True)
            max_dd_pct = dd.relative_account_drawdown * 100
        except ValueError:
            max_dd_pct = 0.0

        dd_penalty = max(0.0, max_dd_pct - RobustPFHyperOptLoss.DD_FREE_PCT) * RobustPFHyperOptLoss.DD_PENALTY_WEIGHT
        total_return_pct = (profits.sum() / starting_balance * 100) if starting_balance else 0.0

        score = profit_factor - dd_penalty + 0.05 * total_return_pct
        return -score
