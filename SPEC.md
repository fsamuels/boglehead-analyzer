# Boglehead Portfolio Analyzer — Project Spec

## Overview

A web dashboard for analyzing index fund portfolios through a Boglehead lens: low-cost, broadly diversified, buy-and-hold, periodically rebalanced. The project is scoped as a Python learning vehicle, so each module introduces a new library concept deliberately. The final artifact is a GitHub portfolio piece with a live Dash dashboard.

---

## Goals

**Learning goals (primary)**
- Get comfortable with `pandas` for time series data manipulation
- Learn `NumPy` for vectorized numerical operations
- Build intuition for data visualization with `matplotlib` and `plotly`
- Understand how to structure a real Python project (modules, separation of concerns, requirements)
- Produce clean, readable code that can be explained in an interview

**Output goals (secondary)**
- A working dashboard that analyzes a configurable ETF portfolio
- A GitHub repo that demonstrates agentic development process via PR descriptions
- A portfolio piece legible to both technical and non-technical reviewers

---

## Non-Goals

- Real-time trading or live market data (delayed/historical data only)
- Tax-lot tracking or tax optimization
- Support for individual stocks (ETFs and index funds only, per Boglehead philosophy)
- Authentication or multi-user support
- Deployment beyond localhost (stretch goal only)

---

## Tech Stack

| Purpose | Library | Version target |
|---|---|---|
| Data fetching | `yfinance` | latest |
| Data manipulation | `pandas` | 2.x |
| Numerical analysis | `numpy` | 1.x / 2.x |
| Static charts | `matplotlib` | 3.x |
| Interactive charts | `plotly` | 5.x |
| Dashboard / web UI | `dash` | 2.x |
| Notebook exploration | `jupyterlab` | 4.x |
| Dependency management | `pip` + `requirements.txt` | — |

No database. Data is fetched from `yfinance` and cached locally as CSV files in `data/raw/`.

---

## Repository Structure

```
boglehead-analyzer/
├── data/
│   └── raw/                    # Cached CSV price data (git-ignored)
├── analysis/
│   ├── __init__.py
│   ├── fetch.py                # Module 1: data ingestion
│   ├── returns.py              # Module 2: return calculations
│   ├── portfolio.py            # Module 3: portfolio construction
│   ├── rebalancing.py          # Module 4: rebalancing simulator
│   └── costs.py                # Module 5: cost drag analysis
├── dashboard/
│   ├── __init__.py
│   ├── app.py                  # Module 6: Dash entry point
│   ├── layout.py               # UI component layout
│   └── callbacks.py            # Reactive logic
├── notebooks/
│   ├── 01_data_ingestion.ipynb
│   ├── 02_returns.ipynb
│   ├── 03_portfolio.ipynb
│   ├── 04_rebalancing.ipynb
│   └── 05_cost_drag.ipynb
├── tests/
│   └── test_returns.py         # Basic unit tests (stretch)
├── .gitignore
├── README.md
├── requirements.txt
└── SPEC.md                     # This file
```

**Convention:** Each module is explored in a notebook first, then refactored into a clean `.py` file. The notebook is kept in the repo as an honest artifact of the exploratory process.

---

## Module Specifications

---

### Module 1 — Data Ingestion (`analysis/fetch.py`)

**Purpose:** Pull and cache historical adjusted close prices for a configurable list of ETFs.

**Key concepts introduced:** `yfinance` API, `pandas.DataFrame`, datetime indexing, file I/O with `pandas`, handling missing data.

**Inputs:**
- `tickers: list[str]` — e.g. `["VTI", "VXUS", "BND"]`
- `start: str` — ISO date string, e.g. `"2010-01-01"`
- `end: str` — ISO date string, defaults to today

**Outputs:**
- `pandas.DataFrame` with date index and one column per ticker (adjusted close price)
- CSV written to `data/raw/{ticker}.csv` for caching

**Functions to implement:**

```python
def fetch_prices(tickers, start, end=None) -> pd.DataFrame
    # Downloads adjusted close prices via yfinance
    # Drops rows where all values are NaN
    # Returns aligned DataFrame (inner join on dates)

def load_or_fetch(tickers, start, end=None) -> pd.DataFrame
    # Checks data/raw/ for cached CSVs first
    # Falls back to fetch_prices() if cache is stale or missing
    # Cache is considered stale if end date > last cached date
```

**What to explore in notebook:**
- What does raw `yfinance` output look like?
- What happens at date boundaries (weekends, holidays)?
- What does `.info()`, `.describe()`, `.head()` tell you?
- How do you handle a ticker that has less history than others (e.g. a newer ETF)?

---

### Module 2 — Return Calculations (`analysis/returns.py`)

**Purpose:** Compute daily, cumulative, and annualized returns from price data.

**Key concepts introduced:** NumPy vectorized math, `pandas` `.pct_change()`, log returns, rolling windows, `np.log()`, `np.exp()`.

**Inputs:**
- `prices: pd.DataFrame` — output of Module 1

**Outputs:**
- DataFrames of daily returns, cumulative returns, and annualized returns per ticker

**Functions to implement:**

