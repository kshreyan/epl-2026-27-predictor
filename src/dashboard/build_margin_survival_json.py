"""Builds the +2 Margin Survival dashboard JSON: one per-league file
(data/outputs/dashboard/{league}_margin_survival.json, EVERY team in
EVERY match -- no eligibility filter) plus a combined cross-league
leaderboard (top20_margin_survival.json) of the best real PICK +2 /
LEAN +2 candidates.

Covers the 5 domestic leagues with a real, backtested, PRIMARY Dixon-
Coles fit (see src/models/compute_margin_survival.py's module
docstring) plus UCL/UEL/UECL (see compute_margin_survival_continental.py's
module docstring) -- built on request even though those three
competitions' own real backtest found Dixon-Coles clearly weaker than
Elo, their actual moneyline model; every row for those three says so
plainly in engine_note/why_text. Every row carries a `verdict` (PICK
+2 / LEAN +2 / PASS) that combines absolute blowout risk with real
market price where one exists -- most fixtures have no real market
posted yet (bookmakers only post close to kickoff), so most verdicts
are risk-tier only; `real_line`/`real_odds`/`value_gap` are null
rather than estimated whenever no real market exists for that
fixture.

Run: python -m src.dashboard.build_margin_survival_json
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.dashboard.build_dashboard_json import _to_records, _write_json  # noqa: E402
from src.leagues import load_league_config  # noqa: E402
from src.models.compute_margin_survival import MARGIN_SURVIVAL_LEAGUE_IDS  # noqa: E402
from src.models.compute_margin_survival_team_sport import MARGIN_THRESHOLD  # noqa: E402
from src.models.point_margin_model import should_use_point_margin_model  # noqa: E402
from src.utils.versioning import MODEL_VERSION, now_utc_iso  # noqa: E402

OUT_DIR = REPO_ROOT / "data" / "outputs"
TOP20_SIZE = 20

# UCL/UEL/UECL (see compute_margin_survival_continental.py's module
# docstring): built on request despite the real backtest finding Elo
# clearly beats Dixon-Coles for all three competitions' own moneyline
# prediction -- unlike the 5 domestic leagues above, the Dixon-Coles
# surface this reads from is NOT this league's primary/best-validated
# model, just the weaker of two real models tested. engine_note below
# is written per-league so this distinction is never glossed over.
CONTINENTAL_CUP_MARGIN_SURVIVAL_LEAGUE_IDS = ["ucl", "uel", "uecl"]

# NFL/NBA/NHL/NCAA Football (see compute_margin_survival_team_sport.py's
# module docstring): a sport-correct equivalent, not soccer's "+2
# goals" ported literally -- each league's own real threshold is
# anchored to its own real research/backtested margin distribution,
# never a borrowed number (see that module's docstring for the real
# per-league reasoning).
TEAM_SPORT_MARGIN_SURVIVAL_LEAGUE_IDS = ["nfl", "nba", "nhl", "ncaaf"]


QUARTILE_FRACTION = 0.25  # "top"/"bottom" of a real current table, for the Pick Moneyline signal below


def _live_predictions(league_id: str) -> pd.DataFrame:
    """data/outputs/{league}_2026_27_match_predictions.csv, indexed by
    match_id -- this is the one file in each league's pipeline that is
    reliably kept in sync with real results (status flips to
    "completed" and actual_home_goals/actual_away_goals get filled in
    as real games conclude). The raw per-sport fixtures.csv that
    compute_margin_survival_team_sport.py reads its own "status"/"date"
    columns from is NOT reliably updated this way for the 4 points-
    format team sports -- confirmed directly this session: NCAA
    Football's raw fixtures.csv still marks literally every one of its
    761 rows "scheduled", including ones from Week 1 (early September)
    that have obviously already been played by late October. Anything
    that needs to know whether a match has REALLY already happened
    must use this file, never margin_survival's own status/date."""
    path = OUT_DIR / f"{league_id}_2026_27_match_predictions.csv"
    if not path.exists():
        return pd.DataFrame(columns=["status", "date", "home_team", "away_team", "actual_home_goals", "actual_away_goals"])
    return pd.read_csv(path).set_index("match_id")


