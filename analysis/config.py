"""Default configuration for development and demo purposes (see SPEC.md)."""

# Every ticker the analyzer knows about — the universe the dashboard can offer
# for selection. Kept separate from the demo portfolio below so that adding a
# selectable ETF never silently changes the default allocation.
AVAILABLE_TICKERS = ["VTI", "VXUS", "VOO", "VT", "BND"]

# Annual expense ratios (as decimals) for every known ticker. Approximate
# current Vanguard figures; used by the cost-drag module (Module 5).
EXPENSE_RATIOS = {
    "VTI": 0.0003,   # Total US Stock Market
    "VXUS": 0.0007,  # Total International Stock
    "VOO": 0.0003,   # S&P 500
    "VT": 0.0006,    # Total World Stock
    "BND": 0.0003,   # Total US Bond Market
}

DEFAULT_TICKERS = ["VTI", "VXUS", "BND"]
DEFAULT_WEIGHTS = {"VTI": 0.60, "VXUS": 0.30, "BND": 0.10}
DEFAULT_START = "2013-01-01"  # VXUS inception was 2011, gives a few years of buffer
DEFAULT_INVESTMENT = 10000.0

# The demo portfolio's expense ratios, derived from the full table so the two
# never drift out of sync.
DEFAULT_EXPENSE_RATIOS = {t: EXPENSE_RATIOS[t] for t in DEFAULT_TICKERS}
