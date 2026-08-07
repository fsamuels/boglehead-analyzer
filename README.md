# Boglehead Portfolio Analyzer

A web dashboard for analyzing index-fund portfolios through a [Boglehead](https://www.bogleheads.org/wiki/Main_Page) lens: low-cost, broadly diversified, buy-and-hold, periodically rebalanced.

This is a Python learning project — each module introduces a new library concept deliberately (`pandas`, `NumPy`, `matplotlib`, `plotly`, `dash`) — that culminates in an interactive Dash dashboard. See [SPEC.md](SPEC.md) for the full design.

## What it does

Given a configurable portfolio of ETFs (default `VTI` / `VXUS` / `BND`), the analyzer:

- Fetches and caches historical price data
- Computes daily, cumulative, annualized, and rolling returns
- Simulates a lump-sum investment and tracks portfolio value and drawdown
- Compares rebalancing strategies (none / annual / threshold)
- Quantifies the compounding cost drag of expense ratios over time
- Surfaces all of it in an interactive Dash dashboard

## Project structure

```
boglehead-analyzer/
├── analysis/        # Core analysis modules (fetch, returns, portfolio, rebalancing, costs)
├── dashboard/       # Dash web app (app, layout, callbacks)
├── notebooks/       # Exploratory notebooks, one per module
│   └── images/      # Matplotlib chart PNGs, saved externally and linked from markdown cells
├── tests/           # Unit tests
├── data/raw/        # Cached CSV price data (git-ignored)
├── requirements.txt
└── SPEC.md          # Full project specification
```

The `analysis/` modules hold the math; the `dashboard/` layer stays thin and calls into them.

## Getting started

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Run the dashboard:

```bash
python -m dashboard.app
```

Then open [http://127.0.0.1:8050](http://127.0.0.1:8050). Pick your ETFs, set an
allocation, a date range, and an initial investment, then click **Run analysis**
to fetch/cache the price data and populate the four tabs.

Explore a module interactively:

```bash
jupyter lab
```

## Status

All six modules are implemented and tested — the analyzer is feature-complete
per the original spec, from data ingestion through the interactive dashboard.
Each module was explored in a notebook first (where applicable) and then
refactored into a clean module — see the per-module PRs.

The configurable ticker universe lives in [`analysis/config.py`](analysis/config.py)
as `AVAILABLE_TICKERS` (`VTI`, `VXUS`, `VOO`, `VT`, `BND`) with matching
`EXPENSE_RATIOS`. The default demo portfolio (`VTI` / `VXUS` / `BND`) is kept
separate so adding a selectable ETF never changes the default allocation.

### Module 1 — Data ingestion

`analysis/fetch.py` pulls historical **adjusted close** prices from `yfinance` and
caches them as one CSV per ticker under `data/raw/` (git-ignored):

- `fetch_prices(tickers, start, end=None)` — download adjusted closes, drop fully
  empty rows, return a date-indexed `DataFrame` (one column per ticker).
- `load_or_fetch(tickers, start, end=None)` — serve from the CSV cache when fresh,
  otherwise fetch and rewrite it. Freshness accounts for yfinance's exclusive
  `end` date and weekends, so the cache isn't perpetually invalidated.

Explore it in [`notebooks/01_data_ingestion.ipynb`](notebooks/01_data_ingestion.ipynb);
tests live in [`tests/test_fetch.py`](tests/test_fetch.py) and run offline (yfinance
is stubbed).

### Module 2 — Return calculations

`analysis/returns.py` turns a price frame into returns using `pandas` and
vectorized `NumPy` math. Tickers with a shorter history keep their leading
`NaN`s, so a newer ETF never contaminates an older one's numbers.

- `daily_returns(prices)` — simple percentage returns via `.pct_change()`.
- `log_returns(prices)` — `ln(P_t / P_{t-1})`; time-additive, handy for aggregation.
- `cumulative_returns(daily_ret)` — growth of $1 to date, `(1 + r).cumprod() - 1`.
- `annualized_return(daily_ret, periods_per_year=252)` — geometric CAGR per ticker.
- `rolling_return(daily_ret, window=252)` — trailing 1-year return across time.

Explore it in [`notebooks/02_returns.ipynb`](notebooks/02_returns.ipynb); tests
live in [`tests/test_returns.py`](tests/test_returns.py) and run on small,
hand-checkable frames (no network).

### Module 3 — Portfolio construction

`analysis/portfolio.py` turns a price frame and a target allocation into a
simulated lump-sum investment, using NumPy-style weighted operations and
`pandas` broadcasting. No rebalancing happens here — that's Module 4 — so the
allocation drifts with the market on its own.

- `validate_weights(weights)` — asserts weights sum to 1.0 (within tolerance).
- `build_portfolio(prices, weights, initial_investment)` — allocates the
  investment by weight, converts each ticker's dollar allocation to a share
  count at its first available price, then revalues daily. Returns a
  DataFrame with one column per ticker plus a `"total"` column.
- `portfolio_returns(portfolio_df)` — daily returns on the total portfolio
  value.
- `max_drawdown(portfolio_series)` — peak-to-trough maximum decline, as a
  negative fraction.

Explore it in [`notebooks/03_portfolio.ipynb`](notebooks/03_portfolio.ipynb);
tests live in [`tests/test_portfolio.py`](tests/test_portfolio.py) and run on
small, hand-checkable frames (no network).

### Module 4 — Rebalancing simulator

`analysis/rebalancing.py` simulates and compares three rebalancing
strategies via a stateful day-by-day loop over the price history, reusing
`portfolio.validate_weights` so weight checks stay in one place.

- `simulate(prices, weights, initial_investment, strategy, threshold=0.05)` —
  core simulation loop for one strategy (`"none"`, `"annual"`, or
  `"threshold"`). Starts from the same lump-sum share allocation as
  `portfolio.build_portfolio`, then on any day that triggers a rebalance,
  resizes shares back to the target dollar weights at that day's prices.
  Returns `(portfolio_values, rebalance_log)` — a per-ticker-plus-`"total"`
  value frame, and a log of every buy/sell with date, asset, action, and
  dollar amount. Days with an incomplete price row (a newer ETF that hasn't
  started trading) are never rebalanced.
- `_needs_rebalance_threshold(current_weights, target_weights, threshold)` —
  `True` if any asset's current weight deviates from target by more than
  `threshold`.
- `compare_strategies(prices, weights, initial_investment)` — runs all three
  strategies and returns their total portfolio values side by side as a
  `DataFrame` with columns `"none"`, `"annual"`, `"threshold"`.

Explore it in [`notebooks/04_rebalancing.ipynb`](notebooks/04_rebalancing.ipynb);
tests live in [`tests/test_rebalancing.py`](tests/test_rebalancing.py) and run
on small, hand-checkable frames (no network).

### Module 5 — Cost drag analysis

`analysis/costs.py` shows the compounding impact of expense ratios over
time — the core Boglehead argument that costs compound just like returns do,
but against you.

- `apply_expense_ratio(portfolio_series, expense_ratio_annual)` — deducts the
  annual ratio from a portfolio value series, spread evenly across trading
  days: each day's growth factor is multiplied by `(1 - expense_ratio / 252)`
  on top of that day's actual return, then compounded forward. The first
  observation is left untouched (no time has elapsed to accrue a cost yet).
- `cost_drag_over_time(initial_investment, annual_return, years, expense_ratios)` —
  a pure-math projection (no price data needed): for each expense ratio,
  compounds `(1 + annual_return) * (1 - expense_ratio)` per year. Returns a
  `DataFrame` indexed by year (0 through `years`), one column per ratio.
- `compare_funds(portfolio_series, expense_ratios_dict)` — applies a map of
  `{label: expense_ratio}` scenarios to the same return stream and returns
  their value series side by side.

Explore it in [`notebooks/05_cost_drag.ipynb`](notebooks/05_cost_drag.ipynb);
tests live in [`tests/test_costs.py`](tests/test_costs.py) and run on small,
hand-checkable series (no network).

### Module 6 — Dashboard

`dashboard/` wires all five analysis modules into an interactive Dash app.
The layout (`dashboard/layout.py`) and callbacks (`dashboard/callbacks.py`)
are kept separate: layout only defines components and their ids, callbacks
only call into `analysis/` and reshape results into Plotly figures and
`DataTable` rows — no math is duplicated in the dashboard layer.

- **Controls**: a multi-select ETF dropdown, one allocation slider per
  selected ticker (generated dynamically and normalized automatically, so
  they never have to sum to exactly 100%), a date range picker, an initial
  investment input, a rebalancing strategy selector, and a drift-threshold
  slider. Everything is gathered behind an explicit **Run analysis** button
  — one click fetches/caches the price data and computes all four tabs in a
  single pass, rather than re-fetching on every keystroke.
- **Returns tab**: cumulative return and rolling 1-year return charts, plus
  an annualized return table — one row per selected ticker.
- **Portfolio tab**: portfolio value over time, and an allocation-drift area
  chart showing each asset's share of the total across the full date range.
- **Rebalancing tab**: a `"none"` vs. `"annual"` vs. `"threshold"` strategy
  comparison chart, plus the paginated buy/sell event log for whichever
  strategy is selected in the controls.
- **Cost Drag tab**: this portfolio's blended expense ratio compared against
  a hypothetical 1.00% active fund over its actual price history, plus a
  pure-math 30-year projection table (using the portfolio's own historical
  annualized return) across a few representative expense ratios.

Edge cases are handled inline rather than left to crash the app: an empty
ticker selection, a non-positive investment amount, all-zero allocation
sliders, an insufficient date range, and fetch failures all clear the charts
and show a message in place of a traceback.

Run it locally with `python -m dashboard.app` (see
[Getting started](#getting-started)); tests live in
[`tests/test_dashboard.py`](tests/test_dashboard.py) and check the app wires
together and that the callback helper functions format data correctly —
they don't drive a real browser.

| Module | Area | Status |
|---|---|---|
| 1 | Data ingestion (`analysis/fetch.py`) | ✅ Complete |
| 2 | Return calculations (`analysis/returns.py`) | ✅ Complete |
| 3 | Portfolio construction (`analysis/portfolio.py`) | ✅ Complete |
| 4 | Rebalancing simulator (`analysis/rebalancing.py`) | ✅ Complete |
| 5 | Cost drag analysis (`analysis/costs.py`) | ✅ Complete |
| 6 | Dashboard (`dashboard/`) | ✅ Complete |

## Disclaimer

This is an educational project. Nothing here is financial advice. It uses
delayed/historical data only and does not place trades.
