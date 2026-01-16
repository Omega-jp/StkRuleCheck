#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轉折點識別模塊 - 書本規格標準版 v4.0 (區間極值版)

根據 v2.0 規格書 (實務簡化版) 實作：
不再使用複雜的「位移」邏輯，改採「區間極值 (Range Extremum)」原則。

核心邏輯：
1. 向上穿越 (Cross Up) 時：在「前一個轉折高點之後」到「本次穿越點」之間，找最低價 (Low) 為轉折低點。
2. 向下穿越 (Cross Down) 時：在「前一個轉折低點之後」到「本次穿越點」之間，找最高價 (High) 為轉折高點。

版本：v4.0
更新日期：2026-01-15
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple, List

def detect_cross_events(df: pd.DataFrame) -> pd.DataFrame:
    """
    檢測收盤價與MA5的穿越事件 (單日穿越)
    
    Args:
        df: K線數據，需包含 'Close' 和 'ma5'
    
    Returns:
        包含 'cross_up', 'cross_down' 標記的 DataFrame copy
    """
    df_cross = df.copy()
    
    # 計算收盤價與MA5的相對位置
    df_cross['close_above_ma5'] = df_cross['Close'] > df_cross['ma5']
    
    # 前一天的狀態
    df_cross['prev_close_above_ma5'] = (
        df_cross['close_above_ma5'].shift(1).astype('boolean')
    )
    
    # 向上穿越：前一天 <= MA5, 當天 > MA5
    df_cross['cross_up'] = (
        (df_cross['close_above_ma5']) &
        (~df_cross['prev_close_above_ma5'].fillna(False))
    )
    
    # 向下穿越：前一天 >= MA5, 當天 < MA5
    df_cross['cross_down'] = (
        (~df_cross['close_above_ma5']) &
        (df_cross['prev_close_above_ma5'].fillna(True))
    )
    
    return df_cross

def identify_turning_points(df: pd.DataFrame, window_size: int = 5) -> pd.DataFrame:
    """
    識別股價的轉折高點和轉折低點 (區間極值法)
    
    Args:
        df: K線數據 (需包含 Close, High, Low, ma5)
        window_size: 保留參數，未使用
        
    Returns:
        DataFrame (date, turning_high_point, turning_low_point)
    """
    # 1. 基本檢查與初始化
    if 'ma5' not in df.columns:
        raise ValueError("DataFrame必須包含'ma5'欄位")
    
    # 建立結果容器
    # 用 list of dict 來存，最後再轉 DataFrame，比逐行 append 效能好
    # 但為了配合原有回傳格式，我們最後會 merge 回去或生成新結構
    # 這裡策略：先標記在一個 mask 上，最後生成結果
    
    n = len(df)
    turning_high_mask = [False] * n
    turning_low_mask = [False] * n
    
    # 2. 檢測穿越
    df_cross = detect_cross_events(df)
    
    # 3. 核心變數初始化
    # 我們需要記錄「前一個轉折點的索引」，用來定義搜尋區間的起點
    # 初始值設為 -1 (代表從資料最開頭開始找)
    last_turned_high_idx = -1
    last_turned_low_idx = -1
    
    # 為了處理第一筆資料前的狀態，我們需要知道第一筆是在 MA5 上方還是下方
    # 如果第一筆就在 MA5 上方，那潛在的第一個轉折點應該是「轉折高」
    # 反之亦然。不過根據區間極值法，我們只需等到「穿越」發生再來回溯即可。
    
    # 遍歷每一天
    for i in range(n):
        row = df_cross.iloc[i]
        
        # 邊界保護：MA5 無值時不處理 (通常是前4天)
        if pd.isna(row['ma5']):
            continue
            
        # === 處理 向上穿越 (找轉折低) ===
        if row['cross_up']:
            # 定義搜尋區間 [start, end]
            # start: 前一個轉折高點的「下一根」 (如果沒轉折高，就從資料頭開始)
            start_idx = max(0, last_turned_high_idx + 1)
            end_idx = i  # 包含當前這根 Cross Up K棒
            
            # 區間極值搜尋：找 Low 的最小值
            # slice is [start_idx : end_idx + 1] because python slice is exclusive at end
            interval_df = df_cross.iloc[start_idx : end_idx + 1]
            
            if not interval_df.empty:
                min_low_val = interval_df['Low'].min()
                # 找出最小值對應的 relative index
                # idxmin() 回傳的是原有 index (可能是 DateIndex 或 IntIndex)
                # 為了穩健，我們用 mask 找
                # 注意：如果有多個相同最低價，通常取第一個或最後一個皆可，這裡取第一個
                target_date_idx = interval_df[interval_df['Low'] == min_low_val].index[0]
                
                # 轉回整數 index (如果是依賴 iloc)
                # 這裡稍微麻煩點，因為 df index 可能是 Date。
                # 簡單作法：透過 interval_df 的 row number 加上 start_idx
                # 或者直接用 get_loc 如果 index 是 unique 的
                target_integer_idx = df_cross.index.get_loc(target_date_idx)
                
                # 標記轉折低點
                turning_low_mask[target_integer_idx] = True
                
                # 更新狀態
                last_turned_low_idx = target_integer_idx
        
        # === 處理 向下穿越 (找轉折高) ===
        elif row['cross_down']:
            # 定義搜尋區間 [start, end]
            # start: 前一個轉折低點的「下一根」
            start_idx = max(0, last_turned_low_idx + 1)
            end_idx = i
            
            # 區間極值搜尋：找 High 的最大值
            interval_df = df_cross.iloc[start_idx : end_idx + 1]
            
            if not interval_df.empty:
                max_high_val = interval_df['High'].max()
                target_date_idx = interval_df[interval_df['High'] == max_high_val].index[0]
                target_integer_idx = df_cross.index.get_loc(target_date_idx)
                
                # 標記轉折高點
                turning_high_mask[target_integer_idx] = True
                
                # 更新狀態
                last_turned_high_idx = target_integer_idx

    # 4. 格式化輸出結果
    results = []
    for i in range(n):
        date_str = df.index[i].strftime('%Y-%m-%d')
        results.append({
            'date': date_str,
            'turning_high_point': 'O' if turning_high_mask[i] else '',
            'turning_low_point': 'O' if turning_low_mask[i] else ''
        })
        
    return pd.DataFrame(results)

