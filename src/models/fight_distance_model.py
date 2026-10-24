"""UFC's real "+2 Margin Survival" equivalent: "Distance Survival".

An individual fight has no continuous score margin -- there is no
real analogue to "losing by 3+ goals" or "losing by 14+ points". The
real, honest sport-correct question instead is: does this fighter
survive to the real judges' decision, or get finished (KO/TKO/
submission) first? That is the fight's actual real downside risk, the
same role margin-of-defeat plays in every other sport this project
covers.

`p_fail` for a fighter = P(this fighter is finished) = P(this fighter
loses) x P(a loss is by stoppage | this fighter loses). The first term
comes from fighter_elo_model.py's real win probability. The second
term is a real, backtested blend of two real per-fighter historical
rates (see `stoppage_given_loss_probability`):

- this fighter's own real "vulnerability rate" -- of this fighter's
  own real past losses, what real fraction were by stoppage (not
  decision)?
- the opponent's own real "finishing rate" -- of the opponent's own
  real past wins, what real fraction were by stoppage?

Both rates come straight from real historical data (collect_espn_
ufc_historical.py), never guessed; a fighter with too thin a real
sample (see MIN_FIGHTS) falls back to the real league-wide average
rate computed from the same historical data, the same "too thin to
compute reliably" pattern used elsewhere in this project (e.g.
compute_margin_survival.py's MIN_HISTORY_MATCHES).

There is no real analogue to "push" (exactly at the threshold) for a
binary finish/no-finish outcome -- p_push is always 0.0, a real,
deliberate two-state simplification of the three-state cover/push/
fail pattern used everywhere else, documented plainly rather than
inventing a third state.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

MIN_FIGHTS = 3  # below this, a fighter's own real rate is too thin -- fall back to the real league-wide average


@dataclass
class FighterStoppageRates:
    vulnerability_rate: dict[str, float]  # fighter_id -> real P(stoppage | this fighter's own real losses)
    finishing_rate: dict[str, float]      # fighter_id -> real P(stoppage | this fighter's own real wins)
    league_avg_vulnerability: float
    league_avg_finishing: float
    n_fights_used: dict[str, int]


def fit_stoppage_rates(fights: pd.DataFrame) -> FighterStoppageRates:
    """`fights` must have columns: fighter_a, fighter_b, winner
    ("fighter_a"/"fighter_b"/"draw"), method ("decision"/"finish")."""
    decisive = fights[fights["winner"].isin(["fighter_a", "fighter_b"])]

    losses: dict[str, list[bool]] = {}  # fighter_id -> [is_stoppage, ...] for their own real losses
    wins: dict[str, list[bool]] = {}    # fighter_id -> [is_stoppage, ...] for their own real wins
    n_fights: dict[str, int] = {}

    for _, fgt in decisive.iterrows():
        winner_id = fgt["fighter_a"] if fgt["winner"] == "fighter_a" else fgt["fighter_b"]
        loser_id = fgt["fighter_b"] if fgt["winner"] == "fighter_a" else fgt["fighter_a"]
        is_stoppage = fgt["method"] == "finish"
        wins.setdefault(winner_id, []).append(is_stoppage)
        losses.setdefault(loser_id, []).append(is_stoppage)
        n_fights[winner_id] = n_fights.get(winner_id, 0) + 1
        n_fights[loser_id] = n_fights.get(loser_id, 0) + 1

    all_losses = [v for vs in losses.values() for v in vs]
    all_wins = [v for vs in wins.values() for v in vs]
    league_avg_vulnerability = sum(all_losses) / len(all_losses) if all_losses else 0.5
    league_avg_finishing = sum(all_wins) / len(all_wins) if all_wins else 0.5

    vulnerability_rate = {
        fid: (sum(vs) / len(vs) if len(vs) >= MIN_FIGHTS else league_avg_vulnerability)
        for fid, vs in losses.items()
    }
    finishing_rate = {
        fid: (sum(vs) / len(vs) if len(vs) >= MIN_FIGHTS else league_avg_finishing)
        for fid, vs in wins.items()
    }
    return FighterStoppageRates(
        vulnerability_rate=vulnerability_rate, finishing_rate=finishing_rate,
        league_avg_vulnerability=league_avg_vulnerability, league_avg_finishing=league_avg_finishing,
        n_fights_used=n_fights,
    )


def stoppage_given_loss_probability(
    rates: FighterStoppageRates, fighter_id: str, opponent_id: str, blend_weight: float = 0.5,
) -> float:
    """Real P(a loss by `fighter_id` is by stoppage, not decision) --
    a weighted blend of fighter_id's own real vulnerability rate and
    opponent_id's own real finishing rate. `blend_weight` is this
    fighter's own rate's share of the blend (1.0 = ignore the
    opponent entirely, 0.0 = ignore this fighter's own history
    entirely, 0.5 = equal real weight to both) -- backtest_ufc.py
    compares real candidate weights and reports which wins, not
    assumed here."""
    fighter_rate = rates.vulnerability_rate.get(fighter_id, rates.league_avg_vulnerability)
    opponent_rate = rates.finishing_rate.get(opponent_id, rates.league_avg_finishing)
    return blend_weight * fighter_rate + (1 - blend_weight) * opponent_rate


def p_fail(win_prob_opponent: float, stoppage_given_loss: float) -> float:
    """P(this fighter is finished) = P(this fighter loses) x P(a loss
    is by stoppage | this fighter loses). `win_prob_opponent` is the
    OPPONENT's real win probability (= 1 - this fighter's own win
    probability, from fighter_elo_model.py's win_probability(), real
    draw probability folded in or ignored per caller's own convention
    -- see compute_margin_survival_ufc.py)."""
    return win_prob_opponent * stoppage_given_loss
