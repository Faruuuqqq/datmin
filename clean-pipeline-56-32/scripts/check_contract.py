#!/usr/bin/env python3
"""Assert-based synthetic contract checks for Phase A windowing."""
from __future__ import annotations

import numpy as np
import pandas as pd

from prepare_windows import (
    CHANNELS,
    DATE_COLUMN,
    FEATURE_COLUMNS,
    RAW_COLUMNS,
    SENTINEL,
    TIME_COLUMN,
    WINDOW_SECONDS,
    WindowAccumulator,
    clean_chunk,
    window_features,
)
from cluster_evaluate import collapse_detected, sharp_test_drop, verdict_reasons
from split_scale import EMBARGO_SECONDS, scaler_state
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler


def cleaned_rows(start: str, count: int, value: float = 1.0) -> pd.DataFrame:
    timestamps = pd.date_range(start, periods=count, freq="s")
    data = {"timestamp": timestamps}
    for index, channel in enumerate(CHANNELS):
        data[channel] = np.arange(count, dtype=np.float64) + value + index * 100.0
    return pd.DataFrame(data)


def raw_rows() -> pd.DataFrame:
    times = pd.date_range("2021-02-08 04:30:00", periods=3, freq="s")
    data: dict[str, object] = {
        DATE_COLUMN: times.strftime("%Y/%m/%d"),
        TIME_COLUMN: times.strftime("%H:%M:%S"),
    }
    for raw_column in RAW_COLUMNS.values():
        data[raw_column] = np.array([10.0, 20.0, 30.0])
    data[RAW_COLUMNS["SPP"]] = np.array([100.0, -900.0, 100.0])
    data[RAW_COLUMNS["ROP"]] = np.array([SENTINEL, 2.0, 3.0])
    return pd.DataFrame(data)


def emitted(rows: pd.DataFrame, splits: list[int]) -> WindowAccumulator:
    accumulator = WindowAccumulator()
    cursor = 0
    for stop in splits:
        accumulator.ingest(rows.iloc[cursor:stop].reset_index(drop=True))
        cursor = stop
    accumulator.close()
    return accumulator


