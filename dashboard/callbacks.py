"""Module 6 — Dashboard callbacks.

Reactive logic connecting UI components to the analysis modules. Keep callbacks
thin: call into ``analysis/``, do not duplicate math here. See SPEC.md.
"""

from __future__ import annotations


def register_callbacks(app) -> None:
    """Register all Dash callbacks on the given app."""
    raise NotImplementedError
