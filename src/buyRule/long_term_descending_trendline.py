import math
from typing import Dict, List

import numpy as np
import pandas as pd
from ..baseRule.trendline_utils import segment_respects_line


def identify_long_term_descending_trendlines(
    df: pd.DataFrame,
    turning_points_df: pd.DataFrame,
    min_days_long_term: int = 180,
    min_points_short_term: int = 3,
) -> Dict[str, List[dict]]:
    """Identify descending trendlines from supplied turning points.

    Args:
        df (pd.DataFrame): OHLC dataframe indexed by date and containing a ``High`` column.
        turning_points_df (pd.DataFrame): Output from ``identify_turning_points``.
        min_days_long_term (int): Minimum calendar days for a long-term line.
        min_points_short_term (int): Minimum turning points required for short-term regression lines.

    Returns:
        dict: ``{"long_term_lines": [...], "short_term_lines": [...], "all_lines": [...]}``.
    """
    if df is None or df.empty:
        return {"long_term_lines": [], "short_term_lines": [], "all_lines": []}

    if turning_points_df is None or turning_points_df.empty:
        return {"long_term_lines": [], "short_term_lines": [], "all_lines": []}

    if "High" not in df.columns:
        raise ValueError("DataFrame must contain 'High' column to build trendlines.")

    index_keys = _build_index_key_map(df.index)
    high_points = _collect_high_turning_points(df, turning_points_df, index_keys)

    if len(high_points) < 2:
        return {"long_term_lines": [], "short_term_lines": [], "all_lines": []}

    long_term_lines = _find_long_term_lines(df, high_points, min_days_long_term)
    short_term_lines = _find_short_term_lines(df, high_points, min_days_long_term, min_points_short_term)

    all_lines = sorted(long_term_lines + short_term_lines, key=lambda line: (line["start_idx"], line["end_idx"]))
    return {
        "long_term_lines": long_term_lines,
        "short_term_lines": short_term_lines,
        "all_lines": all_lines,
    }


def _build_index_key_map(index: pd.Index) -> Dict[str, int]:
    if isinstance(index, pd.DatetimeIndex):
        keys = index.strftime("%Y-%m-%d")
    else:
        keys = index.astype(str)
    return {key: pos for pos, key in enumerate(keys)}


def _collect_high_turning_points(
    df: pd.DataFrame,
    turning_points_df: pd.DataFrame,
    index_keys: Dict[str, int],
) -> List[dict]:
    points: List[dict] = []
    for _, row in turning_points_df.iterrows():
        if row.get("turning_high_point") != "O":
            continue

        date_value = row.get("date")
        if pd.isna(date_value):
            continue

        date_value = pd.to_datetime(date_value, errors="coerce")
        if pd.isna(date_value):
            continue

        date_key = date_value.strftime("%Y-%m-%d")
        pos = index_keys.get(date_key)
        if pos is None:
            continue

        high_price = float(df.iloc[pos]["High"])
        points.append({"idx": pos, "date": date_value.normalize(), "price": high_price})

    points.sort(key=lambda p: p["idx"])
    return points


def _find_long_term_lines(
    df: pd.DataFrame,
    high_points: List[dict],
    min_days_long_term: int,
) -> List[dict]:
    lines: List[dict] = []
    seen_pairs = set()

    for i, point1 in enumerate(high_points):
        for j in range(i + 1, len(high_points)):
            point2 = high_points[j]
            idx_span = point2["idx"] - point1["idx"]
            if idx_span <= 0:
                continue

            days_span = _calculate_days_span(df, point1["idx"], point2["idx"])
            if days_span < min_days_long_term:
                continue

            if point2["price"] >= point1["price"]:
                continue

            slope = (point2["price"] - point1["price"]) / idx_span
            if slope >= 0:
                continue

            intercept = point1["price"] - slope * point1["idx"]
            if not segment_respects_line(df, point1["idx"], point2["idx"], slope, intercept):
                continue

            r_squared = _segment_r_squared(df, point1["idx"], point2["idx"], slope, intercept)
            key = (point1["idx"], point2["idx"])
            if key in seen_pairs:
                continue

            seen_pairs.add(key)
            lines.append(
                _build_line(
                    line_type="long_term_two_point",
                    df=df,
                    start_idx=point1["idx"],
                    end_idx=point2["idx"],
                    slope=slope,
                    intercept=intercept,
                    r_squared=r_squared,
                    points=[point1, point2],
                    days_span=days_span,
                )
            )

    return lines


