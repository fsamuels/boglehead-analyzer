"""Module 6 — Dashboard callbacks.

Reactive logic connecting UI components to the analysis modules. Callbacks
stay thin: all the math happens in ``analysis/``, this module only calls into
it and reshapes the results into Plotly figures and DataTable rows. See
SPEC.md.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from dash import ALL, Input, Output, State, dcc, html

from analysis import costs, fetch, portfolio, rebalancing, returns
from analysis.config import DEFAULT_WEIGHTS, EXPENSE_RATIOS

# Terminal-year checkpoints shown in the 30-year cost-drag projection table.
_PROJECTION_YEARS = [0, 5, 10, 15, 20, 25, 30]


def _line_figure(frame: pd.DataFrame, title: str, y_tickformat: str | None = None) -> go.Figure:
    """A multi-series line chart, one trace per column, indexed by date."""
    fig = go.Figure()
    for column in frame.columns:
        fig.add_trace(go.Scatter(x=frame.index, y=frame[column], mode="lines", name=str(column)))
    fig.update_layout(title=title, margin=dict(t=40, b=30, l=50, r=20), legend_title_text="")
    if y_tickformat:
        fig.update_yaxes(tickformat=y_tickformat)
    return fig


def _area_figure(frame: pd.DataFrame, title: str, y_tickformat: str | None = None) -> go.Figure:
    """A stacked area chart, one trace per column, indexed by date."""
    fig = go.Figure()
    for column in frame.columns:
        fig.add_trace(go.Scatter(x=frame.index, y=frame[column], mode="lines", name=str(column), stackgroup="one"))
    fig.update_layout(title=title, margin=dict(t=40, b=30, l=50, r=20), legend_title_text="")
    if y_tickformat:
        fig.update_yaxes(tickformat=y_tickformat)
    return fig


def _series_to_table(series: pd.Series, index_label: str, value_label: str, as_percent: bool = False):
    """Convert a ticker-indexed Series into DataTable ``(data, columns)``."""
    frame = series.rename(value_label).reset_index()
    frame.columns = [index_label, value_label]
    frame[value_label] = (frame[value_label] * 100 if as_percent else frame[value_label]).round(2)
    columns = [{"name": c, "id": c} for c in frame.columns]
    return frame.to_dict("records"), columns


def _annualize(daily_ret: pd.Series, periods_per_year: int = 252) -> float:
    """Geometric annualized return for a single daily-return series."""
    n_days = daily_ret.count()
    if n_days == 0:
        return 0.0
    growth_factor = (1 + daily_ret).prod()
    return growth_factor ** (periods_per_year / n_days) - 1


def _rebalance_log_table(log: pd.DataFrame):
    columns = [{"name": c.title(), "id": c} for c in ["date", "asset", "action", "amount"]]
    if log.empty:
        return [], columns
    display = log.copy()
    display["date"] = display["date"].dt.strftime("%Y-%m-%d")
    display["amount"] = display["amount"].round(2)
    display = display.sort_values("date", ascending=False)
    return display.to_dict("records"), columns


def _projection_table(projection: pd.DataFrame):
    checkpoints = [year for year in _PROJECTION_YEARS if year in projection.index]
    display = projection.loc[checkpoints].round(2).reset_index()
    display.columns = ["Year"] + [f"{ratio:.2%} ER" for ratio in projection.columns]
    columns = [{"name": c, "id": c} for c in display.columns]
    return display.to_dict("records"), columns


def _empty_outputs(message: str) -> tuple:
    empty_fig = go.Figure()
    return (
        empty_fig,  # cumulative-return-graph
        empty_fig,  # rolling-return-graph
        [],  # annualized-return-table data
        [],  # annualized-return-table columns
        empty_fig,  # portfolio-value-graph
        empty_fig,  # allocation-drift-graph
        empty_fig,  # rebalancing-comparison-graph
        [],  # rebalance-log-table data
        [],  # rebalance-log-table columns
        empty_fig,  # cost-drag-graph
        [],  # cost-drag-table data
        [],  # cost-drag-table columns
        message,  # error-message
    )


def register_callbacks(app) -> None:
    """Register all Dash callbacks on the given app."""

    @app.callback(
        Output("weight-sliders-container", "children"),
        Input("ticker-dropdown", "value"),
    )
    def update_weight_sliders(selected_tickers):
        selected_tickers = selected_tickers or []
        equal_share_pct = 100 / len(selected_tickers) if selected_tickers else 0

        sliders = []
        for ticker in selected_tickers:
            default_pct = round(DEFAULT_WEIGHTS[ticker] * 100) if ticker in DEFAULT_WEIGHTS else round(equal_share_pct)
            sliders.append(
                html.Div(
                    [
                        html.Label(ticker),
                        dcc.Slider(
                            id={"type": "weight-slider", "ticker": ticker},
                            min=0,
                            max=100,
                            step=5,
                            value=default_pct,
                            tooltip={"placement": "bottom"},
                        ),
                    ],
                    className="weight-slider-row",
                )
            )
        return sliders

    @app.callback(
        Output("cumulative-return-graph", "figure"),
        Output("rolling-return-graph", "figure"),
        Output("annualized-return-table", "data"),
        Output("annualized-return-table", "columns"),
        Output("portfolio-value-graph", "figure"),
        Output("allocation-drift-graph", "figure"),
        Output("rebalancing-comparison-graph", "figure"),
        Output("rebalance-log-table", "data"),
        Output("rebalance-log-table", "columns"),
        Output("cost-drag-graph", "figure"),
        Output("cost-drag-table", "data"),
        Output("cost-drag-table", "columns"),
        Output("error-message", "children"),
        Input("run-button", "n_clicks"),
        State("ticker-dropdown", "value"),
        State({"type": "weight-slider", "ticker": ALL}, "value"),
        State({"type": "weight-slider", "ticker": ALL}, "id"),
        State("date-range", "start_date"),
        State("date-range", "end_date"),
        State("investment-input", "value"),
        State("strategy-radio", "value"),
        State("threshold-slider", "value"),
        prevent_initial_call=True,
    )
    def run_analysis(
        _n_clicks,
        tickers,
        slider_values,
        slider_ids,
        start_date,
        end_date,
        investment,
        strategy,
        threshold,
    ):
        if not tickers:
            return _empty_outputs("Select at least one ETF.")
        if not investment or investment <= 0:
            return _empty_outputs("Initial investment must be a positive number.")

        raw_weights = {slider_id["ticker"]: (value or 0) for slider_id, value in zip(slider_ids, slider_values)}
        total_raw = sum(raw_weights.values())
        if total_raw <= 0:
            return _empty_outputs("Move at least one allocation slider above 0%.")
        weights = {ticker: value / total_raw for ticker, value in raw_weights.items() if value > 0}

        try:
            prices = fetch.load_or_fetch(tickers, start_date, end_date).dropna(how="all")
        except Exception as exc:  # yfinance/network failures shouldn't crash the app
            return _empty_outputs(f"Could not fetch price data: {exc}")

        if len(prices) < 2:
            return _empty_outputs("Not enough price history in the selected date range.")

        try:
            daily_ret = returns.daily_returns(prices)
            cumulative_fig = _line_figure(returns.cumulative_returns(daily_ret), "Cumulative return", ".0%")
            rolling_fig = _line_figure(returns.rolling_return(daily_ret), "Rolling 1-year return", ".0%")
            annualized_data, annualized_columns = _series_to_table(
                returns.annualized_return(daily_ret), "Ticker", "Annualized return (%)", as_percent=True
            )

            built = portfolio.build_portfolio(prices, weights, investment)
            portfolio_fig = _line_figure(built[["total"]], "Portfolio value over time", "$,.0f")

            weight_tickers = list(weights.keys())
            weights_over_time = built[weight_tickers].div(built["total"], axis=0)
            drift_fig = _area_figure(weights_over_time, "Allocation drift over time", ".0%")

            comparison = rebalancing.compare_strategies(prices, weights, investment)
            rebalance_fig = _line_figure(comparison, "Rebalancing strategy comparison", "$,.0f")

            _, log = rebalancing.simulate(prices, weights, investment, strategy, threshold=threshold or 0.05)
            log_data, log_columns = _rebalance_log_table(log)

            blended_expense_ratio = sum(weights[t] * EXPENSE_RATIOS.get(t, 0.0) for t in weight_tickers)
            cost_comparison = costs.compare_funds(
                built["total"], {"this portfolio": blended_expense_ratio, "1.00% active fund": 0.01}
            )
            cost_fig = _line_figure(cost_comparison, "Cost of a 1.00% expense ratio vs. this portfolio", "$,.0f")

            assumed_annual_return = _annualize(built["total"].pct_change().dropna())
            projection = costs.cost_drag_over_time(
                investment, assumed_annual_return, 30, [blended_expense_ratio, 0.005, 0.01]
            )
            cost_table_data, cost_table_columns = _projection_table(projection)
        except ValueError as exc:
            return _empty_outputs(str(exc))

        return (
            cumulative_fig,
            rolling_fig,
            annualized_data,
            annualized_columns,
            portfolio_fig,
            drift_fig,
            rebalance_fig,
            log_data,
            log_columns,
            cost_fig,
            cost_table_data,
            cost_table_columns,
            "",
        )
