"""Immutable production facade. Experiments optimize FredbV2Strategy only."""
from FredbV2Strategy import FredbV2Strategy


class FredbV2ProdStrategy(FredbV2Strategy):
    """PROD LOCK v1; parameters load from FredbV2ProdStrategy.json."""

    pass
