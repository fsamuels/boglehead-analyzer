"""Module 1 — Data ingestion.

Pull and cache historical adjusted close prices for a configurable list of ETFs.
See SPEC.md for the full module specification.
"""

from __future__ import annotations

import pandas as pd


def fetch_prices(tickers: list[str], start: str, end: str | None = None) -> pd.DataFrame:
    """Download adjusted close prices via yfinance.

    Drops rows where all values are NaN and returns an aligned DataFrame
    (inner join on dates).
    """
    raise NotImplementedError


def load_or_fetch(tickers: list[str], start: str, end: str | None = None) -> pd.DataFrame:
    """Load cached CSVs from ``data/raw/`` if fresh, otherwise fetch.

    Cache is considered stale if the requested end date is later than the
    last cached date.
    """
    raise NotImplementedError