def _real_current_standings(preds: pd.DataFrame, league_id: str) -> pd.DataFrame:
    """Real current-season table built directly from this league's own
    real completed results (status == "completed",
    actual_home_goals/actual_away_goals) in `preds` (see
    _live_predictions above) -- the same already-collected real data
    (football-data.co.uk / ESPN / nflverse / NHL api-web, per league)
    this entire pipeline already treats as authoritative, never a
    separate external standings lookup. Ranked by points-per-game
    (goal-difference tiebreak) for single_table/swiss leagues, win
    percentage (point-diff tiebreak) for the 4 points-format team
    sports -- mid-season-fair either way, not raw totals, so a team
    that has simply played fewer games isn't penalized for it."""
    if preds.empty:
        return pd.DataFrame(columns=["team", "rank", "n_teams", "played"])
    completed = preds[preds["status"] == "completed"].dropna(subset=["actual_home_goals", "actual_away_goals"])

    stats: dict[str, dict] = {}

    def bump(team: str, gf: float, ga: float) -> None:
        s = stats.setdefault(team, {"played": 0, "wins": 0, "points": 0, "diff": 0.0})
        s["played"] += 1
        s["diff"] += gf - ga
        if gf > ga:
            s["wins"] += 1
            s["points"] += 3
        elif gf == ga:
            s["points"] += 1

    for _, row in completed.iterrows():
        bump(row["home_team"], row["actual_home_goals"], row["actual_away_goals"])
        bump(row["away_team"], row["actual_away_goals"], row["actual_home_goals"])

    is_points_format = league_id in TEAM_SPORT_MARGIN_SURVIVAL_LEAGUE_IDS
    rows = [
        {
            "team": team,
            "sort_key": (s["wins"] / s["played"] if is_points_format else s["points"] / s["played"]),
            "diff": s["diff"],
            "played": s["played"],
        }
        for team, s in stats.items()
    ]
    table = pd.DataFrame(rows).sort_values(["sort_key", "diff"], ascending=False).reset_index(drop=True)
    table["rank"] = table.index + 1
    table["n_teams"] = len(table)
    return table


def _table_position(table: pd.DataFrame, team: str) -> str | None:
    """"top"/"bottom"/"mid", or None for a team with no real games
    played yet this season (never guessed)."""
    row = table[table["team"] == team] if not table.empty else table
    if row.empty or row.iloc[0]["played"] == 0:
        return None
    rank, n = int(row.iloc[0]["rank"]), int(row.iloc[0]["n_teams"])
    quartile = max(1, round(n * QUARTILE_FRACTION))
    if rank <= quartile:
        return "top"
    if rank > n - quartile:
        return "bottom"
    return "mid"


def _parse_own_score(predicted_score_model_only, is_home: bool) -> tuple[int, int] | None:
    """predicted_score_model_only is stored home-away, the same string
    for both team rows of a match -- split into (this team's own
    score, opponent's own score)."""
    if not isinstance(predicted_score_model_only, str) or "-" not in predicted_score_model_only:
        return None
    h, a = (int(x) for x in predicted_score_model_only.split("-"))
    return (h, a) if is_home else (a, h)


def _flag_pick_moneyline(df: pd.DataFrame, table: pd.DataFrame, preds: pd.DataFrame) -> pd.Series:
    """True on a team's own row exactly when, for the NEXT real
    upcoming round/slate in this league: that team has a real ELITE
    SURVIVAL PICK verdict, its opponent in that same match is HIGH
    BLOWOUT RISK, this team's own predicted score beats the opponent's
    own predicted score, AND the real current standings (see
    _real_current_standings above) place this team in the real top
    quartile and the opponent in the real bottom quartile. A genuine
    convergence of model risk tier, model scoreline, and real external
    league position -- any one of those alone does not set the flag.

    "Next round" is read from `preds` (the live-tracked predictions
    file), NOT from df's own status/matchweek -- see _live_predictions'
    docstring for why those can be stale for the 4 points-format team
    sports."""
    flags = pd.Series(False, index=df.index)
    if preds.empty:
        return flags
    live_status = df["match_id"].map(preds["status"])
    live_matchweek = df["match_id"].map(preds["matchweek"])
    scheduled = df[live_status == "scheduled"]
    if scheduled.empty or table.empty:
        return flags
    next_mw = live_matchweek.loc[scheduled.index].min()
    next_round = scheduled[live_matchweek.loc[scheduled.index] == next_mw]

    for match_id, grp in next_round.groupby("match_id"):
        if len(grp) != 2:
            continue
        blowout = grp[grp["risk_label"] == "HIGH BLOWOUT RISK"]
        elite = grp[(grp["risk_label"] == "ELITE SURVIVAL") & (grp["verdict"].str.startswith("PICK", na=False))]
        if blowout.empty or elite.empty:
            continue
        b_idx, e_idx = blowout.index[0], elite.index[0]
        if b_idx == e_idx:
            continue
        b, e = df.loc[b_idx], df.loc[e_idx]

        b_score = _parse_own_score(b["predicted_score_model_only"], bool(b["is_home"]))
        e_score = _parse_own_score(e["predicted_score_model_only"], bool(e["is_home"]))
        if b_score is None or e_score is None or not (b_score[0] < e_score[0]):
            continue

        if _table_position(table, e["team"]) == "top" and _table_position(table, b["team"]) == "bottom":
            flags.loc[e_idx] = True
    return flags


