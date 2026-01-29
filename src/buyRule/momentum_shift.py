#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Momentum Shift (動能轉移) 系統 v1.0

根據規格書實作：
1. 三根 K 線模型 (Fair Value Gap)
2. 群組不效率模型 (基於波段高低點 Swing Points)
3. 階梯式中心價格 (Center Price) 軌跡更新
4. 買進與賣出訊號偵測
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Tuple
from src.baseRule.turning_point_identification import identify_turning_points

def compute_momentum_shift(df: pd.DataFrame) -> pd.DataFrame:
    """
    計算動能轉移 (Momentum Shift) 軌跡與訊號（同時採用 FVG 與 Group 模型）。

    Args:
        df (pd.DataFrame): 包含 Open, High, Low, Close (ma5 會自動計算)

    Returns:
        pd.DataFrame: 包含 momentum_shift_level, shift_type, ms_buy_signal, ms_sell_signal
    """
    if df.empty or len(df) < 3:
        return pd.DataFrame()

    df_calc = df.sort_index().copy()
    
    # 初始化結果欄位
    df_calc['ms_level'] = np.nan
    df_calc['ms_type'] = None  # "Bullish" or "Bearish"
    df_calc['ms_buy_signal'] = ""
    df_calc['ms_sell_signal'] = ""

    current_ms_level = np.nan
    current_ms_type = None  # "Bullish" (Green) or "Bearish" (Red)

    # 取得波段高低點
    if 'ma5' not in df_calc.columns:
        df_calc['ma5'] = df_calc['Close'].rolling(window=5, min_periods=1).mean()
    
    turning_points = identify_turning_points(df_calc)
    # 把轉折點資訊 merge 回來方便查詢
    df_calc['tp_high'] = turning_points['turning_high_point'].values
    df_calc['tp_low'] = turning_points['turning_low_point'].values

    # 為了找「最近一個」波段點，記錄歷史
    last_swing_high_val = np.nan
    last_swing_low_val = np.nan

    for i in range(len(df_calc)):
        row = df_calc.iloc[i]
        
        # --- 1. 更新最近的波段點 ---
        if row['tp_high'] == 'O':
            last_swing_high_val = row['High']
        if row['tp_low'] == 'O':
            last_swing_low_val = row['Low']

        # --- 2. 偵測新的不效率空隙 ---
        new_gap_found = False
        candidates = [] # 儲存當前 K 線產生的所有潛在空隙

        # A. 三根 K 線模型 (FVG)
        if i >= 2:
            # 看漲 FVG: Low[curr] > High[i-2]
            if df_calc.iloc[i]['Low'] > df_calc.iloc[i-2]['High']:
                candidates.append({
                    'level': (df_calc.iloc[i]['Low'] + df_calc.iloc[i-2]['High']) / 2,
                    'type': "Bullish"
                })
            
            # 看跌 FVG: High[curr] < Low[i-2]
            elif df_calc.iloc[i]['High'] < df_calc.iloc[i-2]['Low']:
                candidates.append({
                    'level': (df_calc.iloc[i-2]['Low'] + df_calc.iloc[i]['High']) / 2,
                    'type': "Bearish"
                })

        # B. 群組不效率模型 (Swing Points)
        # 看漲: 當前 Low > 最近一個波段高點 且 「前一天 Low 尚未突破」 (代表剛突破形成的空隙)
        if not np.isnan(last_swing_high_val) and row['Low'] > last_swing_high_val:
            prev_low = df_calc.iloc[i-1]['Low'] if i > 0 else np.nan
            if i > 0 and prev_low <= last_swing_high_val:
                candidates.append({
                    'level': (row['Low'] + last_swing_high_val) / 2,
                    'type': "Bullish"
                })
        # 看跌: 當前 High < 最近一個波段低點 且 「前一天 High 尚未穿破」
        elif not np.isnan(last_swing_low_val) and row['High'] < last_swing_low_val:
            prev_high = df_calc.iloc[i-1]['High'] if i > 0 else np.nan
            if i > 0 and prev_high >= last_swing_low_val:
                candidates.append({
                    'level': (last_swing_low_val + row['High']) / 2,
                    'type': "Bearish"
                })

        # 如果有多個空隙，以最近的（通常是 FVG）為主
        if candidates:
            selected = candidates[0] 
            new_level = selected['level']
            new_type = selected['type']
            new_gap_found = True

        # --- 3. 處理狀態更新 (Staircase) ---
        prev_level = current_ms_level
        prev_type = current_ms_type

        if new_gap_found:
            current_ms_level = new_level
            current_ms_type = new_type
        
        # --- 4. 偵測交易訊號 ---
        # 買進: 之前是 Bearish (紅線)，今天 Close > Level
        if prev_type == "Bearish" and not np.isnan(prev_level):
            if row['Close'] > prev_level:
                df_calc.at[df_calc.index[i], 'ms_buy_signal'] = "O"
                current_ms_type = "Bullish" 

        # 賣出: 之前是 Bullish (綠線)，今天 Close < Level
        if prev_type == "Bullish" and not np.isnan(prev_level):
            if row['Close'] < prev_level:
                df_calc.at[df_calc.index[i], 'ms_sell_signal'] = "O"
                current_ms_type = "Bearish"

        # 儲存當天狀態
        df_calc.at[df_calc.index[i], 'ms_level'] = current_ms_level
        df_calc.at[df_calc.index[i], 'ms_type'] = current_ms_type

    return df_calc

def check_momentum_shift_buy_rule(df: pd.DataFrame) -> pd.DataFrame:
    """
    相容於系統現行 validate_buy_rule 的 wrapper。
    """
    res = compute_momentum_shift(df)
    if res.empty:
        return pd.DataFrame(columns=["date", "ms_buy_check", "ms_sell_check", "ms_level", "ms_type"])
    
    # 格式化輸出
    res['date'] = res.index.strftime('%Y-%m-%d') if hasattr(res.index, 'strftime') else res.index.map(str)
    res['ms_buy_check'] = res['ms_buy_signal']
    res['ms_sell_check'] = res['ms_sell_signal']
    
    return res[["date", "ms_buy_check", "ms_sell_check", "ms_level", "ms_type"]]

if __name__ == "__main__":
    # 測試腳本
    data = {
        'Close': [100, 102, 105, 110, 108, 106, 104, 112, 115],
        'High':  [101, 103, 106, 111, 109, 107, 105, 113, 116],
        'Low':   [99,  101, 104, 109, 107, 105, 103, 111, 114]
    }
    sample_df = pd.DataFrame(data)
    # 前三根: (3) Low 104 > (1) High 101 -> Bullish Gap @ 102.5
    # 第四根: (4) Low 109 > (2) High 103 -> Bullish Gap @ 106
    # ...
    test_res = compute_momentum_shift(sample_df)
    print(test_res[['ms_level', 'ms_type', 'ms_buy_signal', 'ms_sell_signal']])
