#!/usr/bin/env python3
"""Phase B: chronological split, train-only scaling, and Train-only EDA."""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

ROOT = Path(__file__).resolve().parents[1]

N_VALID = 38_177
N_TRAIN_NOMINAL = 26_723
N_TEST_NOMINAL = N_VALID - N_TRAIN_NOMINAL
EMBARGO_SECONDS = 3_600
TIME_FORMAT = "%Y/%m/%d %H:%M:%S"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return value


def scaler_state(scaler: Any) -> tuple[tuple[str, Any], ...]:
    """Exact, serialization-independent snapshot of all fitted scaler attributes."""
    state: list[tuple[str, Any]] = []
    for name, value in sorted(vars(scaler).items()):
        if isinstance(value, np.ndarray):
            frozen: Any = (value.dtype.str, value.shape, value.tobytes())
        elif isinstance(value, np.generic):
            frozen = (value.dtype.str, value.tobytes())
        else:
            frozen = value
        state.append((name, frozen))
    return tuple(state)


def scaler_parameters(scaler: Any, names: tuple[str, ...]) -> dict[str, Any]:
    return {name: _json_value(getattr(scaler, name)) for name in names}


def strict_valid_mask(values: pd.Series) -> pd.Series:
    parsed = values.map({True: True, False: False, "True": True, "False": False})
    if parsed.isna().any():
        raise ValueError("metadata valid column must contain only True or False")
    return parsed.astype(bool)


def load_valid_join(root: Path) -> tuple[pd.DataFrame, list[str]]:
    manifest_path = root / "outputs/manifests/phase_a_manifest.json"
    features_path = root / "data/processed/window_features.csv"
    metadata_path = root / "data/processed/window_metadata.csv"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_hashes = manifest["output_sha256"]
    for path in (features_path, metadata_path):
        actual = sha256_file(path)
        if actual != expected_hashes[path.name]:
            raise RuntimeError(f"Phase A SHA-256 mismatch for {path.name}: {actual}")

    feature_columns = manifest["feature_columns"]
    if len(feature_columns) != 39 or len(set(feature_columns)) != 39:
        raise RuntimeError("Phase A manifest must declare exactly 39 unique feature columns")
    features = pd.read_csv(features_path)
    metadata = pd.read_csv(metadata_path)
    if features.columns.tolist() != ["window_id", *feature_columns]:
        raise RuntimeError("window_features.csv does not match Phase A feature contract")
    if metadata["window_id"].duplicated().any() or features["window_id"].duplicated().any():
        raise RuntimeError("window_id must be unique in both Phase A inputs")

    valid = metadata.loc[strict_valid_mask(metadata["valid"])].copy()
    joined = valid.merge(features, on="window_id", how="inner", validate="one_to_one")
    if len(valid) != N_VALID or len(features) != N_VALID or len(joined) != N_VALID:
        raise RuntimeError(
            f"expected exactly {N_VALID} valid one-to-one joined windows; "
            f"valid={len(valid)} features={len(features)} joined={len(joined)}"
        )
    if set(valid["window_id"]) != set(features["window_id"]):
        raise RuntimeError("valid metadata and feature window_id sets differ")
    joined["start_time"] = pd.to_datetime(joined["start_time"], format=TIME_FORMAT, errors="raise")
    joined["end_time"] = pd.to_datetime(joined["end_time"], format=TIME_FORMAT, errors="raise")
    if (joined["end_time"] < joined["start_time"]).any():
        raise RuntimeError("window end_time precedes start_time")
    joined = joined.sort_values(["start_time", "window_id"], kind="stable").reset_index(drop=True)
    return joined, feature_columns


