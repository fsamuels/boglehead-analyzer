"""Unit tests for Module 6 — the Dash dashboard.

These are structural/unit tests, not browser tests: they check that the app
wires together without error, that the layout exposes the component ids the
callbacks depend on, and that the small formatting helpers in
``dashboard/callbacks.py`` behave correctly on hand-checkable inputs. No
server is started and no network call is made.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import pytest

from dashboard.app import create_app
from dashboard.callbacks import (
    _annualize,
    _area_figure,
    _line_figure,
    _projection_table,
    _rebalance_log_table,
    _series_to_table,
)
from dashboard.layout import build_layout

EXPECTED_IDS = {
    "ticker-dropdown",
    "weight-sliders-container",
    "date-range",
    "investment-input",
    "strategy-radio",
    "threshold-slider",
    "run-button",
    "error-message",
    "cumulative-return-graph",
    "rolling-return-graph",
    "annualized-return-table",
    "portfolio-value-graph",
    "allocation-drift-graph",
    "rebalancing-comparison-graph",
    "rebalance-log-table",
    "cost-drag-graph",
    "cost-drag-table",
}


def _collect_ids(component) -> set:
    ids = set()
    component_id = getattr(component, "id", None)
    if isinstance(component_id, str):
        ids.add(component_id)

    children = getattr(component, "children", None)
    if children is None:
        return ids
    if isinstance(children, (list, tuple)):
        for child in children:
            ids |= _collect_ids(child)
    else:
        ids |= _collect_ids(children)
    return ids


def test_build_layout_exposes_expected_component_ids():
    layout = build_layout()
    ids = _collect_ids(layout)
    assert EXPECTED_IDS <= ids


def test_create_app_wires_layout_and_callbacks_without_error():
    app = create_app()
    assert app.layout is not None
    # One callback for the dynamic sliders, one for the main analysis run.
    assert len(app.callback_map) == 2


def test_line_figure_has_one_trace_per_column():
    frame = pd.DataFrame({"A": [1.0, 2.0], "B": [3.0, 4.0]})
    fig = _line_figure(frame, "Title")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2
    assert {trace.name for trace in fig.data} == {"A", "B"}


def test_area_figure_stacks_all_columns():
    frame = pd.DataFrame({"A": [0.6, 0.5], "B": [0.4, 0.5]})
    fig = _area_figure(frame, "Title")
    assert len(fig.data) == 2
    assert all(trace.stackgroup == "one" for trace in fig.data)


def test_series_to_table_as_percent_rounds_and_scales():
    series = pd.Series({"VTI": 0.14582, "BND": 0.0181})
    data, columns = _series_to_table(series, "Ticker", "Annualized return (%)", as_percent=True)
    assert columns == [{"name": "Ticker", "id": "Ticker"}, {"name": "Annualized return (%)", "id": "Annualized return (%)"}]
    lookup = {row["Ticker"]: row["Annualized return (%)"] for row in data}
    assert lookup["VTI"] == pytest.approx(14.58)
    assert lookup["BND"] == pytest.approx(1.81)


def test_annualize_matches_returns_module_formula():
    from analysis.returns import annualized_return

    prices = pd.DataFrame({"A": [100.0, 110.0, 121.0]})
    daily_ret = prices["A"].pct_change().dropna()
    expected = annualized_return(daily_ret.to_frame("A"))["A"]
    assert _annualize(daily_ret) == pytest.approx(expected)


def test_annualize_empty_series_is_zero():
    assert _annualize(pd.Series([], dtype=float)) == 0.0


def test_rebalance_log_table_empty_log_has_columns_but_no_rows():
    empty_log = pd.DataFrame(columns=["date", "asset", "action", "amount"])
    data, columns = _rebalance_log_table(empty_log)
    assert data == []
    assert [c["id"] for c in columns] == ["date", "asset", "action", "amount"]


def test_rebalance_log_table_sorts_newest_first_and_formats_dates():
    log = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-01", "2021-06-15"]),
            "asset": ["A", "B"],
            "action": ["buy", "sell"],
            "amount": [100.123, 50.0],
        }
    )
    data, _ = _rebalance_log_table(log)
    assert data[0]["date"] == "2021-06-15"
    assert data[1]["date"] == "2020-01-01"
    assert data[0]["amount"] == 50.0


def test_projection_table_uses_year_checkpoints():
    from analysis.costs import cost_drag_over_time

    projection = cost_drag_over_time(10_000.0, 0.07, 30, [0.0003, 0.01])
    data, columns = _projection_table(projection)
    years = [row["Year"] for row in data]
    assert years == [0, 5, 10, 15, 20, 25, 30]
    assert columns[0]["id"] == "Year"
    assert "0.03% ER" in columns[1]["id"]
