"""Unit tests for Module 1 — data ingestion (``analysis/fetch.py``).

These tests stub out ``yfinance`` so the suite runs offline and
deterministically. No network calls are made.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from analysis import fetch


def _multiindex_download(tickers, dates, closes):
    """Build a frame shaped like ``yf.download`` for multiple tickers.

    Columns are a (field, ticker) MultiIndex, matching ``group_by="column"``.
    """
    fields = ["Open", "High", "Low", "Close", "Volume"]
    cols = pd.MultiIndex.from_product([fields, tickers])
    frame = pd.DataFrame(index=pd.DatetimeIndex(dates, name="Date"), columns=cols, dtype=float)
    for ticker in tickers:
        frame[("Close", ticker)] = closes[ticker]
    return frame


def test_fetch_prices_multi_ticker(monkeypatch):
    tickers = ["VTI", "BND"]
    dates = pd.date_range("2020-01-01", periods=3, freq="D")
    closes = {"VTI": [100.0, 101.0, 102.0], "BND": [80.0, 80.5, 81.0]}

    monkeypatch.setattr(
        fetch.yf, "download",
        lambda *a, **k: _multiindex_download(tickers, dates, closes),
    )

    prices = fetch.fetch_prices(tickers, start="2020-01-01", end="2020-01-04")

    # One adjusted-close column per ticker, in requested order.
    assert list(prices.columns) == tickers
    assert prices.loc[dates[2], "VTI"] == 102.0
    assert prices.index.name == "Date"


def test_fetch_prices_single_ticker(monkeypatch):
    dates = pd.date_range("2020-01-01", periods=2, freq="D")
    flat = pd.DataFrame(
        {"Open": [1.0, 1.0], "Close": [100.0, 101.0], "Volume": [10, 11]},
        index=pd.DatetimeIndex(dates, name="Date"),
    )
    monkeypatch.setattr(fetch.yf, "download", lambda *a, **k: flat)

    prices = fetch.fetch_prices(["VTI"], start="2020-01-01")

    assert list(prices.columns) == ["VTI"]
    assert prices["VTI"].tolist() == [100.0, 101.0]


def test_fetch_prices_drops_all_nan_rows(monkeypatch):
    tickers = ["VTI", "BND"]
    dates = pd.date_range("2020-01-01", periods=3, freq="D")
    # Middle row is NaN for both tickers (e.g. a market holiday).
    closes = {"VTI": [100.0, np.nan, 102.0], "BND": [80.0, np.nan, 81.0]}
    monkeypatch.setattr(
        fetch.yf, "download",
        lambda *a, **k: _multiindex_download(tickers, dates, closes),
    )

    prices = fetch.fetch_prices(tickers, start="2020-01-01")

    assert len(prices) == 2  # the all-NaN row is gone
    assert dates[1] not in prices.index


def test_fetch_prices_keeps_partial_nan_rows(monkeypatch):
    """A newer ETF with less history (some NaN) should not drop shared rows."""
    tickers = ["VTI", "NEW"]
    dates = pd.date_range("2020-01-01", periods=2, freq="D")
    closes = {"VTI": [100.0, 101.0], "NEW": [np.nan, 50.0]}
    monkeypatch.setattr(
        fetch.yf, "download",
        lambda *a, **k: _multiindex_download(tickers, dates, closes),
    )

    prices = fetch.fetch_prices(tickers, start="2020-01-01")

    assert len(prices) == 2
    assert np.isnan(prices.loc[dates[0], "NEW"])


def test_fetch_prices_requires_tickers():
    with pytest.raises(ValueError):
        fetch.fetch_prices([], start="2020-01-01")


def test_load_or_fetch_caches_then_reuses(monkeypatch, tmp_path):
    tickers = ["VTI", "BND"]
    dates = pd.date_range("2020-01-01", periods=3, freq="D")
    sample = pd.DataFrame(
        {"VTI": [100.0, 101.0, 102.0], "BND": [80.0, 80.5, 81.0]},
        index=pd.DatetimeIndex(dates, name="Date"),
    )

    # Redirect the cache directory into a temp folder.
    monkeypatch.setattr(fetch, "DATA_DIR", tmp_path)

    calls = {"n": 0}

    def fake_fetch(_tickers, _start, _end=None):
        calls["n"] += 1
        return sample

    monkeypatch.setattr(fetch, "fetch_prices", fake_fetch)

    # First call: cache miss -> fetches and writes CSVs.
    first = fetch.load_or_fetch(tickers, start="2020-01-01", end="2020-01-04")
    assert calls["n"] == 1
    assert (tmp_path / "VTI.csv").exists()
    assert (tmp_path / "BND.csv").exists()

    # Second call with same window: cache hit -> no new fetch.
    second = fetch.load_or_fetch(tickers, start="2020-01-01", end="2020-01-04")
    assert calls["n"] == 1
    assert list(second.columns) == tickers
    # check_freq=False: CSV round-tripping drops the index's freq metadata,
    # which is irrelevant to the values we care about.
    pd.testing.assert_frame_equal(first[tickers], second[tickers], check_freq=False)


def test_load_or_fetch_refetches_when_stale(monkeypatch, tmp_path):
    tickers = ["VTI"]
    dates = pd.date_range("2020-01-01", periods=2, freq="D")
    sample = pd.DataFrame(
        {"VTI": [100.0, 101.0]}, index=pd.DatetimeIndex(dates, name="Date")
    )
    monkeypatch.setattr(fetch, "DATA_DIR", tmp_path)

    calls = {"n": 0}

    def fake_fetch(_tickers, _start, _end=None):
        calls["n"] += 1
        return sample

    monkeypatch.setattr(fetch, "fetch_prices", fake_fetch)

    fetch.load_or_fetch(tickers, start="2020-01-01", end="2020-01-03")
    assert calls["n"] == 1

    # Ask for a later end date than the cache covers -> stale -> refetch.
    fetch.load_or_fetch(tickers, start="2020-01-01", end="2021-01-01")
    assert calls["n"] == 2
