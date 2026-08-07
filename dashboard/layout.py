"""Module 6 — Dashboard layout.

Defines the Dash UI components (ticker input, allocation sliders, date range
picker, investment input, rebalancing controls) and the tabbed sections:
Returns, Portfolio, Rebalancing, Cost Drag. See SPEC.md.
"""

from __future__ import annotations

from datetime import date

from dash import dash_table, dcc, html

from analysis.config import AVAILABLE_TICKERS, DEFAULT_INVESTMENT, DEFAULT_START, DEFAULT_TICKERS

STRATEGY_OPTIONS = [
    {"label": "None", "value": "none"},
    {"label": "Annual", "value": "annual"},
    {"label": "Threshold", "value": "threshold"},
]


def _controls() -> html.Div:
    """The configuration panel: tickers, allocation, date range, investment, rebalancing."""
    return html.Div(
        [
            html.Div(
                [
                    html.Label("ETFs to analyze"),
                    dcc.Dropdown(
                        id="ticker-dropdown",
                        options=[{"label": t, "value": t} for t in AVAILABLE_TICKERS],
                        value=DEFAULT_TICKERS,
                        multi=True,
                        clearable=False,
                    ),
                ],
                className="control",
            ),
            html.Div(
                [
                    html.Label("Target allocation (normalized automatically)"),
                    html.Div(id="weight-sliders-container"),
                ],
                className="control",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Date range"),
                            dcc.DatePickerRange(
                                id="date-range",
                                start_date=DEFAULT_START,
                                end_date=date.today().isoformat(),
                                max_date_allowed=date.today().isoformat(),
                            ),
                        ],
                        className="control",
                    ),
                    html.Div(
                        [
                            html.Label("Initial investment ($)"),
                            dcc.Input(
                                id="investment-input",
                                type="number",
                                value=DEFAULT_INVESTMENT,
                                min=100,
                                step=100,
                            ),
                        ],
                        className="control",
                    ),
                ],
                className="control-row",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Rebalancing strategy (Rebalancing tab log)"),
                            dcc.RadioItems(
                                id="strategy-radio",
                                options=STRATEGY_OPTIONS,
                                value="threshold",
                                inline=True,
                            ),
                        ],
                        className="control",
                    ),
                    html.Div(
                        [
                            html.Label("Drift threshold"),
                            dcc.Slider(
                                id="threshold-slider",
                                min=0.01,
                                max=0.20,
                                step=0.01,
                                value=0.05,
                                marks={0.01: "1%", 0.05: "5%", 0.10: "10%", 0.20: "20%"},
                                tooltip={"placement": "bottom"},
                            ),
                        ],
                        className="control",
                    ),
                ],
                className="control-row",
            ),
            html.Button("Run analysis", id="run-button", n_clicks=0),
            html.Div(
                "Adjust the controls above, then click \"Run analysis\" to fetch data and render the tabs below.",
                id="error-message",
                className="error-message",
            ),
        ],
        className="controls",
    )


def build_layout() -> html.Div:
    """Return the root Dash layout component."""
    returns_tab = dcc.Tab(
        label="Returns",
        children=[
            dcc.Graph(id="cumulative-return-graph"),
            dcc.Graph(id="rolling-return-graph"),
            html.H4("Annualized return"),
            dash_table.DataTable(id="annualized-return-table", style_table={"maxWidth": "400px"}),
        ],
    )

    portfolio_tab = dcc.Tab(
        label="Portfolio",
        children=[
            dcc.Graph(id="portfolio-value-graph"),
            dcc.Graph(id="allocation-drift-graph"),
        ],
    )

    rebalancing_tab = dcc.Tab(
        label="Rebalancing",
        children=[
            dcc.Graph(id="rebalancing-comparison-graph"),
            html.H4("Rebalance event log"),
            dash_table.DataTable(id="rebalance-log-table", page_size=10),
        ],
    )

    cost_drag_tab = dcc.Tab(
        label="Cost Drag",
        children=[
            dcc.Graph(id="cost-drag-graph"),
            html.H4("30-year projection"),
            dash_table.DataTable(id="cost-drag-table"),
        ],
    )

    return html.Div(
        [
            html.H1("Boglehead Portfolio Analyzer"),
            html.P(
                "Analyze a configurable index-fund portfolio through a Boglehead lens: "
                "low-cost, broadly diversified, buy-and-hold, periodically rebalanced."
            ),
            _controls(),
            dcc.Tabs(
                id="tabs",
                children=[returns_tab, portfolio_tab, rebalancing_tab, cost_drag_tab],
            ),
        ],
        className="app-container",
    )
