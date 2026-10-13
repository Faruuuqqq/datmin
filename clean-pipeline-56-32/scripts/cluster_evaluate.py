#!/usr/bin/env python3
"""Phase C: train-only K-Means/GMM grid evaluation with strict NO-WINNER rules."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import struct
import subprocess
import time
import zlib
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, davies_bouldin_score, silhouette_score
from sklearn.mixture import GaussianMixture

ROOT = Path(__file__).resolve().parents[1]

FEATURE_COUNT = 39
TRAIN_ROWS = 26_723
TEST_ROWS = 11_394
SILHOUETTE_SAMPLE_SIZE = 5_000
SILHOUETTE_SEED = 42
SCALERS = ("standard", "robust", "minmax")
ALGORITHMS = ("kmeans", "gmm")
K_VALUES = tuple(range(2, 9))
SEEDS = (42, 0, 1)
PRIMARY_SEED = 42
COLLAPSE_PROPORTION = 0.01
KMEANS_MAX_ITER = 300
GMM_MAX_ITER = 300


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def index_hash(indices: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(indices, dtype="<i8").tobytes()).hexdigest()


def deterministic_indices(row_count: int) -> np.ndarray:
    if row_count < SILHOUETTE_SAMPLE_SIZE:
        raise ValueError(f"need at least {SILHOUETTE_SAMPLE_SIZE} rows, got {row_count}")
    return np.random.default_rng(SILHOUETTE_SEED).choice(row_count, size=SILHOUETTE_SAMPLE_SIZE, replace=False)


def collapse_detected(counts: np.ndarray, row_count: int) -> bool:
    """A missing or <1% cluster invalidates the run."""
    return bool(np.any(counts == 0) or np.any(counts / row_count < COLLAPSE_PROPORTION))


def sharp_test_drop(silhouette_train: float, silhouette_test: float, dbi_train: float, dbi_test: float) -> bool:
    return bool(
        silhouette_train - silhouette_test > 0.10
        or dbi_test > 1.50 * dbi_train
    )


def verdict_reasons(primary: dict[str, Any], stability: dict[str, Any]) -> list[str]:
    """Apply only the ordered, locked Phase C NO-WINNER rules."""
    reasons: list[str] = []
    if primary["collapse_train"] or primary["collapse_test"]:
        reasons.append("COLLAPSE")
    if primary["non_convergent"]:
        reasons.append("NON_CONVERGENT")
    if primary["silhouette_train"] <= 0 or primary["silhouette_test"] <= 0:
        reasons.append("NEGATIVE_SILHOUETTE")
    if sharp_test_drop(
        primary["silhouette_train"], primary["silhouette_test"], primary["dbi_train"], primary["dbi_test"]
    ):
        reasons.append("SHARP_TEST_DROP")
    if stability["unstable"]:
        reasons.append("UNSTABLE")
    return reasons


def read_scaled(root: Path, scaler: str, split: str, expected_rows: int) -> tuple[np.ndarray, np.ndarray, list[str]]:
    path = root / "data/splits/scaled" / f"{split}_{scaler}.csv"
    frame = pd.read_csv(path)
    if frame.columns[0] != "window_id":
        raise RuntimeError(f"{path.name}: window_id must be the first column")
    features = frame.columns[1:].tolist()
    if len(features) != FEATURE_COUNT or len(set(features)) != FEATURE_COUNT:
        raise RuntimeError(f"{path.name}: expected exactly {FEATURE_COUNT} unique features")
    if len(frame) != expected_rows or frame["window_id"].duplicated().any():
        raise RuntimeError(f"{path.name}: unexpected row count or duplicate window_id")
    values = frame.loc[:, features].to_numpy(dtype=np.float64, copy=True)
    if not np.isfinite(values).all():
        raise RuntimeError(f"{path.name}: scaled values must all be finite")
    return frame["window_id"].to_numpy(dtype=np.int64, copy=True), values, features


def load_inputs(root: Path) -> tuple[dict[str, tuple[np.ndarray, np.ndarray]], list[str], dict[str, str]]:
    phase_b_path = root / "outputs/manifests/phase_b_manifest.json"
    phase_b = json.loads(phase_b_path.read_text(encoding="utf-8"))
    if phase_b.get("train_rows") != TRAIN_ROWS or phase_b.get("test_rows") != TEST_ROWS:
        raise RuntimeError("Phase B manifest row counts do not satisfy Phase C contract")
    expected_features = phase_b.get("feature_columns")
    if not isinstance(expected_features, list) or len(expected_features) != FEATURE_COUNT:
        raise RuntimeError("Phase B manifest must declare exactly 39 feature columns")

    loaded: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    source_hashes = {"outputs/manifests/phase_b_manifest.json": sha256_file(phase_b_path)}
    reference_train_ids: np.ndarray | None = None
    reference_test_ids: np.ndarray | None = None
    for scaler in SCALERS:
        train_path = root / "data/splits/scaled" / f"train_{scaler}.csv"
        test_path = root / "data/splits/scaled" / f"test_{scaler}.csv"
        train_ids, x_train, columns = read_scaled(root, scaler, "train", TRAIN_ROWS)
        test_ids, x_test, test_columns = read_scaled(root, scaler, "test", TEST_ROWS)
        if columns != expected_features or test_columns != expected_features:
            raise RuntimeError(f"{scaler}: scaled feature columns do not match Phase B manifest")
        if set(train_ids) & set(test_ids):
            raise RuntimeError(f"{scaler}: Train and Test window_id overlap")
        if reference_train_ids is None:
            reference_train_ids, reference_test_ids = train_ids, test_ids
        elif not np.array_equal(train_ids, reference_train_ids) or not np.array_equal(test_ids, reference_test_ids):
            raise RuntimeError(f"{scaler}: window_id ordering differs across scaler outputs")
        loaded[scaler] = (x_train, x_test)
        source_hashes[str(train_path.relative_to(root))] = sha256_file(train_path)
        source_hashes[str(test_path.relative_to(root))] = sha256_file(test_path)
    return loaded, expected_features, source_hashes


def build_model(algorithm: str, k: int, seed: int) -> Any:
    if algorithm == "kmeans":
        return KMeans(
            n_clusters=k, init="k-means++", n_init=10, max_iter=KMEANS_MAX_ITER,
            tol=1e-4, algorithm="lloyd", random_state=seed,
        )
    if algorithm == "gmm":
        return GaussianMixture(
            n_components=k, covariance_type="full", n_init=3, max_iter=GMM_MAX_ITER,
            tol=1e-3, reg_covar=1e-6, init_params="kmeans", random_state=seed,
        )
    raise ValueError(f"unknown algorithm: {algorithm}")


def split_metrics(x: np.ndarray, labels: np.ndarray, k: int, sample_indices: np.ndarray) -> tuple[float, float, np.ndarray, np.ndarray, bool]:
    counts = np.bincount(labels, minlength=k).astype(np.int64, copy=False)
    proportions = counts / len(labels)
    # Metrics need at least two observed labels; collapse is still recorded and verdicted.
    observed = np.unique(labels).size
    if observed < 2:
        return float("nan"), float("nan"), counts, proportions, True
    dbi = float(davies_bouldin_score(x, labels))
    sampled_labels = labels[sample_indices]
    silhouette = float("nan") if np.unique(sampled_labels).size < 2 else float(silhouette_score(x[sample_indices], sampled_labels))
    return silhouette, dbi, counts, proportions, collapse_detected(counts, len(labels))


def occupancy_columns(row: dict[str, Any], split: str, counts: np.ndarray, proportions: np.ndarray) -> None:
    for cluster in range(8):
        row[f"{split}_C{cluster}_count"] = int(counts[cluster]) if cluster < len(counts) else 0
        row[f"{split}_C{cluster}_prop"] = float(proportions[cluster]) if cluster < len(proportions) else 0.0


def run_one(
    scaler: str, algorithm: str, k: int, seed: int, x_train: np.ndarray, x_test: np.ndarray,
    train_sample: np.ndarray, test_sample: np.ndarray,
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    model = build_model(algorithm, k, seed)
    started = time.monotonic()
    model.fit(x_train)  # Anti-leakage: only Train is fitted.
    labels_train = model.predict(x_train)
    labels_test = model.predict(x_test)
    silhouette_train, dbi_train, train_counts, train_props, collapse_train = split_metrics(x_train, labels_train, k, train_sample)
    silhouette_test, dbi_test, test_counts, test_props, collapse_test = split_metrics(x_test, labels_test, k, test_sample)
    if algorithm == "kmeans":
        n_iter = int(model.n_iter_)
        converged = n_iter < KMEANS_MAX_ITER
        inertia = float(model.inertia_)
    else:
        n_iter = int(model.n_iter_)
        converged = bool(model.converged_)
        inertia = float("nan")
    row: dict[str, Any] = {
        "scaler": scaler, "algorithm": algorithm, "k": k, "seed": seed,
        "fit_scope": "train_only", "train_rows": len(x_train), "test_rows": len(x_test),
        "silhouette_train": silhouette_train, "silhouette_test": silhouette_test,
        "dbi_train": dbi_train, "dbi_test": dbi_test,
        "collapse_train": collapse_train, "collapse_test": collapse_test,
        "converged": converged, "non_convergent": not converged, "n_iter": n_iter,
        "inertia_train": inertia, "fit_seconds": round(time.monotonic() - started, 6),
    }
    occupancy_columns(row, "train", train_counts, train_props)
    occupancy_columns(row, "test", test_counts, test_props)
    return row, labels_train, labels_test


def stability_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    if len(records) != len(SEEDS) or {row["seed"] for row in records} != set(SEEDS):
        raise RuntimeError("each ledger configuration requires exactly seeds 42, 0, and 1")
    metrics = {}
    for split in ("train", "test"):
        silhouettes = np.array([row[f"silhouette_{split}"] for row in records], dtype=float)
        dbis = np.array([row[f"dbi_{split}"] for row in records], dtype=float)
        metrics[f"silhouette_range_{split}"] = float(np.ptp(silhouettes))
        median_dbi = float(np.median(dbis))
        metrics[f"dbi_relative_range_{split}"] = float((np.max(dbis) - np.min(dbis)) / median_dbi) if median_dbi > 0 else float("inf")
        aris = [
            float(adjusted_rand_score(left[f"labels_{split}"], right[f"labels_{split}"]))
            for left, right in combinations(records, 2)
        ]
        metrics[f"min_pairwise_ari_{split}"] = min(aris)
    unstable = bool(
        max(metrics["silhouette_range_train"], metrics["silhouette_range_test"]) > 0.05
        or max(metrics["dbi_relative_range_train"], metrics["dbi_relative_range_test"]) > 0.20
        or min(metrics["min_pairwise_ari_train"], metrics["min_pairwise_ari_test"]) < 0.80
    )
    metrics["unstable"] = unstable
    return metrics


def build_ledger(run_rows: list[dict[str, Any]], label_cache: dict[tuple[str, str, int, int], tuple[np.ndarray, np.ndarray]]) -> pd.DataFrame:
    ledger: list[dict[str, Any]] = []
    for scaler in SCALERS:
        for algorithm in ALGORITHMS:
            for k in K_VALUES:
                configuration = [
                    dict(row, labels_train=label_cache[(scaler, algorithm, k, row["seed"])][0], labels_test=label_cache[(scaler, algorithm, k, row["seed"])][1])
                    for row in run_rows if (row["scaler"], row["algorithm"], row["k"]) == (scaler, algorithm, k)
                ]
                stability = stability_summary(configuration)
                primary = next(row for row in configuration if row["seed"] == PRIMARY_SEED)
                reasons = verdict_reasons(primary, stability)
                ledger.append({
                    "scaler": scaler, "algorithm": algorithm, "k": k, "primary_seed": PRIMARY_SEED,
                    "verdict": "ELIGIBLE" if not reasons else "NO-WINNER",
                    "reason_codes": ";".join(reasons) if reasons else "PASS_ALL_LOCKED_RULES",
                    "reason_detail": (
                        f"silhouette_range_train={stability['silhouette_range_train']:.6f}; "
                        f"silhouette_range_test={stability['silhouette_range_test']:.6f}; "
                        f"dbi_relative_range_train={stability['dbi_relative_range_train']:.6f}; "
                        f"dbi_relative_range_test={stability['dbi_relative_range_test']:.6f}; "
                        f"min_pairwise_ari_train={stability['min_pairwise_ari_train']:.6f}; "
                        f"min_pairwise_ari_test={stability['min_pairwise_ari_test']:.6f}"
                    ),
                    "primary_silhouette_train": primary["silhouette_train"], "primary_silhouette_test": primary["silhouette_test"],
                    "primary_dbi_train": primary["dbi_train"], "primary_dbi_test": primary["dbi_test"],
                    "primary_collapse_train": primary["collapse_train"], "primary_collapse_test": primary["collapse_test"],
                    "primary_converged": primary["converged"], **stability,
                })
    return pd.DataFrame(ledger)


def _png(path: Path, image: np.ndarray) -> None:
    """Write RGB PNG using only the Python standard library."""
    height, width, channels = image.shape
    assert channels == 3
    raw = b"".join(bytes((0,)) + image[row].tobytes() for row in range(height))
    chunk = lambda kind, payload: struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)
    path.write_bytes(bytes((137, 80, 78, 71, 13, 10, 26, 10)) + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def _line(canvas: np.ndarray, x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int]) -> None:
    points = max(abs(x1 - x0), abs(y1 - y0), 1)
    xs = np.rint(np.linspace(x0, x1, points + 1)).astype(int)
    ys = np.rint(np.linspace(y0, y1, points + 1)).astype(int)
    valid = (xs >= 0) & (xs < canvas.shape[1]) & (ys >= 0) & (ys < canvas.shape[0])
    canvas[ys[valid], xs[valid]] = color


def _marker(canvas: np.ndarray, x: int, y: int, color: tuple[int, int, int]) -> None:
    canvas[max(0, y - 3):y + 4, max(0, x - 3):x + 4] = color


def _multi_panel_png(path: Path, series: list[list[tuple[np.ndarray, tuple[int, int, int]]]], rows: int, cols: int) -> None:
    """Minimal, dependency-free multi-panel line chart; blue=Train, orange=Test."""
    height, width, margin = rows * 270 + 50, cols * 390 + 50, 30
    canvas = np.full((height, width, 3), 255, dtype=np.uint8)
    for panel, lines in enumerate(series):
        row, col = divmod(panel, cols)
        left, top = col * 390 + margin, row * 270 + margin
        right, bottom = left + 330, top + 200
        canvas[top:bottom + 1, left] = (30, 30, 30); canvas[bottom, left:right + 1] = (30, 30, 30)
        values = np.concatenate([line[0] for line in lines])
        finite_values = values[np.isfinite(values)]
        if not len(finite_values):
            continue
        ymin, ymax = float(finite_values.min()), float(finite_values.max())
        pad = max((ymax - ymin) * 0.08, 1e-12); ymin -= pad; ymax += pad
        for grid in range(1, 5):
            y = top + (bottom - top) * grid // 5
            canvas[y, left:right + 1] = (225, 225, 225)
        for values, color in lines:
            xs = np.rint(np.linspace(left + 8, right - 8, len(values))).astype(int)
            finite = np.isfinite(values)
            ys = np.zeros(len(values), dtype=int)
            ys[finite] = np.rint(bottom - 8 - (values[finite] - ymin) / (ymax - ymin) * (bottom - top - 16)).astype(int)
            for start in range(len(values) - 1):
                if finite[start] and finite[start + 1]: _line(canvas, int(xs[start]), int(ys[start]), int(xs[start + 1]), int(ys[start + 1]), color)
            for x, y in zip(xs[finite], ys[finite], strict=True): _marker(canvas, int(x), int(y), color)
    _png(path, canvas)


def annotate_chart(path: Path, title: str, panels: list[str]) -> None:
    """Add compact labels with the already-installed ImageMagick, when available."""
    convert = shutil.which("convert")
    if not convert:
        return  # ponytail: unlabeled fallback; add a plotting dependency only if native convert disappears.
    args = [convert, str(path), "-background", "white", "-gravity", "north", "-splice", "0x32", "-gravity", "northwest", "-fill", "black", "-pointsize", "15", "-annotate", "+10+18", title]
    for index, label in enumerate(panels):
        row, col = divmod(index, 3)
        args.extend(["-pointsize", "12", "-annotate", f"+{35 + col * 390}+{45 + row * 270}", label])
    args.extend(["-gravity", "south", "-splice", "0x22", "-pointsize", "12", "-annotate", "+0+5", "x: k = 2, 3, 4, 5, 6, 7, 8   |   blue: Train   orange: Test", str(path)])
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def save_figures(primary: pd.DataFrame, figures_dir: Path) -> None:
    # stdlib fallback: panel order is KMEANS/GMM (rows) × standard/robust/minmax (columns).
    for metric, filename in (("silhouette", "cluster_silhouette_train_vs_test.png"), ("dbi", "cluster_dbi_train_vs_test.png")):
        panels = []
        for algorithm in ALGORITHMS:
            for scaler in SCALERS:
                subset = primary.loc[(primary["algorithm"] == algorithm) & (primary["scaler"] == scaler)].sort_values("k")
                panels.append([(subset[f"{metric}_train"].to_numpy(), (31, 119, 180)), (subset[f"{metric}_test"].to_numpy(), (255, 127, 14))])
        path = figures_dir / filename
        _multi_panel_png(path, panels, rows=2, cols=3)
        annotate_chart(path, f"{metric.upper()} — Train vs Test", ["KMeans · standard", "KMeans · robust", "KMeans · minmax", "GMM · standard", "GMM · robust", "GMM · minmax"])
    inertia_panels = []
    for scaler in SCALERS:
        subset = primary.loc[(primary["algorithm"] == "kmeans") & (primary["scaler"] == scaler)].sort_values("k")
        inertia_panels.append([(subset["inertia_train"].to_numpy(), (31, 119, 180))])
    path = figures_dir / "cluster_kmeans_inertia_elbow.png"
    _multi_panel_png(path, inertia_panels, rows=1, cols=3)
    annotate_chart(path, "K-MEANS TRAIN INERTIA — Elbow", ["standard", "robust", "minmax"])


def build_outputs(root: Path = ROOT) -> dict[str, Any]:
    started = time.monotonic()
    metrics_dir, figures_dir, manifest_dir = root / "outputs/metrics", root / "outputs/figures", root / "outputs/manifests"
    for directory in (metrics_dir, figures_dir, manifest_dir):
        directory.mkdir(parents=True, exist_ok=True)
    inputs, feature_columns, source_hashes = load_inputs(root)
    train_sample, test_sample = deterministic_indices(TRAIN_ROWS), deterministic_indices(TEST_ROWS)

    run_rows: list[dict[str, Any]] = []
    label_cache: dict[tuple[str, str, int, int], tuple[np.ndarray, np.ndarray]] = {}
    for scaler in SCALERS:
        x_train, x_test = inputs[scaler]
        for algorithm in ALGORITHMS:
            for k in K_VALUES:
                for seed in SEEDS:
                    row, labels_train, labels_test = run_one(scaler, algorithm, k, seed, x_train, x_test, train_sample, test_sample)
                    run_rows.append(row)
                    label_cache[(scaler, algorithm, k, seed)] = (labels_train, labels_test)
                    print(
                        f"RUN scaler={scaler} algorithm={algorithm} k={k} seed={seed} "
                        f"sil_train={row['silhouette_train']:.6f} sil_test={row['silhouette_test']:.6f} "
                        f"dbi_train={row['dbi_train']:.6f} dbi_test={row['dbi_test']:.6f}", flush=True,
                    )
    if len(run_rows) != 126:
        raise AssertionError(f"expected 126 runs, got {len(run_rows)}")
    all_results = pd.DataFrame(run_rows)
    primary = all_results.loc[all_results["seed"] == PRIMARY_SEED].copy()
    ledger = build_ledger(run_rows, label_cache)
    if len(primary) != 42 or len(ledger) != 42:
        raise AssertionError("primary and verdict row counts must each be 42")

    all_path = metrics_dir / "clustering_results_all.csv"
    primary_path = metrics_dir / "clustering_summary_primary42.csv"
    ledger_path = metrics_dir / "verdict_ledger.csv"
    all_results.to_csv(all_path, index=False)
    primary.to_csv(primary_path, index=False)
    ledger.to_csv(ledger_path, index=False)
    save_figures(primary, figures_dir)
    figure_paths = [
        figures_dir / "cluster_silhouette_train_vs_test.png", figures_dir / "cluster_dbi_train_vs_test.png",
        figures_dir / "cluster_kmeans_inertia_elbow.png",
    ]
    output_paths = [all_path, primary_path, ledger_path, *figure_paths]
    verdict_counts = ledger["verdict"].value_counts().to_dict()
    manifest = {
        "phase": "C", "run_count": len(run_rows), "primary_seed_run_count": len(primary), "verdict_count": len(ledger),
        "feature_count": len(feature_columns), "fit_scope": "train_only", "train_rows": TRAIN_ROWS, "test_rows": TEST_ROWS,
        "grid": {"scalers": list(SCALERS), "algorithms": list(ALGORITHMS), "k_values": list(K_VALUES), "seeds": list(SEEDS)},
        "silhouette": {"sample_size": SILHOUETTE_SAMPLE_SIZE, "seed": SILHOUETTE_SEED, "train_indices_sha256": index_hash(train_sample), "test_indices_sha256": index_hash(test_sample)},
        "thresholds": {"collapse_proportion_lt": COLLAPSE_PROPORTION, "silhouette_range_gt": 0.05, "dbi_relative_range_gt": 0.20, "pairwise_ari_lt": 0.80},
        "status_counts": {key: int(value) for key, value in verdict_counts.items()},
        "primary_collapse_runs": int((primary["collapse_train"] | primary["collapse_test"]).sum()),
        "primary_non_convergent_runs": int(primary["non_convergent"].sum()),
        "input_sha256": source_hashes, "output_sha256": {str(path.relative_to(root)): sha256_file(path) for path in output_paths},
        "runtime_seconds": round(time.monotonic() - started, 3),
    }
    manifest_path = manifest_dir / "phase_c_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(
        f"PASS phase=C runs={len(run_rows)} verdicts={len(ledger)} "
        f"eligible={manifest['status_counts'].get('ELIGIBLE', 0)} "
        f"no_winner={manifest['status_counts'].get('NO-WINNER', 0)} runtime_seconds={manifest['runtime_seconds']:.3f}",
        flush=True,
    )
    return manifest


def main() -> None:
    build_outputs()


if __name__ == "__main__":
    main()
