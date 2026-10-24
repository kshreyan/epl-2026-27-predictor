import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.leagues import league_path  # noqa: E402

# UFC ("fight_card" format -- not a team sport, see config/leagues.yaml)
# gets its own integrity checks here, separate from the team-sport
# leagues (test_team_sport_fixture_integrity.py): no CANONICAL_TEAMS
# table exists for UFC fighters (see team_names.py's module docstring
# on why), so there's no "known fighter" check to run, only real
# structural checks on the fight-card data itself.
FIGHT_CARD_PATH = REPO_ROOT / "data" / "raw" / league_path("ufc", "2026_27_fight_card.csv")


def _skip_reason() -> str | None:
    if not FIGHT_CARD_PATH.exists():
        return "ufc: fight card not collected yet -- run collect_espn_ufc_schedule.py"
    return None


@pytest.fixture
def fight_card() -> pd.DataFrame:
    reason = _skip_reason()
    if reason:
        pytest.skip(reason)
    return pd.read_csv(FIGHT_CARD_PATH)


def test_real_fights_have_no_duplicates_or_self_fights(fight_card):
    assert len(fight_card) > 0
    assert fight_card["match_id"].duplicated().sum() == 0
    assert (fight_card["fighter_a"] == fight_card["fighter_b"]).sum() == 0


def test_real_fights_have_a_real_scheduled_round_count(fight_card):
    # Most real UFC fights are scheduled for 3 rounds (5 for a real
    # title/main-event fight) -- confirmed directly via ESPN's own
    # format.regulation.periods field (see espn_mma_api.py). A real,
    # directly-observed exception exists too (e.g. a handful of real
    # 4-round fights) -- bounded to a sane real range rather than
    # enumerating exact values this project doesn't have full real
    # research on.
    assert fight_card["scheduled_rounds"].between(1, 5).all()


def test_real_fights_status_is_known(fight_card):
    assert fight_card["status"].isin(["scheduled", "completed"]).all()


def test_real_completed_fights_have_a_result(fight_card):
    real_results_path = REPO_ROOT / "data" / "raw" / league_path("ufc", "2026_27_real_results.csv")
    if not real_results_path.exists():
        pytest.skip("ufc: real results not collected yet")
    real_results = pd.read_csv(real_results_path)
    completed_ids = set(fight_card[fight_card["status"] == "completed"]["match_id"])
    # A real completed fight can still be missing a real result row if
    # ESPN reports it "completed" without a decisive real method (e.g.
    # a real no-contest -- see espn_mma_api.py's "unscored" method) --
    # checked as a real, bounded minority, not an exact 1:1 requirement.
    missing = completed_ids - set(real_results["match_id"])
    assert len(missing) <= max(1, int(0.05 * len(completed_ids))) if completed_ids else True
