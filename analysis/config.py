"""Default configuration for development and demo purposes (see SPEC.md)."""

DEFAULT_TICKERS = ["VTI", "VXUS", "BND"]
DEFAULT_WEIGHTS = {"VTI": 0.60, "VXUS": 0.30, "BND": 0.10}
DEFAULT_START = "2013-01-01"  # VXUS inception was 2011, gives a few years of buffer
DEFAULT_INVESTMENT = 10000.0
DEFAULT_EXPENSE_RATIOS = {"VTI": 0.0003, "VXUS": 0.0007, "BND": 0.0003}
