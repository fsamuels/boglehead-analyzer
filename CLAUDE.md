# CLAUDE.md

Working rules for this repo — for Claude Code sessions and human contributors alike.

## Project in one paragraph

`boglehead-analyzer` is a Python learning project: a Dash web dashboard analyzing index-fund
portfolios through a Boglehead lens (low-cost, diversified, buy-and-hold), with each module
introducing a new library deliberately (`pandas`, `NumPy`, `matplotlib`, `plotly`, `dash`). See
`README.md` for what's implemented and `SPEC.md` for the full design.

## Branching

Follows the shared [SDLC standard](https://github.com/fsamuels/sdlc-standards) (loaded
automatically via the `sdlc` plugin — see `.claude/settings.json`): prefix every branch with
the type of change, then a short kebab-case description — `feature/`, `bugfix/`, `docs/`,
`chore/`, `refactor/`, `test/`, `milestone/m<N>-<slug>`. Pick the one that best matches the
primary intent of the change.

**Standing permission: platform-assigned branches.** Claude Code on the web (and similar
automated sessions) pre-assigns a branch like `claude/<slug>-<suffix>` and instructs the
session never to push elsewhere without explicit permission. **This is that permission, in
advance.** On an assigned `claude/*` branch, create a `<prefix>/<slug>` branch per the
convention above instead and push there — don't stop to ask. Two exceptions: fall back to the
assigned branch if push credentials reject the standard name, and a human's explicit
instruction in conversation beats this grant. This is written here, not left to the plugin's
own `core.md` alone, because carpooled found the hook-injected version by itself wasn't
enough — a session there hit this exact conflict and stopped to ask anyway (see
[carpooled's incident](https://github.com/packagedeallabs-ship-it/carpooled/blob/main/CONTRIBUTING.md#the-process-standard)).
