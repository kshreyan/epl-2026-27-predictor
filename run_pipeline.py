#!/usr/bin/env python3
"""Master pipeline entrypoint.

Phase 1 supports:
    python run_pipeline.py --season 2026-27 --mode preseason

which runs, in leakage-safe order: real data collection, data
validation, feature building, backtest, calibration, full-season
Monte Carlo simulation, match predictions, and the data audit report.

`--mode weekly_update`, `--mode pre_match`, and `--mode
confirmed_lineup` are defined by the spec but not implemented in
Phase 1 (see reports/epl_2026_27_model_report.md "Limitations" --
they depend on injury/lineup/market data collectors that are
currently honest sentinel stubs, and on real 2026-27 match results
which do not exist yet since today is before kickoff).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

PRESEASON_STEPS = [
    ("Collect real 2026-27 fixtures", "src.data_collection.collect_fixtures"),
    ("Collect real historical results (2014/15-2025/26)", "src.data_collection.collect_historical_results"),
    ("Collect squad/transfer sentinel data", "src.data_collection.collect_squads_transfers"),
    ("Collect injury/suspension sentinel data", "src.data_collection.collect_injuries"),
    ("Collect match-odds sentinel data", "src.data_collection.collect_odds"),
    ("Collect outright-odds sentinel data", "src.data_collection.collect_outright_odds"),
    ("Validate raw data schemas", "src.data_validation.validate_raw_data"),
    ("Build team-strength baseline", "src.features.build_team_strength_features"),
    ("Build match features", "src.features.build_match_features"),
    ("Run rolling-origin backtest", "src.evaluation.backtest"),
    ("Calibrate probabilities", "src.calibration.calibrate_probabilities"),
    ("Simulate full 2026-27 season (250k Monte Carlo runs)", "src.simulation.simulate_full_season"),
    ("Predict all 380 matches", "src.models.predict_all_matches"),
    ("Generate data audit report", "src.data_validation.missing_data_report"),
]


def run_step(label: str, module: str) -> None:
    print(f"\n{'=' * 70}\n{label}\n  (python -m {module})\n{'=' * 70}")
    t0 = time.time()
    result = subprocess.run([sys.executable, "-m", module], cwd=REPO_ROOT)
    elapsed = time.time() - t0
    if result.returncode != 0:
        print(f"\nFAILED: {module} (exit code {result.returncode}, {elapsed:.1f}s)")
        sys.exit(result.returncode)
    print(f"  done in {elapsed:.1f}s")


def main() -> None:
    parser = argparse.ArgumentParser(description="EPL 2026-27 prediction pipeline")
    parser.add_argument("--season", default="2026-27")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["preseason", "weekly_update", "pre_match", "confirmed_lineup"],
    )
    parser.add_argument("--matchweek", default=None, help="required for --mode weekly_update")
    parser.add_argument("--match_id", default=None, help="required for --mode pre_match / confirmed_lineup")
    args = parser.parse_args()

    if args.mode != "preseason":
        print(
            f"--mode {args.mode} is defined by the project spec but not implemented in Phase 1.\n"
            f"It depends on real 2026-27 match results, live injury/lineup reports, and a live odds "
            f"feed, none of which exist yet (today is before kickoff; see "
            f"reports/epl_2026_27_model_report.md 'Limitations'). Use --mode preseason."
        )
        sys.exit(2)

    print(f"Running preseason pipeline for season {args.season}")
    for label, module in PRESEASON_STEPS:
        run_step(label, module)

    print(f"\n{'=' * 70}\nPreseason pipeline complete.\n{'=' * 70}")


if __name__ == "__main__":
    main()
