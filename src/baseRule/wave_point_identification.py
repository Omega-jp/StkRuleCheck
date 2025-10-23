#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
波段高低點檢查工具
提供 `check_wave_points` 介面供買入規則驗證流程呼叫。
"""

from __future__ import annotations

from typing import List

import pandas as pd

from .waving_point_identification import (
    WavingPointIdentifier,
    identify_waving_points,
)

__all__: List[str] = [
    "check_wave_points",
    "identify_waving_points",
    "WavingPointIdentifier",
]


def check_wave_points(df: pd.DataFrame, debug: bool = False) -> pd.DataFrame:
    """
    基於轉折點資訊產出波段高低點結果。

    Args:
        df: 包含 K 線資料與 `turning_high_point`、`turning_low_point` 欄位的 DataFrame。
            索引需為日期（DatetimeIndex 或可轉為日期的索引）。
        debug: 是否啟用詳細偵錯輸出。

    Returns:
        DataFrame: 具備波段標記與趨勢狀態的表格。
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "wave_high_point",
                "wave_low_point",
                "trend_type",
                "pending_reversal",
            ]
        )

    turning_columns = ["turning_high_point", "turning_low_point"]
    missing_columns = set(turning_columns) - set(df.columns)
    if missing_columns:
        raise ValueError(
            "DataFrame 必須包含轉折點欄位: "
            f"{', '.join(sorted(missing_columns))}"
        )

    data = df.copy()
    if "date" in data.columns:
        data = data.drop(columns=["date"])
    if not isinstance(data.index, pd.DatetimeIndex):
        data.index = pd.to_datetime(data.index, errors="coerce")
    data = data.sort_index()

    turning_points = data[turning_columns].fillna("").reset_index()
    index_name = data.index.name or "index"
    turning_points.rename(columns={index_name: "date"}, inplace=True)
    duplicate_date_cols = [
        col for col in turning_points.columns[1:] if col == "date"
    ]
    if duplicate_date_cols:
        turning_points.drop(columns=duplicate_date_cols, inplace=True)

    turning_points["date"] = pd.to_datetime(
        turning_points["date"],
        errors="coerce",
    )
    turning_points = turning_points[turning_points["date"].notna()]
    turning_points["date"] = turning_points["date"].dt.strftime("%Y-%m-%d")

    wave_points = identify_waving_points(data, turning_points, debug=debug)

    expected_columns = [
        "date",
        "wave_high_point",
        "wave_low_point",
        "trend_type",
        "pending_reversal",
    ]
    for col in expected_columns:
        if col not in wave_points.columns:
            wave_points[col] = ""

    wave_points["date"] = pd.to_datetime(
        wave_points["date"],
        errors="coerce",
    ).dt.strftime("%Y-%m-%d")

    return wave_points[expected_columns].fillna("")
