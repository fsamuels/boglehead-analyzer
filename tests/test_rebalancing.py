"""Unit tests for Module 4 — rebalancing simulator (``analysis/rebalancing.py``).

These use small, hand-checkable price frames so the expected numbers can be
verified by eye. No network or cached data is touched.
"""

from __future__ import annotations

import pandas as pd
import pytest

from analysis import portfolio, rebalancing


def _prices(values: dict, dates) -> pd.DataFrame:
    return pd.DataFrame(values, index=pd.DatetimeIndex(dates, name="Date"))


def test_needs_rebalance_threshold_true_when_deviation_exceeds():
    current = pd.Series({"A": 0.667, "B": 0.333})
    target = pd.Series({"A": 0.5, "B": 0.5})
    assert rebalancing._needs_rebalance_threshold(current, target, 0.05) is True


def test_needs_rebalance_threshold_false_within_tolerance():
    current = pd.Series({"A": 0.52, "B": 0.48})
    target = pd.Series({"A": 0.5, "B": 0.5})
    assert rebalancing._needs_rebalance_threshold(current, target, 0.05) is False


def test_simulate_rejects_unknown_strategy():
    prices = _prices({"A": [100.0]}, ["2020-01-01"])
    with pytest.raises(ValueError):
        rebalancing.simulate(prices, {"A": 1.0}, 1000.0, "yolo")


def test_simulate_rejects_bad_weights():
    prices = _prices({"A": [100.0]}, ["2020-01-01"])
    with pytest.raises(ValueError):
        rebalancing.simulate(prices, {"A": 0.5}, 1000.0, "none")


def test_simulate_none_never_rebalances_and_matches_build_portfolio():
    dates = pd.date_range("2020-01-01", periods=3, freq="B")
    prices = _prices({"A": [100.0, 200.0, 200.0], "B": [100.0, 100.0, 50.0]}, dates)
    weights = {"A": 0.5, "B": 0.5}

    values, log = rebalancing.simulate(prices, weights, 1000.0, "none")

    assert log.empty
    expected = portfolio.build_portfolio(prices, weights, 1000.0)
    pd.testing.assert_series_equal(values["total"], expected["total"], check_freq=False)


def test_simulate_threshold_rebalances_on_drift():
    dates = pd.date_range("2020-01-01", periods=3, freq="B")
    # Day 2: A doubles, B flat -> A drifts to 2/3 of the portfolio (> 5% threshold).
    prices = _prices({"A": [100.0, 200.0, 200.0], "B": [100.0, 100.0, 100.0]}, dates)
    weights = {"A": 0.5, "B": 0.5}

    values, log = rebalancing.simulate(prices, weights, 1000.0, "threshold", threshold=0.05)

    # Total value is unaffected by rebalancing itself, only reshuffled between assets.
    assert values["total"].iloc[1] == pytest.approx(1500.0)
    assert values["A"].iloc[1] == pytest.approx(750.0)
    assert values["B"].iloc[1] == pytest.approx(750.0)

    day2 = dates[1]
    day2_log = log[log["date"] == day2].set_index("asset")
    assert day2_log.loc["A", "action"] == "sell"
    assert day2_log.loc["A", "amount"] == pytest.approx(250.0)
    assert day2_log.loc["B", "action"] == "buy"
    assert day2_log.loc["B", "amount"] == pytest.approx(250.0)

    # Day 3: prices unchanged from the just-rebalanced allocation -> no further trade.
    day3 = dates[2]
    assert log[log["date"] == day3].empty


def test_simulate_annual_rebalances_on_first_trading_day_of_new_year():
    dates = pd.to_datetime(["2020-12-30", "2020-12-31", "2021-01-04"])
    prices = _prices({"A": [100.0, 100.0, 100.0], "B": [100.0, 150.0, 150.0]}, dates)
    weights = {"A": 0.5, "B": 0.5}

    values, log = rebalancing.simulate(prices, weights, 1000.0, "annual")

    # No rebalance while still within 2020, even though B has drifted.
    assert log[log["date"] == dates[1]].empty

    # First trading day of 2021 triggers the rebalance.
    day3 = dates[2]
    day3_log = log[log["date"] == day3].set_index("asset")
    assert values["total"].iloc[2] == pytest.approx(1250.0)
    assert day3_log.loc["A", "action"] == "buy"
    assert day3_log.loc["A", "amount"] == pytest.approx(125.0)
    assert day3_log.loc["B", "action"] == "sell"
    assert day3_log.loc["B", "amount"] == pytest.approx(125.0)


def test_simulate_skips_rebalance_on_incomplete_price_row():
    dates = pd.date_range("2020-01-01", periods=2, freq="B")
    prices = _prices({"A": [100.0, 200.0], "B": [float("nan"), 100.0]}, dates)
    # threshold=0 would force a rebalance every day if it weren't skipped on NaN rows.
    values, log = rebalancing.simulate(prices, {"A": 1.0}, 1000.0, "threshold", threshold=0.0)
    assert log.empty


def test_compare_strategies_returns_expected_columns():
    dates = pd.date_range("2020-01-01", periods=5, freq="B")
    prices = _prices(
        {"A": [100.0, 110.0, 120.0, 90.0, 130.0], "B": [50.0, 55.0, 45.0, 60.0, 40.0]},
        dates,
    )
    weights = {"A": 0.6, "B": 0.4}

    result = rebalancing.compare_strategies(prices, weights, 1000.0)

    assert list(result.columns) == ["none", "annual", "threshold"]
    assert len(result) == 5
    # First-day value should be the initial investment under every strategy.
    assert result.iloc[0].tolist() == pytest.approx([1000.0, 1000.0, 1000.0])
