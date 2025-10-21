#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下降趨勢線識別模組（基於波段高點）- 規格書版本
============================================

根據「突破下降趨勢線偵測規格書」實作：
1. 使用波段高點（非轉折高點）繪製趨勢線
2. 支援斜向下降趨勢線和水平壓力線
3. 嚴格驗證趨勢線有效性（無穿越檢查）

作者：Claude
日期：2025-01-21
"""

import math
from typing import Dict, List, Optional
import numpy as np
import pandas as pd


def identify_descending_trendlines(
    df: pd.DataFrame,
    wave_points_df: pd.DataFrame,
    lookback_days: int = 180,
    recent_end_days: int = 20,
    tolerance_pct: float = 0.1
) -> Dict[str, List[dict]]:
    """
    識別下降趨勢線（基於波段高點）
    
    根據規格書 2.1 斜向下降趨勢線：
    - 回溯期間：lookback_days（預設180天）
    - 終點限制：連線終點必須在最近 recent_end_days 天內
    - 連線規則：取任意兩個波段高點連線（起點在180天內，終點在最近20天內）
    - 斜率要求：斜率 ≤ 0（下降或水平）
    - 有效性驗證：區間內所有K線最高價不得穿越趨勢線（±0.1%誤差）
    
    根據規格書 2.2 水平壓力線：
    - 180天觀察窗口內的最高價
    
    Args:
        df: K線數據，需包含 'High' 欄位，索引為日期
        wave_points_df: 波段點識別結果，需包含 'wave_high_point' 欄位
        lookback_days: 回溯期間（預設180天）
        recent_end_days: 終點限制天數（預設20天）
        tolerance_pct: 誤差容忍百分比（預設0.1%）
    
    Returns:
        字典包含：
        - 'diagonal_lines': 斜向下降趨勢線列表
        - 'horizontal_line': 水平壓力線資訊（dict或None）
        - 'all_lines': 所有趨勢線的合併列表
    """
    
    if df is None or df.empty:
        return {"diagonal_lines": [], "horizontal_line": None, "all_lines": []}
    
    if wave_points_df is None or wave_points_df.empty:
        return {"diagonal_lines": [], "horizontal_line": None, "all_lines": []}
    
    if "High" not in df.columns:
        raise ValueError("DataFrame 必須包含 'High' 欄位")
    
    # 建立日期索引映射
    index_keys = _build_index_key_map(df.index)
    
    # 收集波段高點
    wave_high_points = _collect_wave_high_points(df, wave_points_df, index_keys)
    
    if len(wave_high_points) < 2:
        print(f"   ⚠️  波段高點數量不足（{len(wave_high_points)}個），無法繪製趨勢線")
        return {"diagonal_lines": [], "horizontal_line": None, "all_lines": []}
    
    print(f"   ✓ 找到 {len(wave_high_points)} 個波段高點")
    
    # 識別斜向下降趨勢線
    diagonal_lines = _find_diagonal_descending_lines(
        df, wave_high_points, lookback_days, recent_end_days, tolerance_pct
    )
    
    # 識別水平壓力線（180天最高價）
    horizontal_line = _find_horizontal_resistance_line(df, lookback_days)
    
    # 合併所有趨勢線
    all_lines = diagonal_lines.copy()
    if horizontal_line is not None:
        all_lines.append(horizontal_line)
    
    print(f"   ✓ 識別到 {len(diagonal_lines)} 條斜向趨勢線")
    if horizontal_line:
        print(f"   ✓ 識別到水平壓力線：{horizontal_line['resistance_price']:.2f}")
    
    return {
        "diagonal_lines": diagonal_lines,
        "horizontal_line": horizontal_line,
        "all_lines": all_lines
    }


def _build_index_key_map(index: pd.Index) -> Dict[str, int]:
    """建立日期字串到索引位置的映射"""
    if isinstance(index, pd.DatetimeIndex):
        keys = index.strftime("%Y-%m-%d")
    else:
        keys = index.astype(str)
    return {key: pos for pos, key in enumerate(keys)}


def _collect_wave_high_points(
    df: pd.DataFrame,
    wave_points_df: pd.DataFrame,
    index_keys: Dict[str, int],
) -> List[dict]:
    """
    收集所有波段高點
    
    Returns:
        波段高點列表，每個元素包含：
        - idx: 索引位置
        - date: 日期（pd.Timestamp）
        - price: 價格
    """
    points: List[dict] = []
    
    for _, row in wave_points_df.iterrows():
        # 檢查是否為波段高點
        if row.get("wave_high_point") != "O":
            continue
        
        # 提取日期
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
        
        # 提取該日最高價
        high_price = float(df.iloc[pos]["High"])
        
        points.append({
            "idx": pos,
            "date": date_value.normalize(),
            "price": high_price
        })
    
    # 按索引位置排序
    points.sort(key=lambda p: p["idx"])
    return points


def _find_diagonal_descending_lines(
    df: pd.DataFrame,
    wave_high_points: List[dict],
    lookback_days: int,
    recent_end_days: int,
    tolerance_pct: float
) -> List[dict]:
    """
    找出斜向下降趨勢線
    
    規格書邏輯：
    1. 起點：180天內任意波段高點
    2. 終點：最近20天內的波段高點
    3. 斜率要求：≤ 0（下降或水平）
    4. 有效性：區間內所有K線最高價不穿越趨勢線（±0.1%誤差）
    """
    lines = []
    
    # 計算時間範圍
    last_idx = len(df) - 1
    lookback_idx = max(0, last_idx - lookback_days)
    recent_start_idx = max(0, last_idx - recent_end_days)
    
    # 篩選終點候選（必須在最近20天內）
    end_point_candidates = [p for p in wave_high_points if p["idx"] >= recent_start_idx]
    
    # 💡 改進：如果最近20天沒有波段高點，則使用最近的一個波段高點
    if len(end_point_candidates) == 0:
        if len(wave_high_points) > 0:
            # 使用最近的波段高點作為終點
            most_recent_point = wave_high_points[-1]
            end_point_candidates = [most_recent_point]
            print(f"   ℹ️  最近{recent_end_days}天內無波段高點，使用最近波段高點：{most_recent_point['date'].strftime('%Y-%m-%d')}")
        else:
            return lines
    
    # 篩選起點候選（必須在180天內）
    start_point_candidates = [p for p in wave_high_points if p["idx"] >= lookback_idx]
    
    # 遍歷所有可能的起點-終點組合
    for i, point1 in enumerate(start_point_candidates):
        for point2 in end_point_candidates:
            # 確保時間順序：point1 在前，point2 在後
            if point1["idx"] >= point2["idx"]:
                continue
            
            # 檢查斜率（必須 ≤ 0）
            if point2["price"] > point1["price"]:
                continue
            
            # 計算趨勢線參數
            start_idx = point1["idx"]
            end_idx = point2["idx"]
            
            # 計算斜率和截距
            slope = (point2["price"] - point1["price"]) / (end_idx - start_idx)
            intercept = point1["price"] - slope * start_idx
            
            # 驗證趨勢線有效性（區間內無穿越）
            if not _segment_respects_line(df, start_idx, end_idx, slope, intercept, tolerance_pct):
                continue
            
            # 計算時間跨度
            days_span = _calculate_days_span(df, start_idx, end_idx)
            
            # 建立趨勢線資訊
            line_info = {
                "type": "diagonal_descending",
                "start_idx": start_idx,
                "end_idx": end_idx,
                "start_date": point1["date"],
                "end_date": point2["date"],
                "days_span": days_span,
                "slope": slope,
                "intercept": intercept,
                "equation": {"slope": slope, "intercept": intercept},
                "points": [
                    {"date": point1["date"], "price": point1["price"]},
                    {"date": point2["date"], "price": point2["price"]}
                ]
            }
            
            lines.append(line_info)
    
    return lines


def _find_horizontal_resistance_line(df: pd.DataFrame, lookback_days: int) -> Optional[dict]:
    """
    找出水平壓力線（180天最高點）
    
    規格書 2.2：
    - 取值：180天觀察窗口內所有K線的最高價
    - 性質：水平線（斜率 = 0）
    """
    last_idx = len(df) - 1
    lookback_idx = max(0, last_idx - lookback_days)
    
    # 取得回溯期間的數據
    lookback_df = df.iloc[lookback_idx:last_idx+1]
    
    if lookback_df.empty:
        return None
    
    # 找出最高價及其日期
    max_high = lookback_df["High"].max()
    max_high_date = lookback_df["High"].idxmax()
    
    # 計算該日期的索引位置
    if isinstance(max_high_date, pd.Timestamp):
        max_high_idx = df.index.get_loc(max_high_date)
    else:
        max_high_idx = lookback_df["High"].idxmax()
    
    # 建立水平壓力線資訊
    line_info = {
        "type": "horizontal_resistance",
        "start_idx": lookback_idx,
        "end_idx": last_idx,
        "start_date": pd.to_datetime(df.index[lookback_idx]),
        "end_date": pd.to_datetime(df.index[last_idx]),
        "days_span": lookback_days,
        "slope": 0.0,
        "intercept": max_high,
        "equation": {"slope": 0.0, "intercept": max_high},
        "resistance_price": max_high,
        "resistance_date": pd.to_datetime(max_high_date),
        "points": [
            {"date": pd.to_datetime(max_high_date), "price": max_high}
        ]
    }
    
    return line_info


def _segment_respects_line(
    df: pd.DataFrame,
    start_idx: int,
    end_idx: int,
    slope: float,
    intercept: float,
    tolerance_pct: float
) -> bool:
    """
    驗證趨勢線區間內所有K線最高價不穿越趨勢線
    
    規格書有效性驗證：
    - 趨勢線區間內所有K線的最高價不得穿越趨勢線
    - 誤差容忍：允許 ±0.1% 的誤差範圍
    
    Args:
        df: K線數據
        start_idx: 起始索引
        end_idx: 結束索引
        slope: 趨勢線斜率
        intercept: 趨勢線截距
        tolerance_pct: 誤差容忍百分比
    
    Returns:
        True 表示有效（無穿越），False 表示無效（有穿越）
    """
    if end_idx <= start_idx:
        return True
    
    # 遍歷區間內所有K線
    for i in range(start_idx, end_idx + 1):
        high_price = df.iloc[i]["High"]
        trendline_price = intercept + slope * i
        
        # 計算誤差容忍範圍
        tolerance = trendline_price * (tolerance_pct / 100.0)
        
        # 檢查是否穿越（高點超過趨勢線 + 誤差）
        if high_price > trendline_price + tolerance:
            return False
    
    return True


def _calculate_days_span(df: pd.DataFrame, start_idx: int, end_idx: int) -> int:
    """計算時間跨度（自然日）"""
    if end_idx <= start_idx:
        return 0
    
    start_date = pd.to_datetime(df.index[start_idx])
    end_date = pd.to_datetime(df.index[end_idx])
    
    if pd.isna(start_date) or pd.isna(end_date):
        return end_idx - start_idx
    
    return max(0, (end_date - start_date).days)


if __name__ == "__main__":
    print("下降趨勢線識別模組 - 規格書版本")
    print("=" * 60)
    print("功能：")
    print("  1. 斜向下降趨勢線（起點180天內，終點最近20天內）")
    print("  2. 水平壓力線（180天最高價）")
    print("  3. 嚴格有效性驗證（±0.1%誤差容忍）")
    print("\n使用方式：")
    print("  from long_term_descending_trendline import identify_descending_trendlines")
    print("  trendlines = identify_descending_trendlines(df, wave_points_df)")