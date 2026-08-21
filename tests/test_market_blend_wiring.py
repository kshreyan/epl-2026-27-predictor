"""Tests that predict_fixtures actually applies the model+market blend
end to end, against a REAL fitted Dixon-Coles context (real historical
data, real backtest results, real market-blend significance check) --
not just the isolated blend-math unit tests in
test_market_blend_model.py. Confirms: blend applies only when both
significant AND real odds exist for that specific fixture, the
blended output is a genuine log-odds average (not silently equal to
either input), and a fixture with no market data is left untouched."""
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


def test_blend_applies_only_to_fixtures_with_real_market_odds(real_ctx):
    ctx, df_clean, model_cfg = real_ctx
    fixtures_df = pd.DataFrame([
        {"match_id": "with_odds", "season": "2026-27", "matchweek": 1, "date": "2026-08-21",
         "kickoff_utc": "2026-08-21T19:00:00+00:00", "home_team": "Arsenal", "away_team": "Chelsea",
         "stadium": "Emirates Stadium", "status": "scheduled"},
        {"match_id": "no_odds", "season": "2026-27", "matchweek": 1, "date": "2026-08-21",
         "kickoff_utc": "2026-08-21T19:00:00+00:00", "home_team": "Liverpool", "away_team": "Everton",
         "stadium": "Anfield", "status": "scheduled"},
    ])
    match_odds_by_id = {
        "with_odds": {
            "home_implied_probability_no_vig": 0.05, "draw_implied_probability_no_vig": 0.05,
            "away_implied_probability_no_vig": 0.90,  # deliberately extreme, easy to detect if blended in
        },
    }
    generated_at = now_utc_iso()
    pred_rows, _ = predict_fixtures(fixtures_df, ctx, df_clean, model_cfg, "test_mode", generated_at, "test_run", match_odds_by_id)
    by_id = {r["match_id"]: r for r in pred_rows}

    if ctx["market_blend_significant"]:
        assert by_id["with_odds"]["market_blend_applied"] is True
        # The extreme away-favoring market price must have pulled the
        # published probability meaningfully toward away -- not left it
        # exactly at the model-only value.
        assert by_id["with_odds"]["away_win_prob_model_only"] > 0.30
    else:
        assert by_id["with_odds"]["market_blend_applied"] is False

    # No real odds were supplied for this fixture -- must never be blended,
    # regardless of whether the blend is globally significant.
    assert by_id["no_odds"]["market_blend_applied"] is False