def _confidence(row: pd.Series) -> str:
    team_n, opponent_n = row.get("team_history_n_matches"), row.get("opponent_history_n_matches")
    # NFL/NBA/NHL/NCAA Football margin survival (compute_margin_survival_
    # team_sport.py) does not compute a real historical-tail factor
    # (team_history_n_matches/opponent_history_n_matches are always
    # null for these leagues -- a real, disclosed limitation, not a
    # bug). .get() treats a missing column the same honest way as a
    # null one. "low" is the honest answer either way, not a crash.
    if pd.isna(team_n) or pd.isna(opponent_n):
        return "low"
    n_min = min(team_n, opponent_n)
    if n_min >= 20:
        return "high"
    if n_min >= 10:
        return "moderate"
    return "low"


def build_league_margin_survival_json(league_id: str) -> pd.DataFrame:
    path = OUT_DIR / f"{league_id}_2026_27_margin_survival.csv"
    if not path.exists():
        _write_json(f"{league_id}_margin_survival.json", {
            "league": league_id, "generated_at": now_utc_iso(), "model_version": MODEL_VERSION,
            "season": "2026-27", "record_count": 0, "data": [],
            "status": "not_yet_available",
            "note": "No margin-survival predictions yet -- run compute_margin_survival.py first.",
        })
        return pd.DataFrame()

    df = pd.read_csv(path)
    df["data_confidence"] = df.apply(_confidence, axis=1)
    live_preds = _live_predictions(league_id)
    df["pick_moneyline"] = _flag_pick_moneyline(df, _real_current_standings(live_preds, league_id), live_preds)

    tally = df["verdict"].value_counts().to_dict()
    if league_id in CONTINENTAL_CUP_MARGIN_SURVIVAL_LEAGUE_IDS:
        engine_note = (
            "Every team in every match, every round: P_cover/P_push/P_fail read directly off this "
            "competition's own separately-fit Dixon-Coles score matrix -- NOT the same model as this "
            f"competition's moneyline prediction, which is Elo-only (the real backtest found Elo clearly "
            f"beats Dixon-Coles here -- see reports/{league_id}_model_selection_report.md). Treat these "
            "verdicts with real caution. Each row's verdict (PICK +2 / LEAN +2 / PASS) gates on absolute "
            "blowout risk first, then breaks ties with real market price where one currently exists."
        )
    elif league_id in TEAM_SPORT_MARGIN_SURVIVAL_LEAGUE_IDS:
        threshold = MARGIN_THRESHOLD[league_id]
        same_model_note = (
            "the same point-margin model used for this league's own moneyline prediction"
            if should_use_point_margin_model(league_id) else
            "NOT the same model as this league's moneyline prediction, which is Elo-only -- the real backtest "
            f"found Elo beats the point-margin model here (see reports/{league_id}_model_selection_report.md). "
            "Treat these verdicts with real caution"
        )
        engine_note = (
            f"Every team in every game: P_cover/P_push/P_fail read off a real fitted Normal margin "
            f"distribution (not a discrete scoreline grid -- there isn't one for this model), at this "
            f"league's own real blowout threshold (lose by more than {threshold} points) -- see "
            f"reports/{league_id}_model_selection_report.md for how that threshold was derived. Uses "
            f"{same_model_note}. Each row's verdict (PICK +{threshold} / LEAN +{threshold} / PASS) gates on "
            "absolute blowout risk first, then breaks ties with real market price where one currently exists."
        )
    else:
        engine_note = (
            "Every team in every match, every gameweek: P_cover/P_push/P_fail read directly off the same "
            "backtested Dixon-Coles score matrix used for this league's own moneyline predictions -- "
            "not a separate multi-model ensemble. Each row's verdict (PICK +2 / LEAN +2 / PASS) gates on "
            "absolute blowout risk first, then breaks ties with real market price where one currently exists "
            "(most fixtures have none yet -- bookmakers only post close to kickoff)."
        )
    payload = {
        "league": league_id, "generated_at": now_utc_iso(), "model_version": MODEL_VERSION,
        "season": "2026-27", "record_count": len(df),
        "verdict_tally": tally,
        "pick_moneyline_count": int(df["pick_moneyline"].sum()),
        "engine_note": engine_note,
        "data": _to_records(df),
    }
    _write_json(f"{league_id}_margin_survival.json", payload)
    return df


def _verdict_rank(verdict: str) -> int:
    """Ranks by verdict TIER, not the exact string -- "PICK +2" (soccer),
    "PICK +14" (NFL), and "PICK +20" (NBA) are all the same tier here,
    just at each league's own real tag (see
    compute_margin_survival.py's verdict())."""
    if verdict.startswith("PICK "):
        return 0
    if verdict.startswith("LEAN "):
        return 1
    return 2


