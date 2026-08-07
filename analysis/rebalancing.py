"""Module 4 — Rebalancing simulator.

Simulate and compare rebalancing strategies to quantify the behavioral and
return impact of discipline vs drift. See SPEC.md for the full module
specification.

Notebook companion: ``notebooks/04_rebalancing.ipynb``.

The input everywhere is a price frame as produced by Module 1
(``analysis/fetch.py``): a ``DatetimeIndex`` with one adjusted-close column per
ticker.
"""

from __future__ import annotations

import pandas as pd

from analysis.portfolio import validate_weights

STRATEGIES = ("none", "annual", "threshold")


def simulate(
    prices: pd.DataFrame,
    weights: dict,
    initial_investment: float,
    strategy: str,
    threshold: float = 0.05,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run one rebalancing strategy over the full price history.

    Starts from the same lump-sum allocation as ``portfolio.build_portfolio``
    (dollar allocation by weight, converted to a share count at the first
    available price), then walks the price history day by day. On any day
    that triggers a rebalance, shares are resized back to the target dollar
    weights at that day's prices, and the buy/sell amounts are logged.

    Days where any tracked ticker's price is missing (a newer ETF that
    hasn't started trading yet) are never rebalanced, since drifted target
    weights aren't well-defined without a complete price row.

    Args:
        prices: Adjusted close prices, one column per ticker.
        weights: Target allocation, e.g. ``{"VTI": 0.6, "BND": 0.4}``.
        initial_investment: Starting dollar amount.
        strategy: One of ``"none"``, ``"annual"``, ``"threshold"``.
        threshold: Drift tolerance for the ``"threshold"`` strategy.

    Returns:
        ``(portfolio_values, rebalance_log)`` — ``portfolio_values`` has one
        column per ticker plus ``"total"``; ``rebalance_log`` has columns
        ``date``, ``asset``, ``action`` (``"buy"``/``"sell"``), ``amount``.
    """
    if strategy not in STRATEGIES:
        raise ValueError(f"strategy must be one of {STRATEGIES}, got {strategy!r}")

    validate_weights(weights)
    tickers = list(weights.keys())
    missing = [t for t in tickers if t not in prices.columns]
    if missing:
        raise ValueError(f"weights reference tickers not in prices: {missing}")

    asset_prices = prices[tickers]
    target_weights = pd.Series(weights)[tickers]

    first_prices = asset_prices.bfill().iloc[0]
    shares = (target_weights * initial_investment) / first_prices

    value_rows = []
    rebalance_events = []
    prev_year = None

    for current_date, price_row in asset_prices.iterrows():
        current_values = shares * price_row
        total = current_values.sum(skipna=True)
        complete_row = not price_row.isna().any()

        do_rebalance = False
        if complete_row:
            if strategy == "annual":
                do_rebalance = prev_year is not None and current_date.year != prev_year
            elif strategy == "threshold":
                current_weights = current_values / total
                do_rebalance = _needs_rebalance_threshold(current_weights, target_weights, threshold)

        if do_rebalance:
            target_values = target_weights * total
            diff = target_values - current_values
            for ticker in tickers:
                amount = diff[ticker]
                if abs(amount) > 1e-9:
                    rebalance_events.append(
                        {
                            "date": current_date,
                            "asset": ticker,
                            "action": "buy" if amount > 0 else "sell",
                            "amount": abs(amount),
                        }
                    )
            shares = target_values / price_row
            current_values = shares * price_row
            total = current_values.sum(skipna=True)

        row = current_values.copy()
        row["total"] = total
        row.name = current_date
        value_rows.append(row)
        prev_year = current_date.year

    portfolio_values = pd.DataFrame(value_rows)
    portfolio_values.index.name = "Date"
    rebalance_log = pd.DataFrame(rebalance_events, columns=["date", "asset", "action", "amount"])
    return portfolio_values, rebalance_log


def _needs_rebalance_threshold(current_weights: pd.Series, target_weights: pd.Series, threshold: float) -> bool:
    """Return True if any asset's current weight deviates from target by more than ``threshold``."""
    deviation = (current_weights - target_weights).abs()
    return bool((deviation > threshold).any())


def compare_strategies(prices: pd.DataFrame, weights: dict, initial_investment: float) -> pd.DataFrame:
    """Run all three strategies and return their total portfolio values side by side.

    Returns a ``DataFrame`` indexed by date with one column per strategy:
    ``"none"``, ``"annual"``, ``"threshold"``.
    """
    totals = {}
    for strategy in STRATEGIES:
        values, _ = simulate(prices, weights, initial_investment, strategy)
        totals[strategy] = values["total"]
    return pd.DataFrame(totals)
