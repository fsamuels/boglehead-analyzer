"""Unit tests for Module 3 — portfolio construction (``analysis/portfolio.py``).

These use small, hand-checkable price frames so the expected numbers can be
verified by eye. No network or cached data is touched.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from analysis import portfolio


def _prices(values: dict, periods: int) -> pd.DataFrame:
    dates = pd.date_range("2020-01-01", periods=periods, freq="B")
    return pd.DataFrame(values, index=pd.DatetimeIndex(dates, name="Date"))


def test_validate_weights_accepts_sum_to_one():
    portfolio.validate_weights({"A": 0.6, "B": 0.4})  # no raise


def test_validate_weights_rejects_bad_sum():
    with pytest.raises(ValueError):
        portfolio.validate_weights({"A": 0.6, "B": 0.5})


def test_build_portfolio_allocates_by_weight():
    prices = _prices({"A": [100.0, 110.0], "B": [50.0, 55.0]}, 2)
    result = portfolio.build_portfolio(prices, {"A": 0.6, "B": 0.4}, 1000.0)

    # $600 / $100 = 6 shares of A; $400 / $50 = 8 shares of B.
    assert result["A"].iloc[0] == pytest.approx(600.0)
    assert result["B"].iloc[0] == pytest.approx(400.0)
    assert result["total"].iloc[0] == pytest.approx(1000.0)

    # Day 2: A worth 6*110=660, B worth 8*55=440, total=1100.
    assert result["A"].iloc[1] == pytest.approx(660.0)
    assert result["B"].iloc[1] == pytest.approx(440.0)
    assert result["total"].iloc[1] == pytest.approx(1100.0)


def test_build_portfolio_rejects_bad_weights():
    prices = _prices({"A": [100.0]}, 1)
    with pytest.raises(ValueError):
        portfolio.build_portfolio(prices, {"A": 0.5}, 1000.0)


def test_build_portfolio_rejects_unknown_ticker():
    prices = _prices({"A": [100.0]}, 1)
    with pytest.raises(ValueError):
        portfolio.build_portfolio(prices, {"A": 0.5, "Z": 0.5}, 1000.0)


def test_build_portfolio_handles_partial_history():
    # "NEW" starts a day late; its allocation should still price in once it appears.
    prices = _prices({"OLD": [100.0, 100.0, 100.0], "NEW": [np.nan, 50.0, 60.0]}, 3)
    result = portfolio.build_portfolio(prices, {"OLD": 0.5, "NEW": 0.5}, 1000.0)

    # NEW's first available price is 50 on day 2, so it buys 10 shares.
    assert np.isnan(result["NEW"].iloc[0])
    assert result["NEW"].iloc[1] == pytest.approx(500.0)
    assert result["NEW"].iloc[2] == pytest.approx(600.0)


def test_portfolio_returns():
    prices = _prices({"A": [100.0, 110.0, 99.0]}, 3)
    built = portfolio.build_portfolio(prices, {"A": 1.0}, 1000.0)
    ret = portfolio.portfolio_returns(built)

    assert len(ret) == 2
    assert ret.iloc[0] == pytest.approx(0.10)
    assert ret.iloc[1] == pytest.approx(-0.10)


def test_max_drawdown_simple():
    # Peak at 100, trough at 80 -> -20% drawdown.
    series = pd.Series([100.0, 90.0, 80.0, 95.0])
    assert portfolio.max_drawdown(series) == pytest.approx(-0.20)


def test_max_drawdown_no_loss_is_zero():
    series = pd.Series([100.0, 110.0, 120.0])
    assert portfolio.max_drawdown(series) == pytest.approx(0.0)


def test_max_drawdown_recovers_and_drops_again():
    # Peak 100 -> trough 80 (-20%), recover to 120 -> trough 90 (-25%).
    series = pd.Series([100.0, 80.0, 120.0, 90.0])
    assert portfolio.max_drawdown(series) == pytest.approx(-0.25)