```python
def daily_returns(prices) -> pd.DataFrame
    # Simple percentage returns: (P_t - P_{t-1}) / P_{t-1}
    # Use pandas .pct_change() first, then replicate manually with NumPy

def log_returns(prices) -> pd.DataFrame
    # Log returns: ln(P_t / P_{t-1})
    # Use np.log() — explain in a comment why log returns are useful

def cumulative_returns(daily_ret) -> pd.DataFrame
    # (1 + r_1) * (1 + r_2) * ... - 1
    # Use (1 + daily_ret).cumprod() - 1

def annualized_return(daily_ret, periods_per_year=252) -> pd.Series
    # Geometric annualized return
    # (1 + total_return)^(252/n_days) - 1

def rolling_return(daily_ret, window=252) -> pd.DataFrame
    # Rolling 1-year return window
    # Useful for visualizing volatility across time
```

**What to explore in notebook:**
- Plot cumulative returns for all tickers on one chart
- Compare simple vs log returns — when does it matter?
- Which ETF had the best 5-year rolling return? Which had the worst drawdown?

---

### Module 3 — Portfolio Construction (`analysis/portfolio.py`)

**Purpose:** Define a target allocation, simulate investing a lump sum, and track portfolio value over time.

**Key concepts introduced:** NumPy weighted operations (`np.dot`), `pandas` alignment, broadcasting, scalar vs array operations.

**Inputs:**
- `prices: pd.DataFrame`
- `weights: dict` — e.g. `{"VTI": 0.60, "VXUS": 0.30, "BND": 0.10}`
- `initial_investment: float` — e.g. `10000.0`

**Outputs:**
- `pd.Series` of portfolio value over time
- `pd.DataFrame` of individual asset values over time

**Functions to implement:**

```python
def validate_weights(weights) -> None
    # Assert weights sum to 1.0 (within floating point tolerance)
    # Assert all tickers in weights exist in prices columns

def build_portfolio(prices, weights, initial_investment) -> pd.DataFrame
    # Allocate initial_investment according to weights
    # Track each asset's value separately
    # Return DataFrame with columns per ticker + "total"

def portfolio_returns(portfolio_df) -> pd.Series
    # Daily returns on the total portfolio value

def max_drawdown(portfolio_series) -> float
    # Peak-to-trough maximum drawdown
    # (min value in window - rolling max) / rolling max
```

**What to explore in notebook:**
- Visualize asset allocation drift over time (pie chart at start vs end)
- Compare this portfolio to 100% VTI — what was the diversification benefit?
- What was the worst drawdown period? When did recovery occur?

---

### Module 4 — Rebalancing Simulator (`analysis/rebalancing.py`)

**Purpose:** Simulate and compare rebalancing strategies. Quantify the behavioral and return impact of discipline vs drift.

**Key concepts introduced:** Conditional logic over time series, `pandas` `.resample()`, iterating over DatetimeIndex, stateful simulation loops.

**Rebalancing strategies to implement:**
- `"none"` — never rebalance, let it drift
- `"annual"` — rebalance on the first trading day of each calendar year
- `"threshold"` — rebalance whenever any asset drifts more than N% from target (e.g. 5%)

**Inputs:**
- `prices: pd.DataFrame`
- `weights: dict`
- `initial_investment: float`
- `strategy: str` — `"none"`, `"annual"`, or `"threshold"`
- `threshold: float` — drift tolerance for threshold strategy (default `0.05`)

**Outputs:**
- `pd.DataFrame` of portfolio value over time per strategy (for comparison)
- `pd.DataFrame` of rebalance events (date, asset, action, amount)

**Functions to implement:**

```python
def simulate(prices, weights, initial_investment, strategy, threshold=0.05) -> tuple[pd.DataFrame, pd.DataFrame]
    # Core simulation loop
    # Returns (portfolio_values, rebalance_log)

def _needs_rebalance_threshold(current_weights, target_weights, threshold) -> bool
    # Returns True if any asset deviates by more than threshold

def compare_strategies(prices, weights, initial_investment) -> pd.DataFrame
    # Runs all three strategies and returns combined portfolio value DataFrame
    # Columns: "none", "annual", "threshold"
```

**What to explore in notebook:**
- Plot all three strategies on the same chart
- How many times did each strategy rebalance over 10 years?
- What was the terminal value difference? (Hint: it's often smaller than expected — that's the point)
- What was the max drawdown difference across strategies?

---

### Module 5 — Cost Drag Analysis (`analysis/costs.py`)

**Purpose:** Show the compounding impact of expense ratios over time. This is the core Boglehead argument: costs compound just like returns do, but against you.

**Key concepts introduced:** Compound growth math, NumPy parameter sweeps (`np.linspace`, broadcasting over 2D arrays), `matplotlib` for clear comparative charts.

**Default expense ratios (configurable):**
- VTI: 0.03%
- VXUS: 0.07%
- BND: 0.03%
- Actively managed fund baseline: 1.00%

**Functions to implement:**

