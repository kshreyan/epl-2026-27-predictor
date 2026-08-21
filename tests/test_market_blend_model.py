"""Tests the model+market blend candidate: real historical-odds parsing
(synthetic CSV mirroring football-data.co.uk's real column format,
never a real network call or the real cached files) and the paired-
bootstrap evaluation logic against small synthetic backtest data."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.models.market_blend_model import evaluate_market_blend, load_historical_market_odds  # noqa: E402
from src.utils.team_names import EPL_2026_27_CLUBS  # noqa: E402

REAL_TEAMS = list(EPL_2026_27_CLUBS)  # 20 real, recognized team names for synthetic fixtures


def test_load_historical_market_odds_parses_and_devigs(tmp_path, monkeypatch):
    import src.models.market_blend_model as market_blend_model
    monkeypatch.setattr(market_blend_model, "RAW_CACHE_DIR", tmp_path)
    monkeypatch.setattr(market_blend_model, "SEASON_CODES", {"2025-26": "2526"})

    pd.DataFrame([
        {"Date": "15/08/2025", "HomeTeam": "Arsenal", "AwayTeam": "Chelsea", "AvgH": 2.0, "AvgD": 3.5, "AvgA": 4.0},
    ]).to_csv(tmp_path / "E0_2526.csv", index=False)

    odds = load_historical_market_odds(["2025-26"])
    assert len(odds) == 1
    row = odds.iloc[0]
    assert row["key"] == "2025-08-15_Arsenal_Chelsea"
    total = row["market_home_win"] + row["market_draw"] + row["market_away_win"]
    assert abs(total - 1.0) < 1e-9
    assert row["market_home_win"] > row["market_draw"] > row["market_away_win"]  # shortest odds = highest prob


def test_load_historical_market_odds_raises_on_missing_avg_columns(tmp_path, monkeypatch):
    import src.models.market_blend_model as market_blend_model
    monkeypatch.setattr(market_blend_model, "RAW_CACHE_DIR", tmp_path)
    monkeypatch.setattr(market_blend_model, "SEASON_CODES", {"2025-26": "2526"})

    pd.DataFrame([
        {"Date": "15/08/2025", "HomeTeam": "Arsenal", "AwayTeam": "Chelsea", "AvgH": 2.0, "AvgD": 3.5, "AvgA": None},
    ]).to_csv(tmp_path / "E0_2526.csv", index=False)

    with pytest.raises(ValueError, match="missing Avg odds"):
        load_historical_market_odds(["2025-26"])


def _synthetic_backtest_df(n_per_season=40, seasons=("2019-20", "2020-21"), market_is_more_accurate=True, seed=0):
    """A synthetic backtest_df + matching odds cache: DC is a fixed,
    mediocre 0.5/0.3/0.2 guess every match; the market's odds are
    either genuinely informative (tracks the real outcome closely) or
    just as uninformative as DC, controlling whether the blend SHOULD
    or SHOULDN'T look better."""
    rng = np.random.default_rng(seed)
    rows = []
    for season_idx, season in enumerate(seasons):
        year = 2015 + season_idx  # a different year per season -- keeps (date, home, away) keys globally unique
        for i in range(n_per_season):
            if market_is_more_accurate:
                p_home = 0.75  # market "knows" this team wins most of the time
            else:
                p_home = 0.5  # market knows nothing DC doesn't
            actual = rng.choice(["home_win", "draw", "away_win"], p=[p_home, 0.15, 1 - p_home - 0.15])
            home_team = REAL_TEAMS[i % 20]
            away_team = REAL_TEAMS[(i + 1) % 20]
            month = 1 + (i // 28)
            day = (i % 28) + 1
            rows.append({
                "season": season, "date": f"{year}-{month:02d}-{day:02d}",
                "home_team": home_team, "away_team": away_team,
                "dc_home_win": 0.5, "dc_draw": 0.3, "dc_away_win": 0.2,
                "actual_result": actual,
            })
    return pd.DataFrame(rows)


def _write_matching_odds_cache(tmp_path, backtest_df, market_is_more_accurate, monkeypatch):
    import src.models.market_blend_model as market_blend_model
    monkeypatch.setattr(market_blend_model, "RAW_CACHE_DIR", tmp_path)
    codes = {s: f"{i:04d}" for i, s in enumerate(backtest_df["season"].unique())}
    monkeypatch.setattr(market_blend_model, "SEASON_CODES", codes)

    for season, code in codes.items():
        rows = backtest_df[backtest_df["season"] == season]
        out = []
        for _, r in rows.iterrows():
            date_obj = pd.to_datetime(r["date"])
            date_str = date_obj.strftime("%d/%m/%Y")
            if market_is_more_accurate:
                out.append({"Date": date_str, "HomeTeam": r["home_team"], "AwayTeam": r["away_team"], "AvgH": 1.35, "AvgD": 6.0, "AvgA": 9.0})
            else:
                out.append({"Date": date_str, "HomeTeam": r["home_team"], "AwayTeam": r["away_team"], "AvgH": 2.0, "AvgD": 3.33, "AvgA": 5.0})
        pd.DataFrame(out).to_csv(tmp_path / f"E0_{code}.csv", index=False)


def test_evaluate_market_blend_promotes_when_market_carries_real_signal(tmp_path, monkeypatch):
    backtest_df = _synthetic_backtest_df(n_per_season=60, market_is_more_accurate=True, seed=1)
    _write_matching_odds_cache(tmp_path, backtest_df, market_is_more_accurate=True, monkeypatch=monkeypatch)

    result = evaluate_market_blend(backtest_df)

    assert result["n_dropped"] == 0
    assert result["blend_mean_log_loss"] < result["dc_mean_log_loss"]
    assert result["blend_significant"] is True
    assert result["significance"]["ci_low"] > 0


def test_evaluate_market_blend_does_not_promote_when_market_has_no_edge(tmp_path, monkeypatch):
    backtest_df = _synthetic_backtest_df(n_per_season=60, market_is_more_accurate=False, seed=2)
    _write_matching_odds_cache(tmp_path, backtest_df, market_is_more_accurate=False, monkeypatch=monkeypatch)

    result = evaluate_market_blend(backtest_df)

    assert result["n_dropped"] == 0
    # No real signal for the blend to exploit -- must not be promoted on noise.
    assert result["blend_significant"] is False


def test_evaluate_market_blend_never_estimates_missing_coverage(tmp_path, monkeypatch):
    import src.models.market_blend_model as market_blend_model
    backtest_df = _synthetic_backtest_df(n_per_season=10, seasons=("2019-20",), seed=3)
    monkeypatch.setattr(market_blend_model, "RAW_CACHE_DIR", tmp_path)
    monkeypatch.setattr(market_blend_model, "SEASON_CODES", {"2019-20": "0000"})
    # Only write odds for HALF the matches -- the rest have no real market row.
    rows = backtest_df.iloc[:5]
    out = [{"Date": pd.to_datetime(r["date"]).strftime("%d/%m/%Y"), "HomeTeam": r["home_team"], "AwayTeam": r["away_team"], "AvgH": 2.0, "AvgD": 3.33, "AvgA": 5.0} for _, r in rows.iterrows()]
    pd.DataFrame(out).to_csv(tmp_path / "E0_0000.csv", index=False)

    result = evaluate_market_blend(backtest_df)
    assert result["n_matches"] == 5
    assert result["n_dropped"] == 5
