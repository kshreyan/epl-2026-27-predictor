"""Two additional real de-vig methods alongside the existing
proportional-normalization one (`remove_overround`/
`remove_overround_binary` in build_market_features.py, kept as-is and
still the default everywhere that already used it) -- Shin's method
and the power method, both real, documented techniques for removing a
bookmaker's overround, not invented here.

**Shin's method** (Shin, 1992/1993): models the overround as coming
from a fraction `z` of "insider"/informed money the bookmaker must
protect against, and backs out the fair probabilities implied by that
model. For n raw implied probabilities pi_i = 1/odds_i (summing to
B = 1 + overround > 1), it solves for z in [0, 1) such that

    sum_i [sqrt(z^2 + 4*(1-z)*pi_i^2/B) - z] / (2*(1-z)) == 1

then returns each outcome's fair probability from that same formula.
Solved numerically (scipy.optimize.brentq) for the general n-outcome
case rather than hand-deriving a closed form, which only exists
cleanly for n=2 and is easy to get subtly wrong by hand.

**Power method**: raises each raw implied probability to a single
exponent k and renormalizes, where k is chosen so the exponentiated
probabilities already sum to 1 (no separate renormalization step
needed once the right k is found): solve for k such that
sum_i (1/odds_i)^k == 1, then p_i = (1/odds_i)^k.

Neither method is assumed to beat the existing proportional method for
any given sport/market -- `select_devig_method()` below picks per
sport from a real backtest against real historical closing lines and
real outcomes (see backtest_market_devig.py), the same "never assume,
always check" discipline as every model-selection decision in this
project.
"""
from __future__ import annotations

from scipy.optimize import brentq


def _shin_fair_probs(raw_probs: list[float], z: float) -> list[float]:
    b = sum(raw_probs)
    if z >= 1.0:
        z = 1.0 - 1e-9
    return [(((z**2 + 4 * (1 - z) * p**2 / b) ** 0.5) - z) / (2 * (1 - z)) for p in raw_probs]


def devig_shin(decimal_odds: tuple[float, ...]) -> tuple[float, ...]:
    """Fair (de-vigged) probabilities for an n-outcome market via
    Shin's method. Falls back to simple proportional normalization if
    the real book has (near) zero overround (B <= 1 + 1e-9) -- Shin's
    z-root is only meaningfully defined for a real positive overround,
    and a (near-)fair raw book needs no correction in the first place."""
    raw_probs = [1.0 / o for o in decimal_odds]
    b = sum(raw_probs)
    if b <= 1.0 + 1e-9:
        return tuple(p / b for p in raw_probs)

    def residual(z: float) -> float:
        return sum(_shin_fair_probs(raw_probs, z)) - 1.0

    # z=0 reduces to proportional normalization (residual > 0 since B > 1
    # there is still overround to remove); z just under 1 drives every
    # fair probability toward its own raw share's extreme -- the real
    # root sits inside (0, 1) for any real positive overround.
    z = brentq(residual, 0.0, 1.0 - 1e-9, xtol=1e-10)
    return tuple(_shin_fair_probs(raw_probs, z))


def devig_power(decimal_odds: tuple[float, ...]) -> tuple[float, ...]:
    """Fair (de-vigged) probabilities for an n-outcome market via the
    power method. Falls back to proportional normalization the same
    way devig_shin() does for a (near-)zero-overround book."""
    raw_probs = [1.0 / o for o in decimal_odds]
    b = sum(raw_probs)
    if b <= 1.0 + 1e-9:
        return tuple(p / b for p in raw_probs)

    def residual(k: float) -> float:
        return sum(p**k for p in raw_probs) - 1.0

    # k=1 reproduces the raw (overround-inflated) sum B > 1; a real
    # positive overround always has its root at k > 1 (each raw share
    # shrinks, favorites shrinking less than longshots -- the real,
    # documented "favorite-longshot bias" correction this method is
    # for). Bounded well above 1 is enough for any real bookmaker
    # overround seen in practice (a few percent).
    k = brentq(residual, 1.0, 50.0, xtol=1e-10)
    return tuple(p**k for p in raw_probs)


DEVIG_METHODS = {
    "multiplicative": lambda odds: tuple(
        (1.0 / o) / sum(1.0 / x for x in odds) for o in odds
    ),
    "shin": devig_shin,
    "power": devig_power,
}


def select_devig_method(league_id: str) -> str:
    """This league's own real backtested best de-vig method (see
    backtest_market_devig.py's real comparison report), or
    "multiplicative" (this project's long-standing default) if that
    backtest hasn't been run yet for this league -- never assumed."""
    import sys
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))
    from src.leagues import league_path  # noqa: E402

    import pandas as pd

    path = repo_root / "data" / "outputs" / league_path(league_id, "devig_method_comparison.csv")
    if not path.exists():
        return "multiplicative"
    comparison = pd.read_csv(path).sort_values("log_loss")
    return str(comparison.iloc[0]["method"])
