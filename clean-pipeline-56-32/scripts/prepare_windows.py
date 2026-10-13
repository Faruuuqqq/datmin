#!/usr/bin/env python3
"""Build clean 60-second tumbling windows from the Well 56-32 raw CSV."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

CHUNKSIZE = 50_000
WINDOW_SECONDS = 60
MIN_COVERAGE = 54
SENTINEL = -999.25
TIMESTAMP_FORMAT = "%Y/%m/%d %H:%M:%S"
DATE_COLUMN = "YYYY/MM/DD"
TIME_COLUMN = "HH:MM:SS"

RAW_COLUMNS = {
    "ROP": "Rate Of Penetration (ft_per_hr)",
    "WOB": "Weight on Bit (klbs)",
    "RPM": "Rotary RPM (RPM)",
    "SPP": "Standpipe Pressure (psi)",
    "Torque": "Rotary Torque (kft_lb)",
    "HookLoad": "Hook Load (klbs)",
    "Flow": "Flow (flow_percent)",
    "PumpOut": "Total Pump Output (gal_per_min)",
    "MudVol": "Total Mud Volume (barrels)",
    "BlockHeight": "Block Height (feet)",
    "SPM1": "Pump 1 strokes/min (SPM)",
}
CHANNELS = [*RAW_COLUMNS, "Hydraulic_P", "Mech_P"]
FEATURE_COLUMNS = [f"{channel}_{stat}" for channel in CHANNELS for stat in ("mean", "std", "delta")]
ONE_SECOND = pd.Timedelta(seconds=1)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean_chunk(chunk: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop SPP sentinel rows, then mask sensor sentinels and derive proxies."""
    spp_raw = chunk[RAW_COLUMNS["SPP"]].to_numpy(dtype=np.float64, copy=False)
    keep = ~(spp_raw <= -900.0)
    dropped = int((~keep).sum())
    retained = chunk.loc[keep]

    out = pd.DataFrame(index=retained.index)
    out["timestamp"] = pd.to_datetime(
        retained[DATE_COLUMN].astype(str) + " " + retained[TIME_COLUMN].astype(str),
        format=TIMESTAMP_FORMAT,
        errors="raise",
    )
    for channel, raw_column in RAW_COLUMNS.items():
        values = retained[raw_column].to_numpy(dtype=np.float64, copy=True)
        values[values == SENTINEL] = np.nan
        out[channel] = values

    spp = out["SPP"].to_numpy(dtype=np.float64, copy=False)
    pump_out = out["PumpOut"].to_numpy(dtype=np.float64, copy=False)
    torque = out["Torque"].to_numpy(dtype=np.float64, copy=False)
    rpm = out["RPM"].to_numpy(dtype=np.float64, copy=False)
    # np.maximum preserves NaN, satisfying the missing-input proxy contract.
    out["Hydraulic_P"] = np.maximum(spp, 0.0) * np.maximum(pump_out, 0.0)
    out["Mech_P"] = np.maximum(torque, 0.0) * np.maximum(rpm, 0.0)
    return out.reset_index(drop=True), dropped