```python
def apply_expense_ratio(portfolio_series, expense_ratio_annual) -> pd.Series
    # Deduct expense ratio daily: (1 - expense_ratio/252) per day
    # Returns adjusted portfolio value series

def cost_drag_over_time(initial_investment, annual_return, years, expense_ratios) -> pd.DataFrame
    # Pure math projection (no price data needed)
    # For each expense ratio in expense_ratios, compute terminal value
    # Returns DataFrame: rows=years, columns=expense ratios

def compare_funds(portfolio_series, expense_ratios_dict) -> pd.DataFrame
    # Given a portfolio return stream, apply different expense ratios
    # Returns DataFrame of portfolio values per expense ratio scenario
```

**What to explore in notebook:**
- Plot terminal value at year 30 for expense ratios from 0% to 2% — show the curve
- Specific comparison: $10,000 invested for 30 years at 7% return, 0.03% vs 1.0% ER. What's the dollar difference?
- At what point do costs start to visibly separate the curves?

---

### Module 6 — Dashboard (`dashboard/`)

**Purpose:** Wire all analysis modules into an interactive web app using Dash.

**Key concepts introduced:** Dash component layout, callback functions, reactive UI, separating layout from logic.

**UI components:**

| Component | Type | Purpose |
|---|---|---|
| Ticker input | Multi-select dropdown | Choose ETFs to analyze |
| Allocation sliders | Dash `dcc.Slider` per ticker | Set target weights (must sum to 100%) |
| Date range picker | `dcc.DatePickerRange` | Historical window |
| Initial investment input | `dcc.Input` | Dollar amount |
| Rebalancing strategy | `dcc.RadioItems` | None / Annual / Threshold |
| Threshold slider | `dcc.Slider` | Drift tolerance (only active for threshold strategy) |

**Dashboard tabs / sections:**

1. **Returns** — Cumulative return chart, annualized return table, rolling 1-year return chart
2. **Portfolio** — Portfolio value over time, asset allocation drift chart
3. **Rebalancing** — Strategy comparison chart, rebalance event log table
4. **Cost Drag** — Expense ratio impact chart, 30-year projection table

**Key implementation notes:**
- Keep callback logic thin — call into `analysis/` modules, don't repeat math in `callbacks.py`
- Use `plotly.graph_objects` for charts (not `matplotlib`) — they're natively interactive in Dash
- Handle edge cases in the UI: weights not summing to 100%, date ranges with insufficient data, missing tickers

---

## Default Configuration

For development and demo purposes, default to this portfolio:

```python
DEFAULT_TICKERS = ["VTI", "VXUS", "BND"]
DEFAULT_WEIGHTS = {"VTI": 0.60, "VXUS": 0.30, "BND": 0.10}
DEFAULT_START = "2013-01-01"   # VXUS inception was 2011, gives a few years of buffer
DEFAULT_INVESTMENT = 10000.0
DEFAULT_EXPENSE_RATIOS = {"VTI": 0.0003, "VXUS": 0.0007, "BND": 0.0003}
```

---

## Development Workflow

**Per module:**
1. Open a new notebook in `notebooks/`
2. Explore the data, try things, make charts, leave notes as Markdown cells
3. Once the logic works, refactor into `analysis/<module>.py`
4. Commit the notebook and the module together in one PR
5. PR description: what you built, what the AI suggested, what you changed, what you learned

**Branch strategy:**
- `main` — stable, demo-ready
- `feature/module-1-data-ingestion`, etc. — one branch per module
- Squash merge each module PR

**Git hygiene:**
- `data/raw/` in `.gitignore` (no raw CSVs committed)
- `notebooks/` committed (part of the portfolio artifact)
- Each commit message: imperative, specific (e.g. `Add annualized return calculation to returns module`)

---

## Stretch Goals (post-MVP)

- **Monte Carlo simulation** — project portfolio value distributions forward using historical return/volatility parameters
- **Sharpe ratio and volatility metrics** — standard risk-adjusted return stats
- **Benchmark comparison** — always show S&P 500 (SPY) as a reference line
- **Export** — download charts as PNG, download portfolio data as CSV
- **Deployment** — host on Railway, Render, or Fly.io as a public URL

---

## Learning Checkpoints

At the end of each module, you should be able to answer:

| Module | Checkpoint question |
|---|---|
| 1 | What is a pandas DataFrame and how is it different from a 2D NumPy array? |
| 2 | Why would you use log returns instead of simple returns? |
| 3 | What does NumPy broadcasting mean, and where did you use it? |
| 4 | What does `.resample('YE')` do and why is it useful for financial data? |
| 5 | How does compounding make a 1% expense ratio so costly over 30 years? |
| 6 | What is a Dash callback and how does it connect a UI component to a function? |

---

## References

- [Bogleheads Wiki](https://www.bogleheads.org/wiki/Main_Page)
- [yfinance docs](https://yfinance-download-market-data-from-yahoo.readthedocs.io/)
- [pandas User Guide](https://pandas.pydata.org/docs/user_guide/index.html)
- [NumPy fundamentals](https://numpy.org/doc/stable/user/basics.html)
- [Dash documentation](https://dash.plotly.com/)
- [Plotly Python docs](https://plotly.com/python/)
