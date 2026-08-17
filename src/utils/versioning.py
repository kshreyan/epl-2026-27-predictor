"""Run/version metadata stamping shared by every collector, model, and report.

Every output file in this project must carry run_id/model_version/
data_version/generated_at so runs are reproducible and auditable
(see project spec section 4). This module is the single place that
generates and records that metadata.
"""
from __future__ import annotations

import csv
import subprocess
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_VERSION_MANIFEST = REPO_ROOT / "data" / "versions" / "epl_2026_27_data_version_manifest.csv"
EXPERIMENT_LOG = REPO_ROOT / "experiments" / "epl_2026_27_experiment_log.csv"
MODEL_REGISTRY = REPO_ROOT / "model_registry" / "epl_2026_27_model_registry.csv"

MODEL_VERSION = "0.1.0-phase1"
DATA_VERSION = "2026-08-18.phase1"
FEATURE_VERSION = "0.1.0-phase1"


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_run_id(prefix: str) -> str:
    return f"{prefix}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"


def git_commit_if_available() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=5, check=False,
        )
        commit = out.stdout.strip()
        return commit if commit else "no_commit_yet"
    except Exception:
        return "unavailable"


@dataclass
class RunMetadata:
    run_id: str
    season: str
    model_version: str
    data_version: str
    feature_version: str
    training_window: str
    validation_window: str
    prediction_timestamp: str
    latest_source_timestamp_used: str
    calibration_method: str
    market_weight: float
    hyperparameters: str
    metrics: str
    git_commit_if_available: str
    generated_at: str


def make_run_metadata(
    prefix: str,
    season: str,
    training_window: str = "",
    validation_window: str = "",
    latest_source_timestamp_used: str = "",
    calibration_method: str = "none",
    market_weight: float = 0.0,
    hyperparameters: str = "{}",
    metrics: str = "{}",
) -> RunMetadata:
    ts = now_utc_iso()
    return RunMetadata(
        run_id=new_run_id(prefix),
        season=season,
        model_version=MODEL_VERSION,
        data_version=DATA_VERSION,
        feature_version=FEATURE_VERSION,
        training_window=training_window,
        validation_window=validation_window,
        prediction_timestamp=ts,
        latest_source_timestamp_used=latest_source_timestamp_used or ts,
        calibration_method=calibration_method,
        market_weight=market_weight,
        hyperparameters=hyperparameters,
        metrics=metrics,
        git_commit_if_available=git_commit_if_available(),
        generated_at=ts,
    )


def _append_csv_row(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def log_experiment(meta: RunMetadata, stage: str, notes: str = "") -> None:
    row = asdict(meta)
    row["stage"] = stage
    row["notes"] = notes
    _append_csv_row(EXPERIMENT_LOG, row)


def register_model(meta: RunMetadata, model_name: str, notes: str = "") -> None:
    row = {
        "run_id": meta.run_id,
        "model_name": model_name,
        "model_version": meta.model_version,
        "data_version": meta.data_version,
        "feature_version": meta.feature_version,
        "metrics": meta.metrics,
        "hyperparameters": meta.hyperparameters,
        "git_commit_if_available": meta.git_commit_if_available,
        "generated_at": meta.generated_at,
        "notes": notes,
    }
    _append_csv_row(MODEL_REGISTRY, row)


def log_data_version(
    dataset_name: str,
    source_name: str,
    source_timestamp: str,
    row_count: int,
    is_real_data: bool,
    notes: str = "",
) -> None:
    row = {
        "dataset_name": dataset_name,
        "data_version": DATA_VERSION,
        "source_name": source_name,
        "source_timestamp": source_timestamp,
        "row_count": row_count,
        "is_real_data": is_real_data,
        "collected_at": now_utc_iso(),
        "notes": notes,
    }
    _append_csv_row(DATA_VERSION_MANIFEST, row)