def window_features(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return 39 features and finite coverage for a 60 x 13 window."""
    if values.shape != (WINDOW_SECONDS, len(CHANNELS)):
        raise ValueError(f"expected {(WINDOW_SECONDS, len(CHANNELS))}, got {values.shape}")
    coverage = np.isfinite(values).sum(axis=0).astype(int)
    features: list[float] = []
    for index in range(values.shape[1]):
        finite = values[np.isfinite(values[:, index]), index]
        if finite.size == 0:
            features.extend((np.nan, np.nan, np.nan))
        else:
            features.extend((float(finite.mean()), float(finite.std(ddof=0)), float(finite[-1] - finite[0])))
    return np.asarray(features, dtype=np.float64), coverage


class WindowAccumulator:
    """Keep only one current tumbling window while preserving segment boundaries."""

    def __init__(self) -> None:
        self.previous_time: pd.Timestamp | None = None
        self.segment_id = -1
        self.buffer: list[tuple[pd.Timestamp, np.ndarray]] = []
        self.window_id = 0
        self.metadata: list[dict[str, Any]] = []
        self.feature_rows: list[dict[str, Any]] = []
        self.segment_resets = 0
        self.tail_discarded_rows = 0

    def _discard_tail(self) -> None:
        self.tail_discarded_rows += len(self.buffer)
        self.buffer.clear()

    def _emit_window(self) -> None:
        timestamps = [row[0] for row in self.buffer]
        values = np.vstack([row[1] for row in self.buffer])
        features, coverage = window_features(values)
        bad_channels = [CHANNELS[i] for i, count in enumerate(coverage) if count < MIN_COVERAGE]
        valid = not bad_channels and bool(np.isfinite(features).all())
        reject_reason = "" if valid else (
            "coverage_below_54:" + ",".join(bad_channels) if bad_channels else "non_finite_feature"
        )
        record: dict[str, Any] = {
            "window_id": self.window_id,
            "segment_id": self.segment_id,
            "start_time": timestamps[0].strftime(TIMESTAMP_FORMAT),
            "end_time": timestamps[-1].strftime(TIMESTAMP_FORMAT),
            "valid": valid,
            "reject_reason": reject_reason,
            "n_rows": len(self.buffer),
        }
        record.update({f"{channel}_coverage": int(coverage[i]) for i, channel in enumerate(CHANNELS)})
        self.metadata.append(record)
        if valid:
            self.feature_rows.append({"window_id": self.window_id, **dict(zip(FEATURE_COLUMNS, features.tolist(), strict=True))})
        self.window_id += 1
        self.buffer.clear()

    def ingest(self, cleaned: pd.DataFrame) -> None:
        for timestamp, row in zip(
            cleaned["timestamp"].tolist(),
            cleaned[CHANNELS].to_numpy(dtype=np.float64, copy=False),
            strict=True,
        ):
            if self.previous_time is None:
                self.segment_id += 1
            elif timestamp - self.previous_time != ONE_SECOND:
                self._discard_tail()
                self.segment_id += 1
                self.segment_resets += 1
            self.buffer.append((timestamp, row.copy()))
            self.previous_time = timestamp
            if len(self.buffer) == WINDOW_SECONDS:
                self._emit_window()

    def close(self) -> None:
        self._discard_tail()


def build_outputs(raw_path: Path, output_root: Path) -> dict[str, Any]:
    started = time.monotonic()
    processed_dir = output_root / "data" / "processed"
    manifest_dir = output_root / "outputs" / "manifests"
    processed_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)

    usecols = [DATE_COLUMN, TIME_COLUMN, *RAW_COLUMNS.values()]
    dtypes = {raw_column: np.float64 for raw_column in RAW_COLUMNS.values()}
    accumulator = WindowAccumulator()
    raw_rows = 0
    dropped_spp = 0
    retained_rows = 0

    for chunk_number, chunk in enumerate(
        pd.read_csv(raw_path, usecols=usecols, dtype=dtypes, chunksize=CHUNKSIZE), start=1
    ):
        raw_rows += len(chunk)
        cleaned, dropped = clean_chunk(chunk)
        dropped_spp += dropped
        retained_rows += len(cleaned)
        accumulator.ingest(cleaned)
        print(
            f"chunk={chunk_number} raw_rows={raw_rows} retained_rows={retained_rows} "
            f"dropped_spp={dropped_spp} candidate_windows={accumulator.window_id}",
            flush=True,
        )
    accumulator.close()

    metadata = pd.DataFrame(accumulator.metadata)
    metadata_columns = [
        "window_id", "segment_id", "start_time", "end_time", "valid", "reject_reason", "n_rows",
        *[f"{channel}_coverage" for channel in CHANNELS],
    ]
    metadata = metadata.reindex(columns=metadata_columns)
    features = pd.DataFrame(accumulator.feature_rows).reindex(columns=["window_id", *FEATURE_COLUMNS])
    if not features.empty and not np.isfinite(features[FEATURE_COLUMNS].to_numpy(dtype=np.float64)).all():
        raise RuntimeError("valid feature matrix contains NaN or Inf")

    feature_path = processed_dir / "window_features.csv"
    metadata_path = processed_dir / "window_metadata.csv"
    features.to_csv(feature_path, index=False)
    metadata.to_csv(metadata_path, index=False)

    valid_windows = int(metadata["valid"].sum()) if not metadata.empty else 0
    candidate_windows = len(metadata)
    manifest = {
        "phase": "A",
        "raw_path": str(raw_path),
        "raw_sha256": sha256_file(raw_path),
        "chunksize": CHUNKSIZE,
        "raw_rows": raw_rows,
        "dropped_spp_rows": dropped_spp,
        "retained_rows": retained_rows,
        "segments": accumulator.segment_id + 1 if accumulator.segment_id >= 0 else 0,
        "segment_resets": accumulator.segment_resets,
        "tail_discarded_rows": accumulator.tail_discarded_rows,
        "candidate_windows": candidate_windows,
        "valid_windows": valid_windows,
        "rejected_windows": candidate_windows - valid_windows,
        "feature_columns": FEATURE_COLUMNS,
        "feature_matrix_has_only_finite_values": True,
        "output_sha256": {
            "window_features.csv": sha256_file(feature_path),
            "window_metadata.csv": sha256_file(metadata_path),
        },
        "runtime_seconds": round(time.monotonic() - started, 3),
    }
    manifest_path = manifest_dir / "phase_a_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(
        "PASS "
        f"raw_rows={raw_rows} dropped_spp={dropped_spp} segments={manifest['segments']} "
        f"candidate_windows={candidate_windows} valid_windows={valid_windows} "
        f"rejected_windows={manifest['rejected_windows']} finite_features=true",
        flush=True,
    )
    return manifest


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw",
        type=Path,
        default=root.parent / "Datmin-new" / "dataset" / "56-32 1sec data 27029986.csv",
    )
    parser.add_argument("--output-root", type=Path, default=root)
    args = parser.parse_args()
    build_outputs(args.raw.resolve(), args.output_root.resolve())


if __name__ == "__main__":
    main()
