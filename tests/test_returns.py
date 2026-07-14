"""Unit tests for Module 2 — return calculations (``analysis/returns.py``).

These use small, hand-checkable price frames so the expected numbers can be
verified by eye. No network or cached data is touched.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from analysis import returns


def _prices(values: dict, periods: int) -> pd.DataFrame:
    dates = pd.date_range("2020-01-01", periods=periods, freq="B")
    return pd.DataFrame(values, index=pd.DatetimeIndex(dates, name="Date"))


def test_daily_returns_simple():
    prices = _prices({"A": [100.0, 110.0, 99.0]}, 3)
    ret = returns.daily_returns(prices)

    # First (all-NaN) row is dropped; remaining are simple pct changes.
    assert len(ret) == 2
    assert ret["A"].iloc[0] == pytest.approx(0.10)        # 100 -> 110
    assert ret["A"].iloc[1] == pytest.approx(-0.10)       # 110 -> 99


def test_daily_returns_matches_numpy_manual():
    prices = _prices({"A": [100.0, 105.0, 102.0, 108.0]}, 4)
    ret = returns.daily_returns(prices)

    values = prices["A"].to_numpy()
    manual = (values[1:] - values[:-1]) / values[:-1]
    np.testing.assert_allclose(ret["A"].to_numpy(), manual)


def test_log_returns_relationship():
    prices = _prices({"A": [100.0, 110.0, 121.0]}, 3)
    log_ret = returns.log_returns(prices)

    # ln(110/100) and ln(121/110); both equal ln(1.1).
    assert log_ret["A"].iloc[0] == pytest.approx(np.log(1.1))
    assert log_ret["A"].iloc[1] == pytest.approx(np.log(1.1))

    # Log returns sum to the log of total growth: ln(121/100).
    assert log_ret["A"].sum() == pytest.approx(np.log(1.21))


def test_log_vs_simple_small_moves_close():
    prices = _prices({"A": [100.0, 100.5, 101.0]}, 3)
    simple = returns.daily_returns(prices)["A"].to_numpy()
    logr = returns.log_returns(prices)["A"].to_numpy()
    # For small moves the two are nearly identical.
    np.testing.assert_allclose(simple, logr, atol=1e-3)


def test_cumulative_returns():
    prices = _prices({"A": [100.0, 110.0, 99.0]}, 3)
    daily = returns.daily_returns(prices)
    cum = returns.cumulative_returns(daily)

    # +10% then -10% -> 1.1 * 0.9 - 1 = -0.01 cumulatively.
    assert cum["A"].iloc[0] == pytest.approx(0.10)
    assert cum["A"].iloc[1] == pytest.approx(-0.01)


def test_annualized_return_geometric():
    # 252 trading days, each +0.1% -> annualizes to (1.001**252) - 1 over one year.
    daily = pd.DataFrame({"A": [0.001] * 252})
    ann = returns.annualized_return(daily)
    assert ann["A"] == pytest.approx(1.001 ** 252 - 1)


def test_annualized_return_scales_partial_history():
    # Half a year of flat 0% returns annualizes to 0%.
    daily = pd.DataFrame({"A": [0.0] * 126})
    ann = returns.annualized_return(daily, periods_per_year=252)
    assert ann["A"] == pytest.approx(0.0)


def test_rolling_return_window():
    # 5 days of +10% each; a 2-day rolling return is 1.1*1.1 - 1 = 0.21.
    daily = pd.DataFrame({"A": [0.10] * 5})
    roll = returns.rolling_return(daily, window=2)

    assert np.isnan(roll["A"].iloc[0])   # no full window yet
    assert np.isnan(roll["A"].iloc[1])
    assert roll["A"].iloc[2] == pytest.approx(0.21)
    assert roll["A"].iloc[4] == pytest.approx(0.21)


def test_partial_history_does_not_contaminate():
    # "NEW" starts a day late; its NaN must not bleed into "OLD".
    prices = _prices({"OLD": [100.0, 101.0, 102.0], "NEW": [np.nan, 50.0, 55.0]}, 3)
    ret = returns.daily_returns(prices)

    assert ret["OLD"].notna().all()
    assert np.isnan(ret["NEW"].iloc[0])          # no prior price for NEW
    assert ret["NEW"].iloc[1] == pytest.approx(0.10)  # 50 -> 55
