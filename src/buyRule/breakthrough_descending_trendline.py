#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下降趨勢線突破買入規則檢查模組 - 規格書版本
================================================

根據「突破下降趨勢線偵測規格書」實作突破判定邏輯：
1. 收盤價突破判定（非盤中價）
2. 最小突破幅度 ≥ 0.5%
3. 可選的成交量確認（1.2倍放量）

作者：Claude
日期：2025-01-21
"""

from typing import Optional
import pandas as pd
import numpy as np


def check_breakthrough_descending_trendline(
    df: pd.DataFrame,
    trendlines: dict,
    min_breakthrough_pct: float = 0.5,
    volume_confirmation: bool = True,
    volume_multiplier: float = 1.2,
    volume_window: int = 20
) -> pd.DataFrame:
    """
    檢查下降趨勢線突破買入信號
    
    根據規格書第三節「突破判定標準」：
    
    3.1 突破定義：
    - 收盤價高於當日趨勢線對應價格
    - 非盤中價：只看收盤價，不看盤中最高價
    
    3.2 突破幅度：
    - 最小突破幅度：0.5%
    - 計算公式：(收盤價 - 趨勢線價格) / 趨勢線價格 × 100% ≥ 0.5%
    
    3.3 成交量確認（可選）：
    - 量能放大：當日成交量 ≥ 過去20日平均成交量 × 1.2倍
    - 目的：過濾假突破
    
    Args:
        df: K線數據，需包含 'Close' 和 'Volume'（若需量能確認）
        trendlines: 趨勢線字典（由 identify_descending_trendlines 返回）
        min_breakthrough_pct: 最小突破百分比（預設0.5%）
        volume_confirmation: 是否需要成交量確認（預設True）
        volume_multiplier: 成交量放大倍數（預設1.2倍）
        volume_window: 均量計算窗口（預設20天）
    
    Returns:
        DataFrame，每日一列記錄：
        - date: 日期
        - breakthrough_check: 'O' 表示突破，'' 表示未突破
        - breakthrough_type: 突破類型（'diagonal' 或 'horizontal'）
        - breakthrough_pct: 突破幅度（%）
        - volume_ratio: 成交量比率
        - trendline_price: 趨勢線價格
        - close_price: 收盤價
        - signal_strength: 信號強度（1-5分）
    """
    
    if df is None or df.empty:
        return pd.DataFrame()
    
    if 'Close' not in df.columns:
        raise ValueError("DataFrame 必須包含 'Close' 欄位")
    
    # 預計算成交量移動平均（如果需要）
    volume_ma = None
    if volume_confirmation and 'Volume' in df.columns:
        volume_ma = df['Volume'].rolling(window=volume_window, min_periods=5).mean()
    
    # 提取所有趨勢線
    all_lines = trendlines.get('all_lines', [])
    
    if len(all_lines) == 0:
        # 沒有趨勢線，返回空結果
        return _create_empty_results(df)
    
    results = []
    used_breakthrough_lines = set()
    
    # 對每個日期進行檢查
    for i in range(len(df)):
        date = df.index[i]
        close_price = df.iloc[i]['Close']
        
        # 預設值
        breakthrough_check = ''
        breakthrough_type = ''
        breakthrough_pct = 0.0
        volume_ratio = 1.0
        trendline_price = 0.0
        signal_strength = 0
        
        # 計算當日成交量比率（如果需要）
        if volume_confirmation and volume_ma is not None:
            current_volume = df.iloc[i]['Volume']
            avg_volume = volume_ma.iloc[i]
            
            if not pd.isna(avg_volume) and avg_volume > 0:
                volume_ratio = current_volume / avg_volume
            else:
                volume_ratio = 0.0
        
        # 尋找有效突破
        valid_breakthroughs = []
        
        for line in all_lines:
            line_key = _build_line_key(line)
            if line_key in used_breakthrough_lines:
                continue
            
            # 計算當日趨勢線價格
            current_line_price = line['intercept'] + line['slope'] * i
            
            # 檢查 1：收盤價突破趨勢線
            if close_price <= current_line_price:
                continue
            
            # 計算突破幅度
            pct = ((close_price - current_line_price) / current_line_price) * 100.0
            
            # 檢查 2：突破幅度 ≥ 最小要求
            if pct < min_breakthrough_pct:
                continue
            
            # 檢查 3：成交量確認（如果啟用）
            if volume_confirmation:
                if volume_ratio < volume_multiplier:
                    continue
            
            # 有效突破！記錄資訊
            valid_breakthroughs.append({
                'line': line,
                'breakthrough_pct': pct,
                'volume_ratio': volume_ratio,
                'line_price': current_line_price
            })
        
        # 如果有多個有效突破，選擇最佳的一個
        if valid_breakthroughs:
            best_breakthrough = _select_best_breakthrough(valid_breakthroughs)
            
            if best_breakthrough:
                breakthrough_check = 'O'
                line = best_breakthrough['line']
                breakthrough_type = line['type']
                breakthrough_pct = best_breakthrough['breakthrough_pct']
                volume_ratio = best_breakthrough['volume_ratio']
                trendline_price = best_breakthrough['line_price']
                
                # 計算信號強度（1-5分）
                signal_strength = _calculate_signal_strength(
                    line, breakthrough_pct, volume_ratio
                )
                used_breakthrough_lines.add(_build_line_key(line))
        
        # 記錄結果
        results.append({
            'date': date.strftime('%Y-%m-%d') if isinstance(date, pd.Timestamp) else str(date),
            'breakthrough_check': breakthrough_check,
            'breakthrough_type': breakthrough_type,
            'breakthrough_pct': round(breakthrough_pct, 2),
            'volume_ratio': round(volume_ratio, 2),
            'trendline_price': round(trendline_price, 2),
            'close_price': round(close_price, 2),
            'signal_strength': signal_strength
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
