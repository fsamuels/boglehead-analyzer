"""Unit tests for Module 5 — cost drag analysis (``analysis/costs.py``).

These use small, hand-checkable series so the expected numbers can be
verified by eye. No network or cached data is touched.
"""

from __future__ import annotations

import pandas as pd
import pytest

from analysis import costs


def test_apply_expense_ratio_leaves_first_value_unchanged():
    series = pd.Series([100.0, 100.0, 100.0])
    adjusted = costs.apply_expense_ratio(series, 0.03)
    assert adjusted.iloc[0] == pytest.approx(100.0)


def test_apply_expense_ratio_on_flat_prices_compounds_the_daily_drag():
    # No market return at all; the only movement is the expense drag itself.
    series = pd.Series([100.0, 100.0, 100.0])
    adjusted = costs.apply_expense_ratio(series, 0.03)

    daily_drag = 1 - 0.03 / 252
    assert adjusted.iloc[1] == pytest.approx(100.0 * daily_drag)
    assert adjusted.iloc[2] == pytest.approx(100.0 * daily_drag**2)


def test_apply_expense_ratio_zero_ratio_is_a_noop():
    series = pd.Series([100.0, 110.0, 99.0])
    adjusted = costs.apply_expense_ratio(series, 0.0)
    pd.testing.assert_series_equal(adjusted, series, check_names=False)


def test_apply_expense_ratio_higher_cost_yields_lower_value():
    series = pd.Series([100.0, 105.0, 108.0, 112.0])
    cheap = costs.apply_expense_ratio(series, 0.0003)
    expensive = costs.apply_expense_ratio(series, 0.01)
    assert (cheap.iloc[1:] > expensive.iloc[1:]).all()


def test_cost_drag_over_time_year_zero_is_initial_investment():
    result = costs.cost_drag_over_time(10_000.0, 0.07, 30, [0.0003, 0.01])
    assert result.loc[0].tolist() == pytest.approx([10_000.0, 10_000.0])


def test_cost_drag_over_time_matches_compound_formula():
    result = costs.cost_drag_over_time(10_000.0, 0.07, 30, [0.0003, 0.01])

    expected_cheap = 10_000.0 * ((1.07) * (1 - 0.0003)) ** 30
    expected_expensive = 10_000.0 * ((1.07) * (1 - 0.01)) ** 30

    assert result.loc[30, 0.0003] == pytest.approx(expected_cheap)
    assert result.loc[30, 0.01] == pytest.approx(expected_expensive)


def test_cost_drag_over_time_lower_expense_ratio_wins_at_terminal_year():
    result = costs.cost_drag_over_time(10_000.0, 0.07, 30, [0.0003, 0.01])
    assert result.loc[30, 0.0003] > result.loc[30, 0.01]


def test_compare_funds_returns_one_column_per_scenario():
    series = pd.Series([100.0, 105.0, 110.0])
    result = costs.compare_funds(series, {"cheap": 0.0003, "expensive": 0.01})

    assert list(result.columns) == ["cheap", "expensive"]
    assert result["cheap"].iloc[-1] > result["expensive"].iloc[-1]
    assert result["cheap"].iloc[0] == pytest.approx(100.0)
    assert result["expensive"].iloc[0] == pytest.approx(100.0)
