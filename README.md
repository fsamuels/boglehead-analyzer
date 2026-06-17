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

Run the dashboard (once Module 6 is implemented):

```bash
python -m dashboard.app
```

Explore a module interactively:

```bash
jupyter lab
```

## Status

Scaffolding in place. Modules are being built one at a time, each explored in a
notebook first and then refactored into a clean module — see the per-module PRs.

| Module | Area | Status |
|---|---|---|
| 1 | Data ingestion (`analysis/fetch.py`) | Not started |
| 2 | Return calculations (`analysis/returns.py`) | Not started |
| 3 | Portfolio construction (`analysis/portfolio.py`) | Not started |
| 4 | Rebalancing simulator (`analysis/rebalancing.py`) | Not started |
| 5 | Cost drag analysis (`analysis/costs.py`) | Not started |
| 6 | Dashboard (`dashboard/`) | Not started |

## Disclaimer

This is an educational project. Nothing here is financial advice. It uses
delayed/historical data only and does not place trades.
