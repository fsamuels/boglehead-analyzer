"""Module 5 — Cost drag analysis.

Show the compounding impact of expense ratios over time.
See SPEC.md for the full module specification.
"""

from __future__ import annotations

import pandas as pd


def apply_expense_ratio(portfolio_series: pd.Series, expense_ratio_annual: float) -> pd.Series:
    """Deduct the expense ratio daily: (1 - expense_ratio / 252) per day."""
    raise NotImplementedError


def cost_drag_over_time(
    initial_investment: float,
    annual_return: float,
    years: int,
    expense_ratios: list[float],
) -> pd.DataFrame:
    """Pure-math projection of terminal value per expense ratio.

    Returns a DataFrame: rows = years, columns = expense ratios.
    """
    raise NotImplementedError


def compare_funds(portfolio_series: pd.Series, expense_ratios_dict: dict) -> pd.DataFrame:
    """Apply different expense ratios to a portfolio return stream."""
    raise NotImplementedError