def build_top20(all_leagues: dict[str, pd.DataFrame]) -> None:
    frames = []
    for league_id, df in all_leagues.items():
        if df.empty:
            continue
        upcoming = df[df["status"] != "completed"].copy()
        upcoming["league_display_name"] = load_league_config(league_id).display_name
        frames.append(upcoming)

    if not frames:
        _write_json("top20_margin_survival.json", {
            "generated_at": now_utc_iso(), "model_version": MODEL_VERSION, "season": "2026-27",
            "view": "best_verdict", "record_count": 0, "data": [],
            "note": "No upcoming fixtures across the covered leagues yet.",
        })
        return

    combined = pd.concat(frames, ignore_index=True)
    combined = combined[combined["verdict"] != "PASS"].copy()
    combined["verdict_rank"] = combined["verdict"].map(_verdict_rank)
    # Within a verdict tier, real price value breaks ties (best value first);
    # rows with no real market (value_gap null) sort after ones that do,
    # then by lowest p_fail -- never let "no price to compare" outrank a
    # fixture that actually has one.
    combined["has_value_gap"] = combined["value_gap"].notna()
    combined = combined.sort_values(
        by=["verdict_rank", "has_value_gap", "value_gap", "p_fail"],
        ascending=[True, False, False, True],
    ).head(TOP20_SIZE).reset_index(drop=True)
    combined = combined.drop(columns=["verdict_rank", "has_value_gap"])
    combined.insert(0, "rank", combined.index + 1)

    payload = {
        "generated_at": now_utc_iso(), "model_version": MODEL_VERSION, "season": "2026-27",
        "view": "best_verdict",
        "note": (
            "Ranked by verdict first (Pick before Lean -- Pass is excluded here), then by real price "
            "value where a real market exists, then by lowest blowout risk. Each league's own verdict is at "
            "its own real threshold (+2 goals for soccer/UEFA, +14 points for NFL, +20 for NBA, +3 for NHL, "
            "+21 for NCAA Football -- see each row's own `threshold` field). The verdict pill on each row "
            "already synthesizes risk and price -- this is not a separate signal, and still not advice."
        ),
        "record_count": len(combined),
        "data": _to_records(combined),
    }
    _write_json("top20_margin_survival.json", payload)


def build_pick_moneyline_board(all_leagues: dict[str, pd.DataFrame]) -> None:
    """Cross-league spotlight list of every row _flag_pick_moneyline()
    set True, scoped to each league's own next scheduled round/slate
    (see that function's docstring) -- the compound signal from this
    session's request: an ELITE SURVIVAL real PICK verdict, a HIGH
    BLOWOUT RISK opponent, a better own predicted scoreline, and a real
    top-quartile-vs-bottom-quartile current-standings gap, all at once."""
    frames = []
    for league_id, df in all_leagues.items():
        if df.empty or "pick_moneyline" not in df.columns:
            continue
        hits = df[df["pick_moneyline"]].copy()
        if hits.empty:
            continue
        hits["league_display_name"] = load_league_config(league_id).display_name
        frames.append(hits)

    if not frames:
        _write_json("pick_moneyline.json", {
            "generated_at": now_utc_iso(), "model_version": MODEL_VERSION, "season": "2026-27",
            "record_count": 0, "data": [],
            "note": (
                "No match in the next scheduled round/slate of any covered league currently has this "
                "compound signal: a real ELITE SURVIVAL PICK verdict, a HIGH BLOWOUT RISK opponent, a "
                "better own predicted scoreline, and a real top-quartile-vs-bottom-quartile gap in the "
                "current real standings, all at once."
            ),
        })
        return

    combined = pd.concat(frames, ignore_index=True).sort_values("date").reset_index(drop=True)
    payload = {
        "generated_at": now_utc_iso(), "model_version": MODEL_VERSION, "season": "2026-27",
        "note": (
            "Each row is the FAVORED team in a match where, for the next scheduled round/slate in its "
            "league: this team has a real ELITE SURVIVAL PICK verdict, its opponent is HIGH BLOWOUT RISK, "
            "this team's own predicted scoreline is higher, and the real current league standings "
            "(computed directly from this season's own real completed results) place this team in the "
            "real top quartile and its opponent in the real bottom quartile. A convergence signal across "
            "risk tier, model scoreline, and real external league position -- not advice, and not a guarantee."
        ),
        "record_count": len(combined),
        "data": _to_records(combined),
    }
    _write_json("pick_moneyline.json", payload)


def main() -> None:
    all_leagues = {
        lid: build_league_margin_survival_json(lid)
        for lid in MARGIN_SURVIVAL_LEAGUE_IDS + CONTINENTAL_CUP_MARGIN_SURVIVAL_LEAGUE_IDS + TEAM_SPORT_MARGIN_SURVIVAL_LEAGUE_IDS
    }
    build_top20(all_leagues)
    build_pick_moneyline_board(all_leagues)


if __name__ == "__main__":
    main()
