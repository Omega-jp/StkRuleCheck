#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Impulse MACD 買入規則

規則說明:
1. Impulse MACD 零線交叉買入信號
   - Impulse MACD 由負轉正,向上穿越 0 線
   - 這是較強的趨勢反轉信號

2. Impulse MACD 信號線交叉買入信號
   - Impulse MACD 向上穿越信號線
   - 這是較頻繁的短期買入信號

前提條件:
- DataFrame 中必須已包含 ImpulseMACD, ImpulseSignal, ImpulseHistogram 欄位
- 這些欄位由 data_initial/calculate_impulse_macd.py 預先計算

版本: v1.1
更新日期: 2025-10-29
"""

import pandas as pd
import sys
import os


def check_impulse_macd_zero_cross_buy(df: pd.DataFrame) -> pd.DataFrame:
    """
    檢查 Impulse MACD 零線交叉買入信號
    
    買入條件:
    - Impulse MACD 由負轉正,向上穿越 0 線
    
    Args:
        df: 包含 ImpulseMACD 欄位的 DataFrame
        
    Returns:
        包含買入信號的 DataFrame,欄位:
        - date: 日期
        - impulse_macd_zero_cross_buy: 'O' 表示買入信號
    """
    results = []
    
    # 檢查必要欄位
    if 'ImpulseMACD' not in df.columns:
        print("⚠ DataFrame 缺少 ImpulseMACD 欄位,請先執行 append_indicator")
        return pd.DataFrame(columns=['date', 'impulse_macd_zero_cross_buy'])
    
    for i, (idx, row) in enumerate(df.iterrows()):
        date = idx.strftime('%Y-%m-%d')
        
        # 初始化為不滿足條件
        signal = ''
        
        if i > 0:
            prev_row = df.iloc[i - 1]
            
            curr_impulse = row.get('ImpulseMACD')
            prev_impulse = prev_row.get('ImpulseMACD')
            
            # 檢查數據有效性
            if pd.notna(curr_impulse) and pd.notna(prev_impulse):
                # 向上穿越 0 線
                if prev_impulse <= 0 and curr_impulse > 0:
                    signal = 'O'
        
        results.append({
            'date': date,
            'impulse_macd_zero_cross_buy': signal
        })
    
    return pd.DataFrame(results)


def check_impulse_macd_signal_cross_buy(df: pd.DataFrame) -> pd.DataFrame:
    """
    檢查 Impulse MACD 信號線交叉買入信號
    
    買入條件:
    - Impulse MACD 向上穿越信號線
    
    Args:
        df: 包含 ImpulseMACD 和 ImpulseSignal 欄位的 DataFrame
        
    Returns:
        包含買入信號的 DataFrame,欄位:
        - date: 日期
        - impulse_macd_signal_cross_buy: 'O' 表示買入信號
    """
    results = []
    
    # 檢查必要欄位
    required_cols = ['ImpulseMACD', 'ImpulseSignal']
    for col in required_cols:
        if col not in df.columns:
            print(f"⚠ DataFrame 缺少 {col} 欄位,請先執行 append_indicator")
            return pd.DataFrame(columns=['date', 'impulse_macd_signal_cross_buy'])
    
    for i, (idx, row) in enumerate(df.iterrows()):
        date = idx.strftime('%Y-%m-%d')
        
        # 初始化為不滿足條件
        signal = ''
        
        if i > 0:
            prev_row = df.iloc[i - 1]
            
            curr_macd = row.get('ImpulseMACD')
            prev_macd = prev_row.get('ImpulseMACD')
            curr_signal = row.get('ImpulseSignal')
            prev_signal = prev_row.get('ImpulseSignal')
            
            # 檢查數據有效性
            if (pd.notna(curr_macd) and pd.notna(prev_macd) and 
                pd.notna(curr_signal) and pd.notna(prev_signal)):
                
                # 向上穿越信號線
                if prev_macd <= prev_signal and curr_macd > curr_signal:
                    signal = 'O'
        
        results.append({
            'date': date,
            'impulse_macd_signal_cross_buy': signal
        })
    
    return pd.DataFrame(results)


def check_impulse_macd_combined_buy(df: pd.DataFrame,
                                   require_positive_histo: bool = False) -> pd.DataFrame:
    """
    組合 Impulse MACD 買入信號
    
    買入條件 (任一滿足即可):
    1. 零線交叉買入
    2. 信號線交叉買入
    
    可選條件:
    - require_positive_histo: 要求 ImpulseHistogram 為正
    
    Args:
        df: 包含 Impulse MACD 相關欄位的 DataFrame
        require_positive_histo: 是否要求柱狀圖為正,預設 False
        
    Returns:
        包含買入信號的 DataFrame,欄位:
        - date: 日期
        - impulse_macd_buy: 'O' 表示買入信號
    """
    results = []
    
    # 獲取兩種信號
    zero_cross_df = check_impulse_macd_zero_cross_buy(df)
    signal_cross_df = check_impulse_macd_signal_cross_buy(df)
    
    # 建立日期到信號的映射
    zero_cross_dates = set(
        zero_cross_df[zero_cross_df['impulse_macd_zero_cross_buy'] == 'O']['date'].values
    )
    signal_cross_dates = set(
        signal_cross_df[signal_cross_df['impulse_macd_signal_cross_buy'] == 'O']['date'].values
    )
    
    # 遍歷所有日期
    for idx, row in df.iterrows():
        date = idx.strftime('%Y-%m-%d')
        signal = ''
        
        # 檢查是否有任一信號
        has_signal = date in zero_cross_dates or date in signal_cross_dates
        
        if has_signal:
            # 如果要求柱狀圖為正,檢查條件
            if require_positive_histo:
                impulse_histo = row.get('ImpulseHistogram')
                if pd.notna(impulse_histo) and impulse_histo > 0:
                    signal = 'O'
            else:
                signal = 'O'
        
        results.append({
            'date': date,
            'impulse_macd_buy': signal
        })
    
    return pd.DataFrame(results)


if __name__ == '__main__':
    # 測試程式碼
    print("=== Impulse MACD 買入規則測試 ===\n")
    
    # 這個測試需要實際的股票資料
    print("此模組需要配合已計算 Impulse MACD 的 DataFrame 使用")
    print("\n使用方式:")
    print("1. 先執行 append_indicator 計算 Impulse MACD")
    print("2. 載入包含 ImpulseMACD 欄位的 DataFrame")
    print("3. 調用買入規則檢查函數")
    print("\n範例代碼:")
    print("""
from data_initial.kbar_collector import load_stock_data
from buyRule.impulse_macd_buy_rule import check_impulse_macd_zero_cross_buy

df = load_stock_data('00631L', 'D')
buy_signals = check_impulse_macd_zero_cross_buy(df)
print(buy_signals[buy_signals['impulse_macd_zero_cross_buy'] == 'O'])
    """)