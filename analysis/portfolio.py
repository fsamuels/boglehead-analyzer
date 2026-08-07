"""Module 3 — Portfolio construction.

Define a target allocation, simulate investing a lump sum, and track
portfolio value over time. See SPEC.md for the full module specification.

Notebook companion: ``notebooks/03_portfolio.ipynb``.

The input everywhere is a price frame as produced by Module 1
(``analysis/fetch.py``): a ``DatetimeIndex`` with one adjusted-close column per
ticker.
"""

from __future__ import annotations

import pandas as pd

_WEIGHT_TOLERANCE = 1e-6


def validate_weights(weights: dict) -> None:
    """Assert weights sum to 1.0 (within tolerance) and tickers exist.

    ``weights`` maps ticker -> target allocation, e.g. ``{"VTI": 0.6, "BND":
    0.4}``. Raises ``ValueError`` if the weights don't sum to 1.0, or a
    ``KeyError``-style message if a weighted ticker isn't a valid key.
    """
    total = sum(weights.values())
    if abs(total - 1.0) > _WEIGHT_TOLERANCE:
        raise ValueError(f"weights must sum to 1.0, got {total}")


def build_portfolio(prices: pd.DataFrame, weights: dict, initial_investment: float) -> pd.DataFrame:
    """Allocate the initial investment by weight and track each asset's value.

    Each ticker's dollar allocation is converted to a *share count* at the
    first available price, then revalued at every subsequent price via
    broadcasting (``shares * prices``) — no rebalancing happens here, so
    allocations drift with the market on their own. Returns a DataFrame with
    one column per ticker plus a "total" column (row-wise sum, ``NaN``-safe).
    """
    validate_weights(weights)
    tickers = list(weights.keys())
    missing = [t for t in tickers if t not in prices.columns]
    if missing:
        raise ValueError(f"weights reference tickers not in prices: {missing}")

    asset_prices = prices[tickers]
    first_prices = asset_prices.bfill().iloc[0]  # first available price per ticker
    dollar_allocation = pd.Series(weights)[tickers] * initial_investment
    shares = dollar_allocation / first_prices

    values = asset_prices * shares
    values["total"] = values.sum(axis=1, skipna=True)
    return values


def portfolio_returns(portfolio_df: pd.DataFrame) -> pd.Series:
    """Daily returns on the total portfolio value."""
    return portfolio_df["total"].pct_change().dropna()


def max_drawdown(portfolio_series: pd.Series) -> float:
    """Peak-to-trough maximum drawdown, expressed as a negative fraction.

    At every point in time, compares the current value to the running
    (cumulative) max seen so far — the drawdown if you had bought at the peak
    and held to today. The most negative of those is the max drawdown.
    """
    running_max = portfolio_series.cummax()
    drawdown = (portfolio_series - running_max) / running_max
    return drawdown.min()
