"""Module 6 — Dash entry point.

Builds the Dash app, attaches the layout and callbacks, and runs the server.
See SPEC.md for the full module specification.

Run locally with:

    python -m dashboard.app
"""

from __future__ import annotations

from dash import Dash

from dashboard.callbacks import register_callbacks
from dashboard.layout import build_layout


def create_app() -> Dash:
    """Construct and return the configured Dash app."""
    app = Dash(__name__, title="Boglehead Portfolio Analyzer")
    app.layout = build_layout()
    register_callbacks(app)
    return app


def main() -> None:
    """Run the development server on localhost."""
    app = create_app()
    # debug=True is disabled: Dash 2.x's dev-tools reloader calls the
    # long-removed pkgutil.find_loader, which crashes on Python 3.12+.
    app.run(debug=False)


if __name__ == "__main__":
    main()
