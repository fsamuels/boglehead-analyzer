"""Module 5 — Cost drag analysis.

Show the compounding impact of expense ratios over time — the core Boglehead
argument that costs compound just like returns do, but against you. See
SPEC.md for the full module specification.

Notebook companion: ``notebooks/05_cost_drag.ipynb``.
"""

from __future__ import annotations

import pandas as pd

_TRADING_DAYS_PER_YEAR = 252


def apply_expense_ratio(portfolio_series: pd.Series, expense_ratio_annual: float) -> pd.Series:
    """Deduct an annual expense ratio from a portfolio value series, applied daily.

    The ratio is spread evenly across trading days — each day's growth factor
    is multiplied by ``(1 - expense_ratio_annual / 252)`` on top of that day's
    actual price return, then compounded forward from the series' starting
    value. The first observation is left untouched (no time has elapsed yet
    to accrue a cost against).
    """
    daily_drag = 1 - expense_ratio_annual / _TRADING_DAYS_PER_YEAR
    gross_growth = 1 + portfolio_series.pct_change()  # NaN on the first day
    net_growth = gross_growth * daily_drag
    net_growth.iloc[0] = 1.0  # no drag before any time has passed

    adjusted = portfolio_series.iloc[0] * net_growth.cumprod()
    adjusted.name = portfolio_series.name
    return adjusted


def cost_drag_over_time(
    initial_investment: float,
    annual_return: float,
    years: int,
    expense_ratios: list[float],
) -> pd.DataFrame:
    """Pure-math projection of terminal value per expense ratio (no price data needed).

    Each expense ratio compounds against the same assumed ``annual_return``:
    ``initial_investment * ((1 + annual_return) * (1 - expense_ratio)) ** year``.

    Returns a ``DataFrame`` indexed by year (0 through ``years`` inclusive, so
    year 0 is ``initial_investment`` for every column) with one column per
    entry in ``expense_ratios``.
    """
    year_index = pd.RangeIndex(years + 1, name="year")
    columns = {}
    for expense_ratio in expense_ratios:
        net_annual_factor = (1 + annual_return) * (1 - expense_ratio)
        columns[expense_ratio] = initial_investment * net_annual_factor ** year_index.to_numpy()
    return pd.DataFrame(columns, index=year_index)


def compare_funds(portfolio_series: pd.Series, expense_ratios_dict: dict) -> pd.DataFrame:
    """Apply different expense ratios to the same portfolio return stream.

    ``expense_ratios_dict`` maps a scenario label (e.g. a fund name) to its
    annual expense ratio. Returns a ``DataFrame`` with one column per label,
    each holding that scenario's cost-adjusted value series.
    """
    return pd.DataFrame(
        {label: apply_expense_ratio(portfolio_series, ratio) for label, ratio in expense_ratios_dict.items()}
    )
