"""Module 1 — Data ingestion.

Pull and cache historical adjusted close prices for a configurable list of ETFs.
See SPEC.md for the full module specification.

Notebook companion: ``notebooks/01_data_ingestion.ipynb``.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

# Cached CSVs live here, one file per ticker (git-ignored — see .gitignore).
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def _today_iso() -> str:
    """Return today's date as an ISO string (the default ``end``)."""
    return date.today().isoformat()


def _normalize_download(raw: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    """Reduce a raw ``yfinance.download`` frame to one adjusted-close column per ticker.

    ``yfinance`` returns different shapes depending on how many tickers were
    requested and whether ``group_by`` is set:

    - single ticker  -> flat columns ("Open", "High", "Close", ...)
    - many tickers    -> a column MultiIndex of (field, ticker)

    We request ``auto_adjust=True`` so the "Close" column is already the
    *adjusted* close (splits and dividends folded in), which is what every
    downstream return calculation should use.
    """
    if isinstance(raw.columns, pd.MultiIndex):
        # MultiIndex is (field, ticker); slice out the adjusted close field.
        prices = raw["Close"].copy()
    else:
        # Single ticker: pull the Close series and label it with the ticker.
        prices = raw[["Close"]].copy()
        prices.columns = [tickers[0]]

    # Keep a stable, requested column order (yfinance may reorder alphabetically).
    present = [t for t in tickers if t in prices.columns]
    return prices[present]


def fetch_prices(tickers: list[str], start: str, end: str | None = None) -> pd.DataFrame:
    """Download adjusted close prices via yfinance.

    Drops rows where all values are NaN and returns a DataFrame with a
    ``DatetimeIndex`` and one column per ticker, aligned on a shared date index.

    Args:
        tickers: ETF symbols, e.g. ``["VTI", "VXUS", "BND"]``.
        start: ISO start date, e.g. ``"2013-01-01"``.
        end: ISO end date; defaults to today.

    Returns:
        ``pd.DataFrame`` of adjusted close prices indexed by date.
    """
    if not tickers:
        raise ValueError("`tickers` must contain at least one symbol.")

    end = end or _today_iso()

    raw = yf.download(
        tickers,
        start=start,
        end=end,
        auto_adjust=True,   # "Close" becomes the adjusted close.
        progress=False,
        group_by="column",  # predictable (field, ticker) MultiIndex for >1 ticker.
    )

    if raw.empty:
        # No data at all (bad tickers / range). Return an empty, well-shaped frame.
        return pd.DataFrame(columns=tickers)

    prices = _normalize_download(raw, tickers)

    # A row that is NaN for *every* ticker carries no information — drop it.
    # Rows where only some tickers are NaN (e.g. a newer ETF with less history)
    # are kept; downstream modules decide how to align them.
    prices = prices.dropna(how="all").sort_index()
    prices.index.name = "Date"
    return prices


def _cache_path(ticker: str) -> Path:
    return DATA_DIR / f"{ticker}.csv"


def _last_cached_date(path: Path) -> pd.Timestamp | None:
    """Return the most recent date in a cached CSV, or ``None`` if unreadable."""
    try:
        cached = pd.read_csv(path, index_col=0, parse_dates=True)
    except (FileNotFoundError, ValueError, pd.errors.EmptyDataError):
        return None
    if cached.empty:
        return None
    return cached.index.max()


def _write_cache(prices: pd.DataFrame) -> None:
    """Write one CSV per ticker into ``data/raw/``."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for ticker in prices.columns:
        prices[[ticker]].dropna().to_csv(_cache_path(ticker))


def load_or_fetch(tickers: list[str], start: str, end: str | None = None) -> pd.DataFrame:
    """Load cached CSVs from ``data/raw/`` if fresh, otherwise fetch and cache.

    The cache is considered *stale* if any ticker is missing a CSV, or if the
    requested ``end`` date is later than that ticker's last cached date. On a
    miss we re-fetch every ticker (so the returned frame stays aligned) and
    rewrite the cache.

    Args:
        tickers: ETF symbols.
        start: ISO start date.
        end: ISO end date; defaults to today.

    Returns:
        ``pd.DataFrame`` of adjusted close prices indexed by date.
    """
    if not tickers:
        raise ValueError("`tickers` must contain at least one symbol.")

    end = end or _today_iso()
    requested_end = pd.Timestamp(end)

    # yfinance treats ``end`` as *exclusive*, and markets are closed on
    # weekends — so the newest data we could possibly have is the last business
    # day strictly before ``end``. Comparing against that (rather than ``end``
    # itself) keeps the cache usable instead of perpetually "stale". (Market
    # holidays aren't modelled here; at worst they trigger a harmless refetch.)
    last_expected = requested_end - pd.offsets.BDay(1)

    fresh = True
    for ticker in tickers:
        last = _last_cached_date(_cache_path(ticker))
        # Missing cache, or it stops before the data we now expect -> stale.
        if last is None or last < last_expected:
            fresh = False
            break

    if not fresh:
        prices = fetch_prices(tickers, start, end)
        _write_cache(prices)
        return prices

    # Cache hit: stitch the per-ticker CSVs back into one aligned frame.
    frames = []
    for ticker in tickers:
        series = pd.read_csv(_cache_path(ticker), index_col=0, parse_dates=True)[ticker]
        frames.append(series)
    prices = pd.concat(frames, axis=1)

    # Respect the requested window when serving from cache.
    prices = prices.loc[(prices.index >= pd.Timestamp(start)) & (prices.index < requested_end)]
    prices = prices.dropna(how="all").sort_index()
    prices.index.name = "Date"
    return prices
