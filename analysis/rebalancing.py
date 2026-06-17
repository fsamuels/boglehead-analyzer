"""Module 4 — Rebalancing simulator.

Simulate and compare rebalancing strategies ("none", "annual", "threshold").
See SPEC.md for the full module specification.
"""

from __future__ import annotations

import pandas as pd


def simulate(
    prices: pd.DataFrame,
    weights: dict,
    initial_investment: float,
    strategy: str,
    threshold: float = 0.05,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Core simulation loop.

    Returns ``(portfolio_values, rebalance_log)``.
    """
    raise NotImplementedError


def _needs_rebalance_threshold(current_weights: dict, target_weights: dict, threshold: float) -> bool:
    """Return True if any asset deviates by more than ``threshold``."""
    raise NotImplementedError


def compare_strategies(prices: pd.DataFrame, weights: dict, initial_investment: float) -> pd.DataFrame:
    """Run all three strategies and return a combined portfolio-value DataFrame.

    Columns: "none", "annual", "threshold".
    """
    raise NotImplementedError
