"""Generates reports/epl_2026_27_data_audit.md: an honest accounting of
what is real vs. missing/flagged across every raw data file, per spec
section 2's "if a source is unavailable, create a missing-data report"
rule.

Run: python -m src.data_validation.missing_data_report
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils.versioning import now_utc_iso  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"
OUT_PATH = REPO_ROOT / "reports" / "epl_2026_27_data_audit.md"
DATA_SOURCES_CONFIG = REPO_ROOT / "config" / "data_sources.yaml"


def summarize_file(filename: str) -> dict:
    path = RAW_DIR / filename
    if not path.exists():
        return {"filename": filename, "exists": False}
    df = pd.read_csv(path)
    real_count = int(df["is_real_data"].astype(str).str.lower().isin(["true", "1"]).sum()) if "is_real_data" in df else None
    return {
        "filename": filename,
        "exists": True,
        "n_rows": len(df),
        "n_real_rows": real_count,
        "n_flagged_unavailable": int((df["data_status"] == "unavailable").sum()) if "data_status" in df else None,
        "sources": sorted(df["source_name"].dropna().unique().tolist()) if "source_name" in df else [],
    }


def main() -> None:
    with open(DATA_SOURCES_CONFIG) as f:
        sources_cfg = yaml.safe_load(f)

    files = [
        "epl_2026_27_fixtures.csv", "epl_historical_matches.csv", "epl_2026_27_squads_transfers.csv",
        "epl_2026_27_injury_suspension.csv", "epl_2026_27_real_odds.csv", "epl_2026_27_outright_odds.csv",
    ]
    summaries = [summarize_file(f) for f in files]

    with open(OUT_PATH, "w") as f:
        f.write("# EPL 2026-27 Data Audit\n\n")
        f.write(f"Generated: {now_utc_iso()}\n\n")
        f.write("This report accounts for every raw data file used by the pipeline: what is real and "
                "independently verifiable, and what is explicitly flagged as unavailable rather than "
                "fabricated. See `config/data_sources.yaml` for the full source registry.\n\n")

        f.write("## Connected real sources\n\n")
        for src in sources_cfg.get("connected_real_sources", []):
            f.write(f"- **{src['name']}**: {src['provides']}\n")
            if "url" in src:
                f.write(f"  - URL: {src['url']}\n")
            if "url_pattern" in src:
                f.write(f"  - URL pattern: {src['url_pattern']}\n")
            if "cross_checked_against" in src:
                f.write(f"  - Cross-checked against: {src['cross_checked_against']}\n")
        f.write("\n")

        conditional = sources_cfg.get("conditionally_connected_sources", [])
        if conditional:
            f.write("## Conditionally connected sources (collector built and tested, needs a user-supplied key)\n\n")
            for src in conditional:
                f.write(f"- **{src['name']}**: {src['provides']}\n")
                f.write(f"  - Terms evaluated: {src['terms_evaluated'].strip()}\n")
                f.write(f"  - Key handling: {src['api_key_handling']}\n")
                f.write(f"  - Status: {src['status']}\n")
            f.write("\n")

        f.write("## Documented gaps (not fabricated, explicitly flagged)\n\n")
        for gap in sources_cfg.get("not_connected_documented_gap", []):
            f.write(f"- **{gap['name']}**: {gap['reason'].strip()}\n")
            if gap.get("affected_files"):
                f.write(f"  - Affected files: {', '.join(gap['affected_files'])}\n")
            f.write(f"  - Mitigation: {gap['mitigation']}\n")
        f.write("\n")

        f.write(
            "## Known limitation: player availability (injuries/suspensions)\n\n"
            "No connected real source exists for current 2026-27 EPL injury/suspension data. "
            "`data/raw/epl_2026_27_injury_suspension.csv` is 20 team-level `availability_status=unknown` "
            "sentinel rows, not real reports -- per this project's rule, missing injury data is never "
            "treated as \"fully healthy,\" and every prediction row sets `injury_data_available=False` "
            "rather than silently assuming a full-strength squad. API-Football was evaluated as a "
            "candidate (free tier: 100 requests/day, a dedicated `/injuries` endpoint, terms that permit "
            "dashboard/app use) but its free-tier coverage of the *current* season specifically could not "
            "be confirmed without creating a real account, which this pipeline cannot do on its own. This "
            "is a genuine, disclosed data gap, not a proxy or an estimate standing in for real data.\n\n"
        )

        f.write("## Per-file summary\n\n")
        f.write("| File | Exists | Rows | Real rows | Flagged unavailable | Sources |\n")
        f.write("|---|---|---|---|---|---|\n")
        for s in summaries:
            if not s["exists"]:
                f.write(f"| {s['filename']} | NO | - | - | - | - |\n")
                continue
            f.write(
                f"| {s['filename']} | yes | {s['n_rows']} | {s['n_real_rows']} | "
                f"{s['n_flagged_unavailable']} | {', '.join(s['sources']) or '-'} |\n"
            )
        f.write("\n")

        f.write("## Reading this table\n\n"
                "- `epl_2026_27_fixtures.csv` and `epl_historical_matches.csv` should show **all rows real**, "
                "0 flagged unavailable -- these are the two genuinely-connected real data sources.\n"
                "- `epl_2026_27_squads_transfers.csv`, `epl_2026_27_injury_suspension.csv`, and "
                "`epl_2026_27_outright_odds.csv` should show **0 real rows, all rows flagged unavailable** -- "
                "these are honest sentinel files, not fabricated data.\n"
                "- `epl_2026_27_real_odds.csv` shows 0 real rows **unless a real `ODDS_API_KEY` is configured** "
                "(see `.env.example`); the collector is built and tested against the real endpoint (both the "
                "no-key and invalid-key paths), but no key is available in this environment. If a key is ever "
                "added, expect real rows only for fixtures close enough to kickoff that a bookmaker has posted "
                "a market -- most of the 380 fixtures will still show unavailable at any given time.\n"
                "- Any prediction feature drawing on an unavailable file must set the corresponding "
                "`*_available=False` flag, which `src/models/predict_all_matches.py` does.\n")

    print(f"Wrote data audit to {OUT_PATH}")


if __name__ == "__main__":
    main()
