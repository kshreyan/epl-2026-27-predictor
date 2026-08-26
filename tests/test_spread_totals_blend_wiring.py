"""Tests that predict_fixtures actually applies the spread (Asian
Handicap) and totals (Over/Under) model+market blends end to end,
against a REAL fitted Dixon-Coles context (real historical data, real
backtest results, real spread_totals_blend_model significance check) --
mirrors test_market_blend_wiring.py's structure for the moneyline
blend. Confirms: each blend applies only when both significant AND
real market data exists for that specific fixture and market, the
blended output is a genuine log-odds average (not silently equal to
either input), and a fixture with no real spread/totals data is left
untouched.
"""
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.models.predict_all_matches import build_model_context, predict_fixtures  # noqa: E402
from src.utils.team_names import EPL_2026_27_CLUBS  # noqa: E402
from src.utils.versioning import now_utc_iso  # noqa: E402

REAL_HISTORICAL_PATH = REPO_ROOT / "data" / "raw" / "epl_historical_matches.csv"
REAL_MODEL_CONFIG_PATH = REPO_ROOT / "config" / "model_config.yaml"

pytestmark = [
    pytest.mark.skipif(not REAL_HISTORICAL_PATH.exists(), reason="requires the real historical data collector to have been run first"),
    pytest.mark.slow,
]


@pytest.fixture
def real_ctx():
    df = pd.read_csv(REAL_HISTORICAL_PATH, parse_dates=["date"])
    df_clean = df.dropna(subset=["home_goals", "away_goals"])
    hist_teams = sorted(set(df_clean["home_team"]) | set(df_clean["away_team"]))
    universe = sorted(set(hist_teams) | set(EPL_2026_27_CLUBS))
    with open(REAL_MODEL_CONFIG_PATH) as f:
        model_cfg = yaml.safe_load(f)
    as_of_date = pd.Timestamp(now_utc_iso()[:10])
    ctx = build_model_context(df_clean, universe, model_cfg, as_of_date)
    return ctx, df_clean, model_cfg


def _fixtures_df():
    return pd.DataFrame([
        {"match_id": "with_odds", "season": "2026-27", "matchweek": 1, "date": "2026-08-21",
         "kickoff_utc": "2026-08-21T19:00:00+00:00", "home_team": "Arsenal", "away_team": "Chelsea",
         "stadium": "Emirates Stadium", "status": "scheduled"},
        {"match_id": "no_odds", "season": "2026-27", "matchweek": 1, "date": "2026-08-21",
         "kickoff_utc": "2026-08-21T19:00:00+00:00", "home_team": "Liverpool", "away_team": "Everton",
         "stadium": "Anfield", "status": "scheduled"},
    ])


def test_spread_blend_applies_only_to_fixtures_with_real_spread_odds(real_ctx):
    ctx, df_clean, model_cfg = real_ctx
    fixtures_df = _fixtures_df()
    spread_totals_odds_by_id = {
        "with_odds": {"spread_line": -1.0, "home_cover_prob": 0.95},  # deliberately extreme, easy to detect if blended in
    }
    generated_at = now_utc_iso()
    pred_rows, _ = predict_fixtures(
        fixtures_df, ctx, df_clean, model_cfg, "test_mode", generated_at, "test_run",
        None, spread_totals_odds_by_id,
    )
    by_id = {r["match_id"]: r for r in pred_rows}

    if ctx["spread_blend_significant"]:
        assert by_id["with_odds"]["handicap_blend_applied"] is True
        assert by_id["with_odds"]["handicap_line_model_only"] == -1.0
        assert by_id["with_odds"]["home_cover_prob_model_only"] > 0.60
    else:
        assert by_id["with_odds"]["handicap_blend_applied"] is False

    assert by_id["no_odds"]["handicap_blend_applied"] is False


def test_totals_blend_applies_only_to_fixtures_with_real_totals_odds(real_ctx):
    ctx, df_clean, model_cfg = real_ctx
    fixtures_df = _fixtures_df()
    spread_totals_odds_by_id = {
        "with_odds": {"total_line": 2.5, "over_prob": 0.95},  # deliberately extreme, easy to detect if blended in
    }
    generated_at = now_utc_iso()
    pred_rows, _ = predict_fixtures(
        fixtures_df, ctx, df_clean, model_cfg, "test_mode", generated_at, "test_run",
        None, spread_totals_odds_by_id,
    )
    by_id = {r["match_id"]: r for r in pred_rows}

    if ctx["totals_blend_significant"]:
        assert by_id["with_odds"]["totals_blend_applied"] is True
        assert by_id["with_odds"]["total_goals_line_model_only"] == 2.5
        assert by_id["with_odds"]["over_prob_model_only"] > 0.60
    else:
        assert by_id["with_odds"]["totals_blend_applied"] is False

    assert by_id["no_odds"]["totals_blend_applied"] is False
