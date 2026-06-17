"""Module 3 — Portfolio construction.

Define a target allocation, simulate investing a lump sum, and track
portfolio value over time. See SPEC.md for the full module specification.
"""

from __future__ import annotations

import pandas as pd


def validate_weights(weights: dict) -> None:
    """Assert weights sum to 1.0 (within tolerance) and tickers exist."""
    raise NotImplementedError


def build_portfolio(prices: pd.DataFrame, weights: dict, initial_investment: float) -> pd.DataFrame:
    """Allocate the initial investment by weight and track each asset's value.

    Returns a DataFrame with one column per ticker plus a "total" column.
    """
    raise NotImplementedError


def portfolio_returns(portfolio_df: pd.DataFrame) -> pd.Series:
    """Daily returns on the total portfolio value."""
    raise NotImplementedError


def max_drawdown(portfolio_series: pd.Series) -> float:
    """Peak-to-trough maximum drawdown."""
    raise NotImplementedError