def chronological_membership(joined: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    if len(joined) != N_VALID:
        raise ValueError(f"expected {N_VALID} rows before split")
    train = joined.iloc[:N_TRAIN_NOMINAL].copy()
    test_nominal = joined.iloc[N_TRAIN_NOMINAL:].copy()
    if len(test_nominal) != N_TEST_NOMINAL:
        raise AssertionError("nominal 70:30 split has wrong cardinality")
    train_support_end_exclusive = train["end_time"].max() + pd.Timedelta(seconds=1)
    test_start_minimum = train_support_end_exclusive + pd.Timedelta(seconds=EMBARGO_SECONDS)
    embargo = test_nominal.loc[test_nominal["start_time"] < test_start_minimum].copy()
    test = test_nominal.loc[test_nominal["start_time"] >= test_start_minimum].copy()
    if test.empty:
        raise RuntimeError("embargo removed every nominal test window")
    actual_gap = test["start_time"].min() - train_support_end_exclusive
    if actual_gap < pd.Timedelta(seconds=EMBARGO_SECONDS):
        raise AssertionError(f"embargo violation: actual gap is {actual_gap}")
    return train, embargo, test, train_support_end_exclusive


def write_scaled(path: Path, window_ids: pd.Series, values: np.ndarray, feature_columns: list[str]) -> None:
    pd.DataFrame(values, columns=feature_columns).assign(window_id=window_ids.to_numpy()).loc[
        :, ["window_id", *feature_columns]
    ].to_csv(path, index=False)


def save_eda(
    train: pd.DataFrame,
    feature_columns: list[str],
    train_scaled: dict[str, np.ndarray],
    metrics_dir: Path,
    figures_dir: Path,
) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    X = train[feature_columns]
    stats = pd.DataFrame(
        {
            "count": X.count(), "mean": X.mean(), "std_ddof0": X.std(ddof=0), "min": X.min(),
            "q1_25": X.quantile(0.25), "median_50": X.median(), "q3_75": X.quantile(0.75),
            "max": X.max(), "skewness": X.skew(),
        }
    )
    stats.index.name = "feature"
    stats.reset_index().to_csv(metrics_dir / "train_descriptive_stats.csv", index=False)
    pearson, spearman = X.corr(method="pearson"), X.corr(method="spearman")
    pearson.index.name = spearman.index.name = "feature"
    pearson.to_csv(metrics_dir / "train_pearson_corr.csv")
    spearman.to_csv(metrics_dir / "train_spearman_corr.csv")

    sns.set_theme(style="white")
    fig, ax = plt.subplots(figsize=(26, 22))
    sns.heatmap(pearson, cmap="vlag", center=0, vmin=-1, vmax=1, square=True, ax=ax, cbar_kws={"shrink": 0.7})
    ax.set_title("Train-only Pearson correlation (39 features)")
    fig.tight_layout(); fig.savefig(figures_dir / "eda_correlation_heatmap.png", dpi=180); plt.close(fig)

    channel_mean_columns = [column for column in feature_columns if column.endswith("_mean")]
    fig, ax = plt.subplots(figsize=(18, 8))
    sns.boxplot(data=X[channel_mean_columns], showfliers=False, ax=ax)
    ax.set_yscale("symlog", linthresh=1.0); ax.tick_params(axis="x", rotation=45)
    ax.set_ylabel("Train-only channel mean (symlog scale)"); ax.set_title("Sensor scale disparity across channel means")
    fig.tight_layout(); fig.savefig(figures_dir / "eda_scale_disparity_boxplots.png", dpi=180); plt.close(fig)

    key_features = [name for name in ("ROP_mean", "SPP_mean", "PumpOut_mean", "Hydraulic_P_mean", "Mech_P_mean") if name in feature_columns]
    indexes = [feature_columns.index(name) for name in key_features]
    scalers = {
        "Unscaled": X[key_features].to_numpy(),
        "Standard": train_scaled["standard"][:, indexes],
        "Robust": train_scaled["robust"][:, indexes],
        "MinMax": train_scaled["minmax"][:, indexes],
    }
    fig, axes = plt.subplots(len(key_features), len(scalers), figsize=(18, 3.2 * len(key_features)), squeeze=False)
    for row, feature in enumerate(key_features):
        for column, (label, array) in enumerate(scalers.items()):
            sns.histplot(array[:, row], bins=50, stat="density", element="step", fill=False, ax=axes[row, column])
            axes[row, column].set_title(f"{feature}: {label}"); axes[row, column].set_ylabel("density")
    fig.suptitle("Train-only feature distributions before and after scaling", y=1.002)
    fig.tight_layout(); fig.savefig(figures_dir / "eda_scaler_comparison_distributions.png", dpi=180); plt.close(fig)


def build_outputs(root: Path = ROOT) -> dict[str, Any]:
    started = time.monotonic()
    membership_dir, scaled_dir = root / "data/splits", root / "data/splits/scaled"
    scaler_dir, metrics_dir = root / "models/scalers", root / "outputs/metrics"
    figures_dir, manifest_dir = root / "outputs/figures", root / "outputs/manifests"
    for directory in (membership_dir, scaled_dir, scaler_dir, metrics_dir, figures_dir, manifest_dir):
        directory.mkdir(parents=True, exist_ok=True)

    joined, feature_columns = load_valid_join(root)
    train, embargo, test, train_support_end_exclusive = chronological_membership(joined)
    membership_path = membership_dir / "membership.csv"
    membership = pd.concat([train.assign(split="TRAIN"), embargo.assign(split="EMBARGO"), test.assign(split="TEST")], ignore_index=True)[["window_id", "segment_id", "start_time", "end_time", "split"]].copy()
    membership["start_time"] = membership["start_time"].dt.strftime(TIME_FORMAT)
    membership["end_time"] = membership["end_time"].dt.strftime(TIME_FORMAT)
    if membership["window_id"].duplicated().any() or len(membership) != len(joined):
        raise AssertionError("membership is not mutually exclusive and exhaustive")
    membership.to_csv(membership_path, index=False)

    X_train = train[feature_columns].to_numpy(dtype=np.float64, copy=True)
    X_test = test[feature_columns].to_numpy(dtype=np.float64, copy=True)
    if X_train.shape != (N_TRAIN_NOMINAL, len(feature_columns)):
        raise AssertionError(f"unexpected train matrix shape: {X_train.shape}")
    scaler_specs = {
        "standard": (StandardScaler(with_mean=True, with_std=True), ("mean_", "var_", "scale_")),
        "robust": (RobustScaler(with_centering=True, with_scaling=True, quantile_range=(25.0, 75.0), unit_variance=False), ("center_", "scale_")),
        "minmax": (MinMaxScaler(feature_range=(0.0, 1.0), clip=False), ("data_min_", "data_max_", "data_range_", "scale_", "min_")),
    }
    scaler_summary: dict[str, Any] = {}
    train_scaled_by_name: dict[str, np.ndarray] = {}
    output_paths = [membership_path]
    for name, (scaler, parameter_names) in scaler_specs.items():
        scaler.fit(X_train)
        fit_state = scaler_state(scaler)
        train_scaled, test_scaled = scaler.transform(X_train), scaler.transform(X_test)
        if scaler_state(scaler) != fit_state:
            raise AssertionError(f"{name} transform changed fitted scaler state")
        model_path = scaler_dir / f"{name}_scaler.joblib"
        joblib.dump(scaler, model_path)
        train_path, test_path = scaled_dir / f"train_{name}.csv", scaled_dir / f"test_{name}.csv"
        write_scaled(train_path, train["window_id"], train_scaled, feature_columns)
        write_scaled(test_path, test["window_id"], test_scaled, feature_columns)
        output_paths.extend((model_path, train_path, test_path))
        train_scaled_by_name[name] = train_scaled
        scaler_summary[name] = {"class": type(scaler).__name__, "fit_rows": int(len(X_train)), "parameters": scaler_parameters(scaler, parameter_names)}

    save_eda(train, feature_columns, train_scaled_by_name, metrics_dir, figures_dir)
    output_paths.extend([metrics_dir / "train_descriptive_stats.csv", metrics_dir / "train_pearson_corr.csv", metrics_dir / "train_spearman_corr.csv", figures_dir / "eda_correlation_heatmap.png", figures_dir / "eda_scale_disparity_boxplots.png", figures_dir / "eda_scaler_comparison_distributions.png"])
    output_hashes = {str(path.relative_to(root)): sha256_file(path) for path in output_paths}
    test_start = test["start_time"].min()
    manifest = {
        "phase": "B", "input_phase_a_sha256_verified": True, "valid_rows": int(len(joined)),
        "train_rows": int(len(train)), "embargo_rows": int(len(embargo)), "test_rows": int(len(test)),
        "n_train_nominal": N_TRAIN_NOMINAL, "n_test_nominal": N_TEST_NOMINAL, "embargo_seconds": EMBARGO_SECONDS,
        "train_support_end_exclusive": train_support_end_exclusive.strftime(TIME_FORMAT),
        "test_start_minimum": (train_support_end_exclusive + pd.Timedelta(seconds=EMBARGO_SECONDS)).strftime(TIME_FORMAT),
        "first_test_start": test_start.strftime(TIME_FORMAT),
        "actual_embargo_seconds": float((test_start - train_support_end_exclusive).total_seconds()),
        "scalers": scaler_summary, "feature_columns": feature_columns, "output_sha256": output_hashes,
        "runtime_seconds": round(time.monotonic() - started, 3),
    }
    (manifest_dir / "phase_b_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("PASS " f"valid_rows={len(joined)} train_rows={len(train)} embargo_rows={len(embargo)} test_rows={len(test)} " f"actual_embargo_seconds={manifest['actual_embargo_seconds']:.0f} runtime_seconds={manifest['runtime_seconds']:.3f}", flush=True)
    return manifest


def main() -> None:
    build_outputs()


if __name__ == "__main__":
    main()
