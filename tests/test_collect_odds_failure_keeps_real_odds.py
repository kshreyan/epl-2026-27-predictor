"""A failed Odds API call (deactivated key, exhausted credits) must never
overwrite a league's last real odds with unavailable sentinels -- the
2026-11-22 run did exactly that to every league -- and must exit
non-zero so the workflow records it."""
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.data_collection import collect_odds  # noqa: E402

REAL_FIXTURES = REPO_ROOT / "data" / "raw" / "epl_2026_27_fixtures.csv"
pytestmark = pytest.mark.skipif(not REAL_FIXTURES.exists(), reason="requires real EPL fixtures")


@pytest.fixture
def fake_repo(tmp_path, monkeypatch):
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    shutil.copy(REAL_FIXTURES, raw / REAL_FIXTURES.name)
    monkeypatch.setattr(collect_odds, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(collect_odds, "ODDS_API_KEY", "test-key")
    monkeypatch.setattr(collect_odds, "fetch_real_odds", lambda *a, **k: ({}, "HTTP 401: API key is deactivated"))
    monkeypatch.setattr(collect_odds, "log_data_version", lambda **k: None)
    return raw / "epl_2026_27_real_odds.csv"


def test_failed_fetch_keeps_existing_real_odds_and_exits_nonzero(fake_repo):
    header = ",".join(collect_odds.OUTPUT_COLUMNS)
    row = {c: "" for c in collect_odds.OUTPUT_COLUMNS}
    row.update(match_id="EPL_TEST", is_real_data="True", data_status="live", current_home_odds="1.9")
    original = header + "\n" + ",".join(row[c] for c in collect_odds.OUTPUT_COLUMNS) + "\n"
    fake_repo.write_text(original)

    with pytest.raises(SystemExit) as exc:
        collect_odds.main("epl")
    assert exc.value.code == collect_odds.ODDS_FETCH_FAILED_EXIT_CODE
    assert fake_repo.read_text() == original


def test_failed_fetch_with_no_earlier_real_odds_writes_sentinels_and_exits_nonzero(fake_repo):
    with pytest.raises(SystemExit) as exc:
        collect_odds.main("epl")
    assert exc.value.code == collect_odds.ODDS_FETCH_FAILED_EXIT_CODE
    text = fake_repo.read_text()
    assert "API request failed: HTTP 401" in text
    assert ",True," not in text.replace("is_real_data", "")
