#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TD Sequential (九轉) buy-rule helper.

This module implements a parameterised version of the TD Sequential setup counter
so that we can evaluate either the classic 「收盤價與四根前比較」規則，
or a faster variant（例如與兩根前比較）.

Key features
------------
* Supports configurable comparison offset (預設 2，用來滿足使用者指定的參數)。
* Reports買方與賣方 setup 的連續計數，並在數到 9 時回傳 'O' 作為訊號。
* 僅依賴 K 棒的收盤價，可直接餵入 append_indicator 之後的 DataFrame。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd


TDSequentialResultColumns = [
    "date",
    "td_setup_buy_count",
    "td_buy_signal",
    "td_setup_sell_count",
    "td_sell_signal",
]


@dataclass
class TDSequentialConfig:
    """Light-weight configuration holder for TD Sequential setup detection."""

    comparison_offset: int = 2  # e.g. compare with close two bars ago
    setup_length: int = 9  # 九轉 => 9 bars
    price_column: str = "Close"

    def validate(self) -> None:
        if self.comparison_offset < 1:
            raise ValueError("comparison_offset 必須 >= 1")
        if self.setup_length < 1:
            raise ValueError("setup_length 必須 >= 1")
        if not self.price_column:
            raise ValueError("price_column 不能是空字串")


def _format_date(idx) -> str:
    """Format index into YYYY-MM-DD string (fallback to str if not datetime)."""
    if hasattr(idx, "strftime"):
        return idx.strftime("%Y-%m-%d")
    return str(idx)


def compute_td_sequential_signals(
    df: pd.DataFrame,
    comparison_offset: int = 2,
    setup_length: int = 9,
    price_column: str = "Close",
) -> pd.DataFrame:
    """
    Calculate TD Sequential setup counts/signals with a configurable offset.

    Args:
        df (pd.DataFrame): Price DataFrame, must contain the price_column (default Close)
                           and preferably use DatetimeIndex.
        comparison_offset (int): How many bars back to compare against (original TD uses 4,
                                 request specifies 2).
        setup_length (int): Number of consecutive conditions required before marking a signal.
        price_column (str): Column name to use as the closing price.

    Returns:
        pd.DataFrame: Columns => date, td_setup_buy_count, td_buy_signal,
                                td_setup_sell_count, td_sell_signal
    """
    config = TDSequentialConfig(
        comparison_offset=comparison_offset,
        setup_length=setup_length,
        price_column=price_column,
    )
    config.validate()

    if df is None or df.empty:
        return pd.DataFrame(columns=TDSequentialResultColumns)

    if config.price_column not in df.columns:
        raise ValueError(f"DataFrame 缺少必要欄位 '{config.price_column}'")

    df_sorted = df.sort_index()
    price_series = pd.to_numeric(df_sorted[config.price_column], errors="coerce")

    buy_count = 0
    sell_count = 0
    results: List[dict] = []

    for idx, price in enumerate(price_series):
        prev_buy_count = buy_count
        prev_sell_count = sell_count
        date_str = _format_date(df_sorted.index[idx])

        prev_idx = idx - config.comparison_offset
        prev_price = price_series.iloc[prev_idx] if prev_idx >= 0 else None

        if pd.notna(price) and prev_price is not None and pd.notna(prev_price):
            if price < prev_price:
                buy_count = prev_buy_count + 1
            else:
                buy_count = 0

            if price > prev_price:
                sell_count = prev_sell_count + 1
            else:
                sell_count = 0
        else:
            buy_count = 0
            sell_count = 0

        if buy_count > config.setup_length:
            buy_count = config.setup_length
        if sell_count > config.setup_length:
            sell_count = config.setup_length

        buy_signal = (
            "O" if buy_count == config.setup_length and prev_buy_count < config.setup_length else ""
        )
        sell_signal = (
            "O" if sell_count == config.setup_length and prev_sell_count < config.setup_length else ""
        )

        results.append(
            {
                "date": date_str,
                "td_setup_buy_count": buy_count,
                "td_buy_signal": buy_signal,
                "td_setup_sell_count": sell_count,
                "td_sell_signal": sell_signal,
            }
        )

    return pd.DataFrame(results)


def check_td_sequential_buy_rule(
    df: pd.DataFrame,
    comparison_offset: int = 2,
    setup_length: int = 9,
    price_column: str = "Close",
) -> pd.DataFrame:
    """
    Wrapper used by validate_buy_rule / summarize_buy_rules so output columns
    follow the conventional *_check naming style.
    """
    detailed_df = compute_td_sequential_signals(
        df,
        comparison_offset=comparison_offset,
        setup_length=setup_length,
        price_column=price_column,
    )
    if detailed_df.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "td_sequential_buy_check",
                "td_setup_buy_count",
                "td_sequential_sell_check",
                "td_setup_sell_count",
            ]
        )

    result = detailed_df.copy()
    result["td_sequential_buy_check"] = result["td_buy_signal"]
    result["td_sequential_sell_check"] = result["td_sell_signal"]
    return result[
        [
            "date",
            "td_sequential_buy_check",
            "td_setup_buy_count",
            "td_sequential_sell_check",
            "td_setup_sell_count",
        ]
    ]


if __name__ == "__main__":
    # 簡單示範
    sample_dates = pd.date_range("2024-01-01", periods=12, freq="D")
    sample_prices = pd.DataFrame(
        {"Close": [12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]}, index=sample_dates
    )
    demo = compute_td_sequential_signals(sample_prices, comparison_offset=2, setup_length=9)
    print(demo.tail(5))
