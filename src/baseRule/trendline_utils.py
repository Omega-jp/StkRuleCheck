"""Utility helpers for trendline calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd


def segment_respects_line(
    df: pd.DataFrame,
    start_idx: int,
    end_idx: int,
    slope: float,
    intercept: float,
    tolerance: float = 1e-6,
) -> bool:
    """Return True if all highs between start and end stay under the descending line."""
    if end_idx <= start_idx:
        return True

    segment = df.iloc[start_idx : end_idx + 1]
    highs = segment["High"].to_numpy(dtype=float)
    if highs.size == 0:
        return True

    idx_values = np.arange(start_idx, end_idx + 1, dtype=float)
    line_values = intercept + slope * idx_values

    return bool(np.all(highs <= line_values + tolerance))