def check_turning_points(df: pd.DataFrame, window_size: int = 5) -> pd.DataFrame:
    """向後兼容的別名"""
    return identify_turning_points(df, window_size)

def verify_turning_points_quality(df: pd.DataFrame, turning_points_df: pd.DataFrame) -> dict:
    """
    驗證轉折點識別質量
    """
    issues = []
    
    # 提取轉折點
    high_points = turning_points_df[turning_points_df['turning_high_point'] == 'O']['date'].tolist()
    low_points = turning_points_df[turning_points_df['turning_low_point'] == 'O']['date'].tolist()
    
    # 合併並排序
    all_points = []
    for date in high_points:
        all_points.append((date, 'high'))
    for date in low_points:
        all_points.append((date, 'low'))
    all_points.sort(key=lambda x: x[0])
    
    # 檢查1：高低點是否交替
    alternating = True
    for i in range(len(all_points) - 1):
        if all_points[i][1] == all_points[i+1][1]:
            # 這在區間極值法中仍可能發生嗎？
            # 理論上如果 MA5 頻繁震盪，可能會導致連續 cross up/down?
            # 不，cross up 後必須先有 cross down 才能再次 cross up (除非 MA5 剛好相等)
            # 但我們的區間定義是依賴「前一個轉折點」，這會強制交替嗎？
            # 其實 identify_turning_points 邏輯裡：
            # 找低點依賴 last_high，找高點依賴 last_low。
            # 初始都為 -1。
            # 如果連續兩次 Cross Up (中間沒 Cross Down)，會發生什麼？
            # 正常的 MA5 穿越不會連續兩次 Cross Up，中間一定夾雜 Cross Down。
            # 所以理論上是交替的。
            alternating = False
            issues.append(f"連續兩個{all_points[i][1]}點: {all_points[i][0]} 和 {all_points[i+1][0]}")
            
    return {
        'alternating': alternating,
        'high_points_count': len(high_points),
        'low_points_count': len(low_points),
        'issues': issues
    }

if __name__ == "__main__":
    print("轉折點識別模塊 - 書本規格標準版 v4.0 (區間極值版)")
    print("="*60)
    print("功能：使用區間極值法 (Range Extremum) 識別轉折點")
    print("邏輯簡化：不再需要複雜的位移處理，直接搜尋區間極值")
    print("="*60)
