"""Module 2 — Return calculations.

Compute daily, cumulative, and annualized returns from price data.
See SPEC.md for the full module specification.
"""

from __future__ import annotations

import pandas as pd


def daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Simple percentage returns: (P_t - P_{t-1}) / P_{t-1}."""
    raise NotImplementedError


def log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Log returns: ln(P_t / P_{t-1})."""
    raise NotImplementedError


def cumulative_returns(daily_ret: pd.DataFrame) -> pd.DataFrame:
    """Cumulative returns: (1 + daily_ret).cumprod() - 1."""
    raise NotImplementedError


def annualized_return(daily_ret: pd.DataFrame, periods_per_year: int = 252) -> pd.Series:
    """Geometric annualized return."""
    raise NotImplementedError


def rolling_return(daily_ret: pd.DataFrame, window: int = 252) -> pd.DataFrame:
    """Rolling 1-year return window."""
    raise NotImplementedError
