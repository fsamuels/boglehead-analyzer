"""Module 2 — Return calculations.

Compute daily, cumulative, annualized, and rolling returns from price data.
See SPEC.md for the full module specification.

Notebook companion: ``notebooks/02_returns.ipynb``.

The input everywhere is a price frame as produced by Module 1
(``analysis/fetch.py``): a ``DatetimeIndex`` with one adjusted-close column per
ticker. Tickers with a shorter history carry leading ``NaN`` values; the
functions here preserve that (pandas skips ``NaN`` per column) so a newer ETF
never contaminates an older one's numbers.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Simple percentage returns: ``(P_t - P_{t-1}) / P_{t-1}``.

    ``pandas.DataFrame.pct_change`` is the idiomatic one-liner. The manual
    NumPy equivalent it stands in for is::

        values = prices.to_numpy()
        (values[1:] - values[:-1]) / values[:-1]

    The first row of every column is ``NaN`` (no prior price to compare to), so
    we drop the rows that are ``NaN`` for *all* tickers. Partial ``NaN`` rows —
    a newer ETF that hasn't started yet — are kept and handled per column.
    """
    returns = prices.pct_change()
    return returns.dropna(how="all")


def log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Log returns: ``ln(P_t / P_{t-1})``.

    Log (continuously compounded) returns are convenient because they are
    *additive over time*: the log return of a multi-day period is simply the
    sum of the daily log returns, whereas simple returns must be chained
    multiplicatively. That makes aggregation, and many statistical operations,
    cleaner. For small daily moves they are numerically very close to simple
    returns; the gap widens as moves get larger.
    """
    ratios = prices / prices.shift(1)
    return np.log(ratios).dropna(how="all")


def cumulative_returns(daily_ret: pd.DataFrame) -> pd.DataFrame:
    """Cumulative growth of $1 expressed as a return: ``(1 + r).cumprod() - 1``.

    The value at time ``t`` is the total return earned from the start of the
    series through ``t`` — e.g. ``0.25`` means up 25% cumulatively.
    """
    return (1 + daily_ret).cumprod() - 1


def annualized_return(daily_ret: pd.DataFrame, periods_per_year: int = 252) -> pd.Series:
    """Geometric (CAGR-style) annualized return, one value per ticker.

    Compounds every daily return into a total growth factor, then rescales it
    to a per-year rate::

        (1 + total_return) ** (periods_per_year / n_days) - 1

    ``periods_per_year`` defaults to 252, the typical count of US trading days
    in a year. ``n_days`` is counted per column (``NaN`` returns excluded), so a
    ticker with less history is still annualized over its own lifespan.
    """
    growth_factor = (1 + daily_ret).prod()   # total growth per column; NaNs skipped
    n_days = daily_ret.count()               # number of return observations per column
    return growth_factor ** (periods_per_year / n_days) - 1


def rolling_return(daily_ret: pd.DataFrame, window: int = 252) -> pd.DataFrame:
    """Trailing total return over a moving ``window`` of trading days.

    With the default 252-day window this is the rolling 1-year return — useful
    for seeing how performance varied across time rather than as a single
    summary number.

    Implemented vectorized via a running compound: the product of the last
    ``window`` daily factors equals ``cumprod[t] / cumprod[t - window]``. The
    first ``window`` rows have no full window behind them and are ``NaN``.
    """
    compounded = (1 + daily_ret).cumprod()
    return compounded / compounded.shift(window) - 1