def _find_short_term_lines(
    df: pd.DataFrame,
    high_points: List[dict],
    min_days_long_term: int,
    min_points_short_term: int,
) -> List[dict]:
    lines: List[dict] = []
    if len(high_points) < min_points_short_term:
        return lines

    seen_segments = set()
    total_points = len(high_points)

    for window_size in range(min_points_short_term, total_points + 1):
        for start in range(0, total_points - window_size + 1):
            segment = high_points[start : start + window_size]
            start_idx = segment[0]["idx"]
            end_idx = segment[-1]["idx"]
            days_span = _calculate_days_span(df, start_idx, end_idx)
            if days_span >= min_days_long_term:
                continue

            if not _is_strictly_descending(segment):
                continue

            x = np.array([point["idx"] for point in segment], dtype=float)
            if len(np.unique(x)) < 2:
                continue

            y = np.array([point["price"] for point in segment], dtype=float)
            slope, intercept = np.polyfit(x, y, 1)
            if slope >= 0:
                continue

            if not segment_respects_line(df, start_idx, end_idx, slope, intercept):
                continue

            r_squared = _segment_r_squared(df, start_idx, end_idx, slope, intercept)

            key = tuple(point["idx"] for point in segment)
            if key in seen_segments:
                continue

            seen_segments.add(key)
            lines.append(
                _build_line(
                    line_type="short_term_multi_point",
                    df=df,
                    start_idx=start_idx,
                    end_idx=end_idx,
                    slope=slope,
                    intercept=intercept,
                    r_squared=r_squared,
                    points=segment,
                    days_span=days_span,
                )
            )

    return lines


def _build_line(
    line_type: str,
    df: pd.DataFrame,
    start_idx: int,
    end_idx: int,
    slope: float,
    intercept: float,
    r_squared: float,
    points: List[dict],
    days_span: int,
) -> dict:
    start_date = pd.to_datetime(df.index[start_idx])
    end_date = pd.to_datetime(df.index[end_idx])

    return {
        "type": line_type,
        "start_idx": start_idx,
        "end_idx": end_idx,
        "start_date": start_date,
        "end_date": end_date,
        "days_span": days_span,
        "slope": slope,
        "equation": {"slope": slope, "intercept": intercept},
        "r_squared": float(r_squared),
        "points": [{"date": p["date"], "price": p["price"]} for p in points],
    }


def _calculate_days_span(df: pd.DataFrame, start_idx: int, end_idx: int) -> int:
    if end_idx <= start_idx:
        return 0

    start_date = pd.to_datetime(df.index[start_idx])
    end_date = pd.to_datetime(df.index[end_idx])
    if pd.isna(start_date) or pd.isna(end_date):
        return end_idx - start_idx

    return max(0, (end_date - start_date).days)


def _is_strictly_descending(points: List[dict]) -> bool:
    return all(points[i + 1]["price"] <= points[i]["price"] for i in range(len(points) - 1))



def _segment_r_squared(
    df: pd.DataFrame,
    start_idx: int,
    end_idx: int,
    slope: float,
    intercept: float,
) -> float:
    if end_idx <= start_idx:
        return 1.0

    x = np.arange(start_idx, end_idx + 1, dtype=float)
    high_values = df.iloc[start_idx : end_idx + 1]["High"].to_numpy(dtype=float)
    if high_values.size < 2:
        return 1.0

    predicted = intercept + slope * x
    ss_res = float(np.sum((high_values - predicted) ** 2))
    ss_tot = float(np.sum((high_values - np.mean(high_values)) ** 2))

    if math.isclose(ss_tot, 0.0):
        return 1.0

    return max(0.0, 1.0 - ss_res / ss_tot)
