#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Momentum Shift (動能轉移) 系統 v2.0

根據規格書 (GFVG Update) 實作：
1. Group Fair Value Gap (GFVG) 模型
   - 動態向回掃描尋找最近的未填補空隙 (Global Scan)
   - Bullish GFVG: Low[curr] > High[prev_k]
   - Bearish GFVG: High[curr] < Low[prev_k]
2. 階梯式中心價格 (Center Price) 軌跡更新
3. 買進與賣出訊號偵測
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Tuple, Dict

def compute_momentum_shift(df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """
    計算動能轉移 (Momentum Shift) 軌跡與訊號 (基於 GFVG 掃描)。

    Args:
        df (pd.DataFrame): 包含 Open, High, Low, Close
        lookback (int): 向回掃描尋找邊界 K 線的最大範圍 (預設 20)

    Returns:
        pd.DataFrame: 包含 ms_level, ms_type, ms_buy_signal, ms_sell_signal
    """
    if df.empty or len(df) < 2:
        return pd.DataFrame()

    df_calc = df.sort_index().copy()
    
    # 初始化結果欄位
    df_calc['ms_level'] = np.nan
    df_calc['ms_type'] = None  # "Bullish" or "Bearish"
    df_calc['ms_buy_signal'] = ""
    df_calc['ms_sell_signal'] = ""

    current_ms_level = np.nan
    current_ms_type = None  # "Bullish" (Green) or "Bearish" (Red)
    
    highs = df_calc['High'].values
    lows = df_calc['Low'].values
    closes = df_calc['Close'].values
    n = len(df_calc)

    for i in range(n):
        # 至少要有前面的 K 線才能比較
        if i == 0:
            continue
            
        current_high = highs[i]
        current_low = lows[i]

        new_level = None
        new_type = None
        found_gap = False

        # --- GFVG Scanning Logic ---
        # 往回看 k in [i-1, i-2, ... i-lookback]
        start_scan = max(0, i - lookback)
        
        # 1. Check Bearish GFVG (看跌缺口)
        # 條件: High[curr] < Low[k] (且 k 是最近的一個)
        for k in range(i - 1, start_scan - 1, -1):
            if lows[k] > current_high:
                # Found the nearest boundary candle
                # Level = (Low[boundary] + High[current]) / 2
                new_level = (lows[k] + current_high) / 2
                new_type = "Bearish"
                found_gap = True
                break # 找到最近的就停止

        # 2. Check Bullish GFVG (看漲缺口)
        # 條件: Low[curr] > High[k] (且 k 是最近的一個)
        # 注意: 若同一個 K 線同時滿足 Bullish 和 Bearish (例如 Inside Bar 可能發生極端狀況?)
        # 通常實體方向會決定主要缺口類型，或者後面的取代前面的。
        # 這裡我們獨立掃描。如果 Bearish 已經找到，我們再看 Bullish。
        # 如果都有，如何權衡？
        # 根據定義，如果 High < Old Low 成立 (Bearish Gap)，那 Low > Old High (Bullish Gap) 
        # 在幾何上這兩者很難對「同一根」Old Candle 成立。
        # 但可能對「不同」的 k 成立。
        # 邏輯上，越近的 K 線代表越近期的結構。
        # 這裡簡單起見，若兩者都找到，取 k 比較大的 (比較近的)。
        
        potential_bull_level = None
        potential_bull_k = -1

        for k in range(i - 1, start_scan - 1, -1):
            if highs[k] < current_low:
                potential_bull_level = (highs[k] + current_low) / 2
                potential_bull_k = k
                break
        
        if potential_bull_k != -1:
            # 如果之前已經找到 Bearish
            if found_gap:
                # 比較誰比較近 (k 越大越近)
                # Bearish 的 k 在上面的迴圈變數裡，需要記錄
                # 這裡重新整理一下邏輯架構
                pass 
                # 為了簡潔，我們先以「最後被掃描到的」或「優先順序」為準嗎？
                # 讓我們用一個更嚴謹的方式：
                # 找出 nearest Bearish k and nearest Bullish k
                pass
            else:
                 new_level = potential_bull_level
                 new_type = "Bullish"
                 found_gap = True
        
        # 優化重寫掃描迴圈以處理衝突 (雖然很少見)
        # 我們直接找 min distance
        best_k = -1
        
        # Scan Bearish
        bearish_k = -1
        bearish_val = 0.0
        for k in range(i - 1, start_scan - 1, -1):
            if lows[k] > current_high:
                bearish_k = k
                bearish_val = (lows[k] + current_high) / 2
                break
        
        # Scan Bullish
        bullish_k = -1
        bullish_val = 0.0
        for k in range(i - 1, start_scan - 1, -1):
            if highs[k] < current_low:
                bullish_k = k
                bullish_val = (highs[k] + current_low) / 2
                break
                
        # Decide
        if bearish_k != -1 and bullish_k != -1:
            if bearish_k > bullish_k: # Bearish is closer
                new_level = bearish_val
                new_type = "Bearish"
                found_gap = True
            else: # Bullish is closer or equal
                new_level = bullish_val
                new_type = "Bullish"
                found_gap = True
        elif bearish_k != -1:
            new_level = bearish_val
            new_type = "Bearish"
            found_gap = True
        elif bullish_k != -1:
            new_level = bullish_val
            new_type = "Bullish"
            found_gap = True


        # --- 3. 處理狀態更新 (Staircase) ---
        prev_level = current_ms_level
        prev_type = current_ms_type

        if found_gap:
            current_ms_level = new_level
            current_ms_type = new_type
        
        # --- 4. 偵測交易訊號 ---
        # 買進: 之前是 Bearish (紅線)，今天 Close > Level
        if prev_type == "Bearish" and not np.isnan(prev_level):
            if closes[i] > prev_level:
                df_calc.at[df_calc.index[i], 'ms_buy_signal'] = "O"
                current_ms_type = "Bullish" 
                # 訊號觸發後，狀態翻轉，但 Level 數值維持直到新 Gap 出現?
                # 依照慣例，flip type often implies looking for support now. 
                # 但 Staircase 定義是 "Only update level when new gap found".
                # 所以這裡只改 Type。

        # 賣出: 之前是 Bullish (綠線)，今天 Close < Level
        if prev_type == "Bullish" and not np.isnan(prev_level):
            if closes[i] < prev_level:
                df_calc.at[df_calc.index[i], 'ms_sell_signal'] = "O"
                current_ms_type = "Bearish"

        # 儲存當天狀態
        df_calc.at[df_calc.index[i], 'ms_level'] = current_ms_level
        df_calc.at[df_calc.index[i], 'ms_type'] = current_ms_type

    return df_calc

def check_momentum_shift(df: pd.DataFrame) -> pd.DataFrame:
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
    # 測試邏輯...
    test_res = compute_momentum_shift(sample_df)
    print(test_res[['ms_level', 'ms_type', 'ms_buy_signal', 'ms_sell_signal']])
