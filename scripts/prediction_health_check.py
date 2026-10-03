"""One-off health audit of every prediction currently served to the live
dashboard (reads data/outputs/dashboard/*_match_predictions.json, the
exact files site/ fetches -- not the older per-phase CSVs that
src/run_integrity_audit.py checks).

Four dimensions, one section each:

1. Internal consistency -- do this prediction's own numbers add up
   (1X2/BTTS/totals/spread probabilities sum to 1, confidence/upset_risk
   agree, predicted_result matches predicted_score, completed matches
   carry a real result and scheduled ones don't).
2. Data freshness & provenance -- is each league's file as current as
   the pipeline's own cadence implies, and are there scheduled matches
   whose kickoff has already passed without a result (a stuck fixture).
3. Calibration / accuracy drift -- for matches with a real result,
   how well did model_only win/draw/loss probabilities perform
   (accuracy, Brier score, high-confidence misses).
4. Pipeline/site operational health -- recent GitHub Actions run
   status (via `gh run list`, best-effort) and whether every league
   expected on the dashboard actually has a predictions file.

Run: python scripts/prediction_health_check.py
Exits non-zero if any check in sections 1/2/4 fails outright (section 3
is observational -- calibration drift is reported, not pass/failed,
since some miscalibration on a small completed-match sample is
expected and not itself a bug).
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD = REPO_ROOT / "data" / "outputs" / "dashboard"
REPORT_PATH = REPO_ROOT / "reports" / "epl_2026_27_prediction_health_report.md"

TOL = 1e-3
findings: list[dict] = []


def flag(section: str, severity: str, league: str, message: str) -> None:
    findings.append({"section": section, "severity": severity, "league": league, "message": message})


def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def sum_ok(row: dict, keys: list[str]) -> bool | None:
    vals = [row.get(k) for k in keys]
    if any(v is None for v in vals):
        return None
    return abs(sum(vals) - 1.0) < TOL


def check_internal_consistency(league: str, rows: list[dict]) -> None:
    bad_1x2 = bad_btts = bad_totals = bad_confidence = bad_result_score = 0
    bad_completed = bad_scheduled = 0
    bad_market_1x2 = 0

    for r in rows:
        ok = sum_ok(r, ["home_win_prob_model_only", "draw_prob_model_only", "away_win_prob_model_only"])
        if ok is False:
            bad_1x2 += 1

        if r.get("market_blend_applied") and r.get("home_win_prob_market_integrated") is not None:
            ok_m = sum_ok(r, ["home_win_prob_market_integrated", "draw_prob_market_integrated", "away_win_prob_market_integrated"])
            if ok_m is False:
                bad_market_1x2 += 1

        ok = sum_ok(r, ["btts_yes_prob_model_only", "btts_no_prob_model_only"])
        if ok is False:
            bad_btts += 1

        ok = sum_ok(r, ["over_prob_model_only", "under_prob_model_only"])
        if ok is False:
            bad_totals += 1

        conf, upset = r.get("confidence"), r.get("upset_risk")
        if conf is not None and upset is not None and abs((conf + upset) - 1.0) > 0.01:
            bad_confidence += 1

        score = r.get("predicted_score_model_only")
        result = r.get("predicted_result_model_only")
        if score and result:
            try:
                hg, ag = (int(x) for x in score.split("-"))
                expected = "home_win" if hg > ag else ("away_win" if hg < ag else "draw")
                if expected != result:
                    bad_result_score += 1
            except ValueError:
                bad_result_score += 1

        if r.get("status") == "completed":
            if r.get("actual_home_goals") is None or r.get("actual_away_goals") is None:
                bad_completed += 1
            else:
                hg, ag = r["actual_home_goals"], r["actual_away_goals"]
                expected = "home_win" if hg > ag else ("away_win" if hg < ag else "draw")
                if r.get("actual_result") != expected:
                    bad_completed += 1
        elif r.get("status") == "scheduled":
            if r.get("actual_home_goals") is not None or r.get("actual_away_goals") is not None:
                bad_scheduled += 1

    any_bad = False
    for label, count in [
        ("model-only 1X2 probabilities don't sum to 1", bad_1x2),
        ("market-integrated 1X2 probabilities don't sum to 1", bad_market_1x2),
        ("BTTS probabilities don't sum to 1", bad_btts),
        ("over/under probabilities don't sum to 1", bad_totals),
        ("confidence + upset_risk != 1", bad_confidence),
        ("predicted_result disagrees with predicted_score", bad_result_score),
        ("completed match missing/inconsistent actual result", bad_completed),
        ("scheduled match already carries an actual result", bad_scheduled),
    ]:
        if count:
            any_bad = True
            flag("1. Internal consistency", "FAIL", league, f"{count}/{len(rows)} rows: {label}")
    if not any_bad:
        flag("1. Internal consistency", "INFO", league, f"all {len(rows)} rows pass every consistency check (probability sums, score/result agreement, completed/scheduled result presence)")


def check_freshness(league: str, payload: dict, rows: list[dict], now: datetime) -> None:
    generated_at = parse_iso(payload["generated_at"])
    age_hours = (now - generated_at).total_seconds() / 3600
    if age_hours > 48:
        flag("2. Freshness & provenance", "WARN", league, f"dashboard file generated_at is {age_hours:.0f}h old ({payload['generated_at']})")

    stuck = []
    for r in rows:
        if r.get("status") == "scheduled" and r.get("kickoff_utc"):
            if parse_iso(r["kickoff_utc"]) < now:
                stuck.append(r["match_id"])
    if stuck:
        flag(
            "2. Freshness & provenance",
            "FAIL",
            league,
            f"{len(stuck)} match(es) still 'scheduled' with kickoff already in the past (pipeline hasn't picked up the result): "
            + ", ".join(stuck[:5]) + (" ..." if len(stuck) > 5 else ""),
        )

    inconsistent_market_flag = sum(
        1 for r in rows
        if r.get("market_available") and r.get("home_win_prob_market_integrated") is None and r.get("market_blend_applied")
    )
    if inconsistent_market_flag:
        flag(
            "2. Freshness & provenance", "WARN", league,
            f"{inconsistent_market_flag} row(s) flag market_available=True + market_blend_applied=True but have no market-integrated probabilities",
        )


def check_calibration(league: str, rows: list[dict]) -> None:
    completed = [r for r in rows if r.get("status") == "completed" and r.get("actual_result")]
    if not completed:
        flag("3. Calibration / accuracy drift", "INFO", league, "no completed matches yet -- nothing to score")
        return

    outcomes = ["home_win", "draw", "away_win"]
    prob_keys = {"home_win": "home_win_prob_model_only", "draw": "draw_prob_model_only", "away_win": "away_win_prob_model_only"}

    correct = 0
    brier_sum = 0.0
    high_conf_misses = []
    skipped = 0

    for r in completed:
        probs = {o: r.get(prob_keys[o]) for o in outcomes}
        if any(v is None for v in probs.values()):
            skipped += 1
            continue
        predicted = max(probs, key=probs.get)
        actual = r["actual_result"]
        if predicted == actual:
            correct += 1
        brier_sum += sum((probs[o] - (1.0 if o == actual else 0.0)) ** 2 for o in outcomes)
        if probs[predicted] >= 0.7 and predicted != actual:
            high_conf_misses.append((r["match_id"], predicted, actual, probs[predicted]))

    n = len(completed) - skipped
    if n == 0:
        flag("3. Calibration / accuracy drift", "WARN", league, f"{len(completed)} completed matches but none had usable win-probability fields to score")
        return
    accuracy = correct / n
    brier = brier_sum / n
    skip_note = f", {skipped} skipped (missing probabilities)" if skipped else ""
    flag(
        "3. Calibration / accuracy drift", "INFO", league,
        f"{n} completed matches scored{skip_note}: accuracy={accuracy:.1%}, multiclass Brier={brier:.3f} (lower is better, 0=perfect, 0.667=uniform guessing)",
    )
    if high_conf_misses:
        examples = "; ".join(f"{m} (predicted {p} @{c:.0%}, actual {a})" for m, p, a, c in high_conf_misses[:5])
        flag(
            "3. Calibration / accuracy drift", "WARN", league,
            f"{len(high_conf_misses)} high-confidence (>=70%) miss(es): {examples}" + (" ..." if len(high_conf_misses) > 5 else ""),
        )


def check_pipeline_health(league_ids: list[str]) -> None:
    missing = [lg for lg in league_ids if not (DASHBOARD / f"{lg}_match_predictions.json").exists()]
    if missing:
        flag("4. Pipeline / site operational health", "FAIL", "all", f"missing match_predictions.json for: {', '.join(missing)}")

    try:
        out = subprocess.run(
            ["gh", "run", "list", "--limit", "10", "--json", "name,status,conclusion,createdAt"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
        )
        if out.returncode != 0:
            flag("4. Pipeline / site operational health", "WARN", "all", f"could not query GitHub Actions (gh exit {out.returncode}): {out.stderr.strip()[:200]}")
        else:
            runs = json.loads(out.stdout)
            failures = [r for r in runs if r["status"] == "completed" and r["conclusion"] not in ("success", "skipped")]
            if failures:
                for r in failures:
                    flag("4. Pipeline / site operational health", "FAIL", "all", f"workflow run failed: {r['name']} ({r['conclusion']}, {r['createdAt']})")
            else:
                flag("4. Pipeline / site operational health", "INFO", "all", f"last {len(runs)} GitHub Actions runs all succeeded")
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        flag("4. Pipeline / site operational health", "WARN", "all", f"could not query GitHub Actions: {e}")


def main() -> None:
    now = datetime.now(timezone.utc)
    leagues_payload = json.loads((DASHBOARD / "leagues.json").read_text())
    league_ids = [lg["league_id"] for lg in leagues_payload["leagues"]]

    for league in league_ids:
        path = DASHBOARD / f"{league}_match_predictions.json"
        if not path.exists():
            continue
        payload = json.loads(path.read_text())
        rows = payload["data"]
        check_internal_consistency(league, rows)
        check_freshness(league, payload, rows, now)
        check_calibration(league, rows)

    check_pipeline_health(league_ids)

    n_fail = sum(1 for f in findings if f["severity"] == "FAIL")
    n_warn = sum(1 for f in findings if f["severity"] == "WARN")
    n_info = sum(1 for f in findings if f["severity"] == "INFO")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write("# Prediction Health Report\n\n")
        f.write(f"Generated: {now.isoformat()}\n\n")
        f.write(f"**{n_fail} failures, {n_warn} warnings, {n_info} informational** (out of {len(findings)} findings).\n\n")
        f.write("| Severity | Section | League | Finding |\n|---|---|---|---|\n")
        for item in findings:
            f.write(f"| {item['severity']} | {item['section']} | {item['league']} | {item['message']} |\n")

    print(f"Prediction health check: {n_fail} failures, {n_warn} warnings, {n_info} informational.")
    print(f"Report written to {REPORT_PATH}\n")
    for item in findings:
        if item["severity"] in ("FAIL", "WARN"):
            print(f"  {item['severity']} [{item['section']}] ({item['league']}): {item['message']}")

    sys.exit(1 if n_fail > 0 else 0)


if __name__ == "__main__":
    main()