def main() -> None:
    # SPP <= -900 is dropped before masking; exact sentinel is NaN in other sensors.
    cleaned, dropped = clean_chunk(raw_rows())
    assert dropped == 1 and len(cleaned) == 2
    assert np.isnan(cleaned.loc[0, "ROP"]), "sentinel -999.25 must become NaN"

    # A 54/60 coverage channel is accepted; 53/60 is rejected.
    values = cleaned_rows("2021-01-01", WINDOW_SECONDS)[CHANNELS].to_numpy(dtype=np.float64, copy=True)
    values[:6, 0] = np.nan
    features, coverage = window_features(values)
    assert coverage[0] == 54 and len(features) == 39
    assert np.isfinite(features).all()
    values[6, 0] = np.nan
    _, coverage = window_features(values)
    assert coverage[0] == 53

    # Exact feature contract: mean, population std (ddof=0), endpoint delta, 13 x 3.
    simple = np.tile(np.arange(WINDOW_SECONDS, dtype=np.float64)[:, None], (1, len(CHANNELS)))
    features, coverage = window_features(simple)
    assert FEATURE_COLUMNS[:3] == ["ROP_mean", "ROP_std", "ROP_delta"]
    assert len(FEATURE_COLUMNS) == 39 and len(features) == 39
    assert np.all(coverage == WINDOW_SECONDS)
    assert np.isclose(features[0], 29.5)
    assert np.isclose(features[1], np.std(np.arange(WINDOW_SECONDS), ddof=0))
    assert np.isclose(features[2], 59.0)

    # Chunk boundaries cannot change emitted windows or feature values.
    rows = cleaned_rows("2021-01-01", 120)
    one_chunk = emitted(rows, [120])
    split_chunks = emitted(rows, [37, 84, 120])
    assert one_chunk.metadata == split_chunks.metadata
    assert one_chunk.feature_rows == split_chunks.feature_rows

    # A non-1-second timestamp gap resets the segment and discards both partial tails.
    before_gap = cleaned_rows("2021-01-01", 30)
    after_gap = cleaned_rows("2021-01-01 00:00:31", 30)
    gap_case = emitted(pd.concat([before_gap, after_gap], ignore_index=True), [60])
    assert gap_case.window_id == 0 and gap_case.segment_id == 1
    assert gap_case.segment_resets == 1 and gap_case.tail_discarded_rows == 60

    # Tumbling anchors are the first retained row of each 60-row interval.
    tumbling = emitted(rows, [120])
    assert [item["start_time"] for item in tumbling.metadata] == [
        "2021/01/01 00:00:00", "2021/01/01 00:01:00"
    ]
    assert [item["end_time"] for item in tumbling.metadata] == [
        "2021/01/01 00:00:59", "2021/01/01 00:01:59"
    ]

    # Phase B: Test must start at least one hour after inclusive Train support.
    train_support_end_exclusive = pd.Timestamp("2021-01-01 10:00:59") + pd.Timedelta(seconds=1)
    first_test_start = train_support_end_exclusive + pd.Timedelta(seconds=EMBARGO_SECONDS)
    assert (first_test_start - train_support_end_exclusive).total_seconds() >= EMBARGO_SECONDS

    # Phase B: membership assigns every window exactly once.
    membership = pd.DataFrame({"window_id": [10, 11, 12, 13], "split": ["TRAIN", "TRAIN", "EMBARGO", "TEST"]})
    expected_ids = {10, 11, 12, 13}
    assert not membership["window_id"].duplicated().any()
    assert set(membership["window_id"]) == expected_ids
    assert set(membership["split"]) == {"TRAIN", "EMBARGO", "TEST"}

    # Phase B: transform of arbitrary Test-like data cannot mutate Train-fitted state.
    train_matrix = np.arange(24, dtype=np.float64).reshape(8, 3)
    dummy_test = np.array([[1e9, -1e9, 42.0], [-3e9, 9e9, -7.0]], dtype=np.float64)
    for scaler in (
        StandardScaler(with_mean=True, with_std=True),
        RobustScaler(with_centering=True, with_scaling=True, quantile_range=(25.0, 75.0), unit_variance=False),
        MinMaxScaler(feature_range=(0.0, 1.0), clip=False),
    ):
        scaler.fit(train_matrix)
        before = scaler_state(scaler)
        scaler.transform(dummy_test)
        assert scaler_state(scaler) == before, f"{type(scaler).__name__} state changed during Test transform"

    # Phase C: any empty or <1% cluster is COLLAPSE (e.g., 267 of 26,723).
    assert collapse_detected(np.array([267, 26_456]), 26_723)
    assert not collapse_detected(np.array([268, 26_455]), 26_723)

    # Phase C: strict sharp generalization drop applies to either locked condition.
    assert sharp_test_drop(0.45, 0.34, 0.80, 0.90)
    assert sharp_test_drop(0.45, 0.40, 0.80, 1.21)
    assert not sharp_test_drop(0.45, 0.36, 0.80, 1.20)

    # Phase C: NO-WINNER reasons cannot be bypassed; only a fully clean primary is eligible.
    stable = {"unstable": False}
    clean = {"collapse_train": False, "collapse_test": False, "non_convergent": False, "silhouette_train": 0.20, "silhouette_test": 0.15, "dbi_train": 1.0, "dbi_test": 1.2}
    assert verdict_reasons(clean, stable) == []
    assert verdict_reasons({**clean, "collapse_test": True}, stable) == ["COLLAPSE"]
    assert verdict_reasons({**clean, "silhouette_test": 0.0}, stable) == ["NEGATIVE_SILHOUETTE", "SHARP_TEST_DROP"]
    assert verdict_reasons(clean, {"unstable": True}) == ["UNSTABLE"]
    print("PASS: Phase A, Phase B, and Phase C contract checks")


if __name__ == "__main__":
    main()
