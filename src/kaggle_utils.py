"""Shared utilities for Utah FORGE 56-32 Kaggle notebooks (English-first outputs).

Designed to be copy-pasteable into Kaggle cells: no local path assumptions.
Kaggle Dataset slug default: utah-forge-56-32-1sec
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd

SENSOR_8 = [
    "Rate Of Penetration (ft_per_hr)",
    "Weight on Bit (klbs)",
    "Rotary RPM (RPM)",
    "Standpipe Pressure (psi)",
    "Rotary Torque (kft_lb)",
    "Hook Load (klbs)",
    "Total Pump Output (gal_per_min)",
    "Differential Pressure (psi)",
]

DROP_COLS = ["Pason Gas (percent)", "Gamma (api)"]  # ~100% -999.25 in head sample
MISSING_CODE = -999.25
CSV_NAME = "56-32 1sec data 27029986.csv"
DATASET_SLUG = "utah-forge-56-32-1sec"


def resolve_input_path(csv_name: str = CSV_NAME, slug: str = DATASET_SLUG) -> Path:
    """Resolve CSV path on Kaggle (/kaggle/input/<slug>/) or local dataset/ fallback.

    Robust: searches recursively (handles nested zip-extract folders and
    slightly renamed files), fuzzy-matches the Utah FORGE filename, and
    lists /kaggle/input contents in the error to debug missing Add Input.
    """
    kaggle_root = Path("/kaggle/input")
    if kaggle_root.exists():
        # 1) exact filename, any depth
        hits = list(kaggle_root.rglob(csv_name))
        if hits:
            return hits[0]
        # 2) fuzzy: Utah FORGE sensor file under any name variant
        for p in kaggle_root.rglob("*.csv"):
            if "56-32" in p.name or "1sec" in p.name or "27029986" in p.name:
                return p
        # 3) any CSV at all (largest = almost certainly the sensor data)
        csvs = [p for p in kaggle_root.rglob("*.csv") if p.is_file()]
        if csvs:
            return max(csvs, key=lambda p: p.stat().st_size)
        # 4) parquet mirror
        pqs = [p for p in kaggle_root.rglob("*.parquet") if p.is_file()]
        if pqs:
            return max(pqs, key=lambda p: p.stat().st_size)
    for c in [
        Path("dataset") / csv_name,
        Path("../dataset") / csv_name,
        Path.cwd() / "dataset" / csv_name,
    ]:
        if c.exists():
            return c
    listing = (
        [str(p) for p in sorted(kaggle_root.rglob("*"))][:30]
        if kaggle_root.exists()
        else ["< /kaggle/input not found - not on Kaggle? >"]
    )
    raise FileNotFoundError(
        f"Could not find {csv_name}. /kaggle/input contains: {listing}. "
        f"Fix: in the Kaggle notebook right panel click 'Add Input' -> "
        f"search your private dataset (slug '{slug}') -> Add, then re-run."
    )


def load_sample(nrows: int = 100_000, seed: int = 42) -> pd.DataFrame:
    """Fast stratified-ish sample for EDA: evenly spaced skiprows (memory-safe).

    Uses only SENSOR_8 + time cols + float32 downcast.
    """
    path = resolve_input_path()
    usecols = ["YYYY/MM/DD", "HH:MM:SS"] + SENSOR_8
    # Estimate total rows cheaply only once (cached); fallback to chunked skip sampling
    # For speed we read first nrows*2 then take evenly spaced sample
    df = pd.read_csv(path, usecols=usecols, nrows=nrows * 2, low_memory=True)
    if len(df) > nrows:
        rng = np.random.RandomState(seed)
        idx = np.sort(rng.choice(len(df), nrows, replace=False))
        df = df.iloc[idx].reset_index(drop=True)
    for c in SENSOR_8:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float32")
    df["datetime"] = pd.to_datetime(
        df["YYYY/MM/DD"] + " " + df["HH:MM:SS"], format="%Y/%m/%d %H:%M:%S", errors="coerce"
    )
    return df


def clean_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Drop MISSING_CODE sentinels only where applicable; keep physics outliers for analysis."""
    df = df.copy()
    for c in SENSOR_8:
        if c in df.columns:
            # -999.25 never valid for the 8 sensors, treat as NaN if present
            df.loc[df[c] == MISSING_CODE, c] = np.nan
    return df.dropna(subset=SENSOR_8).reset_index(drop=True)


def build_windows(df: pd.DataFrame, window: int = 60, step: int = 30) -> pd.DataFrame:
    """Sliding-window aggregation: mean, std, delta (last-first) per sensor.

    Addresses Keogh & Lin (2005) critique: cluster on features, not raw subsequences.
    Expects datetime-sorted df with SENSOR_8 columns.
    """
    df = df.sort_values("datetime").reset_index(drop=True)
    rows = []
    for start in range(0, len(df) - window + 1, step):
        chunk = df.iloc[start : start + window]
        rec = {"window_start": chunk["datetime"].iloc[0], "window_end": chunk["datetime"].iloc[-1]}
        for c in SENSOR_8:
            v = chunk[c].to_numpy(dtype="float64")
            rec[f"{c}__mean"] = float(np.mean(v))
            rec[f"{c}__std"] = float(np.std(v))
            rec[f"{c}__delta"] = float(v[-1] - v[0])
        rows.append(rec)
    return pd.DataFrame(rows)


def clustering_metrics(X: np.ndarray, labels: np.ndarray) -> dict:
    """Silhouette (higher better) + Davies-Bouldin (lower better). Sampled for speed."""
    from sklearn.metrics import davies_bouldin_score, silhouette_score

    out = {}
    n = len(X)
    if len(np.unique(labels)) < 2:
        return {"silhouette": float("nan"), "davies_bouldin": float("nan")}
    idx = np.random.RandomState(42).choice(n, min(n, 20_000), replace=False)
    out["silhouette"] = float(silhouette_score(X[idx], labels[idx]))
    out["davies_bouldin"] = float(davies_bouldin_score(X[idx], labels[idx]))
    return out
