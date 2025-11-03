#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
下降趨勢線突破買進訊號檢查模組 - 日線版
================================================

根據最新規格：
1. 僅檢查 K 線收盤是否由下往上突破趨勢線（Cross Up）
2. 不再設定突破幅度或量能放大等額外門檻，但仍保留資訊供統計使用

原稿：Claude
更新：2025-11-01
"""


from __future__ import annotations

from typing import Dict, Optional
import pandas as pd

from src.baseRule.turning_point_identification import check_turning_points
from src.baseRule.wave_point_identification import check_wave_points
from .long_term_descending_trendline import identify_descending_trendlines



def check_breakthrough_descending_trendline(
    df: pd.DataFrame,
    trendlines: dict,
    **deprecated_kwargs,
) -> pd.DataFrame:
    """
    Detect breakouts where the daily close crosses a descending trendline from below.

    The check now follows the simplified specification:
        1. Require only a close cross-up event (previous close ≤ line, current close > line)
        2. Do not gate on minimum breakout percentage or volume expansion
        3. Still capture breakout percentage and volume ratio for reporting/statistics
        4. Each trendline can generate at most one breakout signal
    """
    if deprecated_kwargs:
        ignored_keys = ", ".join(sorted(deprecated_kwargs.keys()))
        print(f"WARNING: check_breakthrough_descending_trendline ignores parameters: {ignored_keys}")

    if df is None or df.empty:
        return pd.DataFrame()

    if "Close" not in df.columns:
        raise ValueError("DataFrame must contain 'Close' column")

    volume_ma = None
    if "Volume" in df.columns:
        volume_ma = df["Volume"].rolling(window=20, min_periods=5).mean()

    all_lines = trendlines.get("all_lines", [])

    if len(all_lines) == 0:
        return _create_empty_results(df)

    results = []
    used_breakthrough_lines = set()

    for i in range(len(df)):
        date = df.index[i]
        close_price = df.iloc[i]["Close"]

        breakthrough_check = ""
        breakthrough_type = ""
        breakthrough_pct = 0.0
        volume_ratio = 0.0
        trendline_price = 0.0
        signal_strength = 0

        if volume_ma is not None:
            current_volume = df.iloc[i].get("Volume", 0.0)
            avg_volume = volume_ma.iloc[i]
            if not pd.isna(avg_volume) and avg_volume > 0:
                volume_ratio = current_volume / avg_volume

        valid_breakthroughs = []

        for line in all_lines:
            line_key = _build_line_key(line)
            if line_key in used_breakthrough_lines:
                continue

            current_line_price = line["intercept"] + line["slope"] * i

            if i == 0:
                continue

            previous_line_price = line["intercept"] + line["slope"] * (i - 1)
            previous_close_price = df.iloc[i - 1]["Close"]

            if pd.isna(previous_close_price) or pd.isna(previous_line_price):
                continue

            if previous_close_price > previous_line_price:
                continue

            if close_price <= current_line_price:
                continue

            pct = ((close_price - current_line_price) / current_line_price) * 100.0

            valid_breakthroughs.append({
                "line": line,
                "breakthrough_pct": pct,
                "volume_ratio": volume_ratio,
                "line_price": current_line_price,
            })

        if valid_breakthroughs:
            best_breakthrough = _select_best_breakthrough(valid_breakthroughs)

            if best_breakthrough:
                breakthrough_check = "O"
                line = best_breakthrough["line"]
                breakthrough_type = line["type"]
                breakthrough_pct = best_breakthrough["breakthrough_pct"]
                volume_ratio = best_breakthrough["volume_ratio"]
                trendline_price = best_breakthrough["line_price"]
                signal_strength = _calculate_signal_strength(
                    line,
                    breakthrough_pct,
                    volume_ratio,
                )
                used_breakthrough_lines.add(_build_line_key(line))

        results.append({
            "date": date.strftime("%Y-%m-%d") if isinstance(date, pd.Timestamp) else str(date),
            "breakthrough_check": breakthrough_check,
            "breakthrough_type": breakthrough_type,
            "breakthrough_pct": round(breakthrough_pct, 2),
            "volume_ratio": round(volume_ratio, 2),
            "trendline_price": round(trendline_price, 2),
            "close_price": round(close_price, 2),
            "signal_strength": signal_strength,
        })

    return pd.DataFrame(results)


def _create_empty_results(df: pd.DataFrame) -> pd.DataFrame:
    """創建空的結果DataFrame"""
    results = []
    for i in range(len(df)):
        date = df.index[i]
        results.append({
            'date': date.strftime('%Y-%m-%d') if isinstance(date, pd.Timestamp) else str(date),
            'breakthrough_check': '',
            'breakthrough_type': '',
            'breakthrough_pct': 0.0,
            'volume_ratio': 0.0,
            'trendline_price': 0.0,
            'close_price': round(df.iloc[i]['Close'], 2),
            'signal_strength': 0
        })
    return pd.DataFrame(results)


def _select_best_breakthrough(valid_breakthroughs: list) -> dict:
    """
    從多個有效突破中選擇最佳的一個
    
    優先級：
    1. 水平壓力線（創新高）> 斜向趨勢線
    2. 突破幅度適中（不要太極端）
    3. 成交量放大適中
    """
    if not valid_breakthroughs:
        return None
    
    # 計算每個突破的得分
    def breakthrough_score(bt):
        line = bt['line']
        score = 0.0
        
        # 1. 趨勢線類型得分
        if line['type'] == 'horizontal_resistance':
            score += 100.0  # 水平壓力線最優先（創新高）
        elif line['type'] == 'diagonal_descending':
            score += 50.0
        
        # 2. 突破幅度得分（1-3%最佳，過高或過低都扣分）
        pct = bt['breakthrough_pct']
        if 1.0 <= pct <= 3.0:
            score += 20.0
        elif 0.5 <= pct < 1.0:
            score += 10.0
        elif 3.0 < pct <= 5.0:
            score += 15.0
        else:
            score += 5.0
        
        # 3. 成交量得分（1.5-2.5倍最佳）
        vol_ratio = bt['volume_ratio']
        if 1.5 <= vol_ratio <= 2.5:
            score += 15.0
        elif 1.2 <= vol_ratio < 1.5:
            score += 10.0
        elif 2.5 < vol_ratio <= 4.0:
            score += 10.0
        else:
            score += 5.0
        
        return score
    
    # 選擇得分最高的突破
    best = max(valid_breakthroughs, key=breakthrough_score)
    return best


def _calculate_signal_strength(line: dict, breakthrough_pct: float, volume_ratio: float) -> int:
    """
    計算信號強度（1-5分）
    
    評分標準：
    - 5分：水平壓力線突破 + 大幅突破 + 大量放量
    - 4分：水平壓力線突破 或 斜線大幅突破
    - 3分：一般突破
    - 2分：小幅突破
    - 1分：勉強突破
    """
    score = 1
    
    # 基礎分數
    if line['type'] == 'horizontal_resistance':
        score += 2  # 水平壓力線 +2分
    else:
        score += 1  # 斜向趨勢線 +1分
    
    # 突破幅度加分
    if breakthrough_pct >= 2.0:
        score += 1
    elif breakthrough_pct >= 1.0:
        score += 0.5
    
    # 成交量加分
    if volume_ratio >= 2.0:
        score += 1
    elif volume_ratio >= 1.5:
        score += 0.5
    
    # 確保在1-5分範圍內
    return max(1, min(5, int(round(score))))


def _build_line_key(line: dict) -> tuple:
    """建立趨勢線的唯一識別 key，避免重複發出信號"""
    return (
        line.get('type'),
        line.get('start_idx'),
        line.get('end_idx'),
        round(line.get('slope', 0.0), 6),
        round(line.get('intercept', 0.0), 3)
    )


def check_descending_trendline(
    df: pd.DataFrame,
    turning_points_df: Optional[pd.DataFrame] = None,
    wave_points_df: Optional[pd.DataFrame] = None,
    *,
    debug: bool = False,
    trendline_kwargs: Optional[Dict] = None,
    breakthrough_kwargs: Optional[Dict] = None,
) -> pd.DataFrame:
    """
    一站式入口：先識別波段高點，再生成下降趨勢線並檢查突破。

    Args:
        df: 原始 K 線資料，索引需為日期。
        turning_points_df: 已計算的轉折點結果（可選，未提供會自動計算）。
        wave_points_df: 已計算的波段點結果（可選，未提供會自動計算）。
        debug: 是否輸出波段偵測除錯訊息。
        trendline_kwargs: 傳給 `identify_descending_trendlines` 的參數。
        breakthrough_kwargs: 傳給 `check_breakthrough_descending_trendline` 的參數。

    Returns:
        DataFrame: 包含突破檢查結果的表格。
    """
    if df is None or df.empty:
        return pd.DataFrame()

    df_sorted = df.sort_index()

    if turning_points_df is None or turning_points_df.empty:
        turning_points_df = check_turning_points(df_sorted)

    if wave_points_df is None or wave_points_df.empty:
        wave_points_df = _prepare_wave_points(df_sorted, turning_points_df, debug=debug)

    trendline_kwargs = trendline_kwargs or {}
    trendlines = identify_descending_trendlines(
        df_sorted,
        wave_points_df,
        **trendline_kwargs,
    )

    breakthrough_kwargs = breakthrough_kwargs or {}
    result_df = check_breakthrough_descending_trendline(
        df_sorted,
        trendlines,
        **breakthrough_kwargs,
    )

    if result_df.empty:
        return result_df

    column_mapping = {
        "breakthrough_check": "descending_trendline_breakthrough_check",
        "breakthrough_type": "descending_trendline_breakthrough_type",
        "breakthrough_pct": "descending_trendline_breakthrough_pct",
        "volume_ratio": "descending_trendline_volume_ratio",
        "trendline_price": "descending_trendline_trendline_price",
        "close_price": "descending_trendline_close_price",
        "signal_strength": "descending_trendline_signal_strength",
    }

    return result_df.rename(columns=column_mapping)


def _prepare_wave_points(
    df: pd.DataFrame,
    turning_points_df: pd.DataFrame,
    *,
    debug: bool = False,
) -> pd.DataFrame:
    """依據轉折點結果產出波段點資料。"""
    if turning_points_df is None or turning_points_df.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "wave_high_point",
                "wave_low_point",
                "trend_type",
                "pending_reversal",
            ]
        )

    df_reset = df.reset_index()
    index_col = df_reset.columns[0]
    df_reset[index_col] = pd.to_datetime(df_reset[index_col], errors="coerce")

    turning_points = turning_points_df.copy()
    if "date" not in turning_points.columns:
        raise ValueError("turning_points_df 缺少 'date' 欄位")

    turning_points = turning_points.dropna(subset=["date"])
    turning_points["date"] = pd.to_datetime(
        turning_points["date"],
        errors="coerce",
    )
    turning_points = turning_points.rename(columns={"date": "turning_date"})

    merged = pd.merge(
        df_reset,
        turning_points,
        left_on=index_col,
        right_on="turning_date",
        how="left",
    )

    if "turning_high_point" not in merged.columns:
        merged["turning_high_point"] = ""
    else:
        merged["turning_high_point"] = merged["turning_high_point"].fillna("")

    if "turning_low_point" not in merged.columns:
        merged["turning_low_point"] = ""
    else:
        merged["turning_low_point"] = merged["turning_low_point"].fillna("")

    merged = merged.drop(columns=["turning_date"])
    merged.set_index(index_col, inplace=True)

    return check_wave_points(merged, debug=debug)


if __name__ == "__main__":
    print("下降趨勢線突破買入規則檢查模組 - 規格書版本")
    print("=" * 60)
    print("突破判定標準：")
    print("  1. 收盤價突破趨勢線（非盤中價）")
    print("  2. 突破幅度 ≥ 0.5%")
    print("  3. 成交量 ≥ 20日均量 × 1.2倍（可選）")
    print("\n使用方式：")
    print("  from breakthrough_descending_trendline import check_breakthrough_descending_trendline")
    print("  signals = check_breakthrough_descending_trendline(df, trendlines)")
