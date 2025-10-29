#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Impulse MACD 指標計算模組
用於 data_initial 階段計算 Impulse MACD 指標

原始作者: LazyBear (TradingView)
Python 移植: 用於 StkRuleCheck 系統

參考來源: https://www.tradingview.com/script/qt6xLfLi-Impulse-MACD-LazyBear/

計算邏輯:
1. src = (High + Low + Close) / 3
2. hi = SMMA(high, 34)
3. lo = SMMA(low, 34)
4. mi = ZLEMA(src, 34)
5. impulse_macd = if mi > hi then (mi - hi)
                 else if mi < lo then (mi - lo)
                 else 0
6. impulse_signal = SMA(impulse_macd, 9)
7. impulse_histogram = impulse_macd - impulse_signal

版本: v1.0
更新日期: 2025-10-29
"""

import pandas as pd
import numpy as np


def calc_smma(src: pd.Series, length: int) -> pd.Series:
    """
    計算平滑移動平均 (Smoothed Moving Average)
    
    Pine Script:
    smma = na(smma[1]) ? sma(src, len) : (smma[1] * (len - 1) + src) / len
    
    Args:
        src: 價格序列
        length: 平滑週期
        
    Returns:
        SMMA 序列
    """
    smma = pd.Series(index=src.index, dtype=float)
    
    if len(src) < length:
        return smma
    
    # 第一個值使用 SMA
    smma.iloc[length - 1] = src.iloc[:length].mean()
    
    # 後續值使用遞推公式
    for i in range(length, len(src)):
        smma.iloc[i] = (smma.iloc[i - 1] * (length - 1) + src.iloc[i]) / length
    
    return smma


def calc_zlema(src: pd.Series, length: int) -> pd.Series:
    """
    計算零延遲指數移動平均 (Zero-Lag EMA)
    
    Pine Script:
    ema1 = ema(src, length)
    ema2 = ema(ema1, length)
    d = ema1 - ema2
    zlema = ema1 + d
    
    Args:
        src: 價格序列
        length: EMA 週期
        
    Returns:
        ZLEMA 序列
    """
    ema1 = src.ewm(span=length, adjust=False).mean()
    ema2 = ema1.ewm(span=length, adjust=False).mean()
    d = ema1 - ema2
    zlema = ema1 + d
    
    return zlema


def calculate_impulse_macd(df: pd.DataFrame, 
                          length_ma: int = 34, 
                          length_signal: int = 9) -> pd.DataFrame:
    """
    計算 Impulse MACD 指標並添加到 DataFrame
    
    Args:
        df: 包含 OHLC 資料的 DataFrame (需要有 High, Low, Close 欄位)
        length_ma: MA 長度,預設 34
        length_signal: 信號線長度,預設 9
        
    Returns:
        包含 Impulse MACD 指標的 DataFrame (添加以下欄位):
        - ImpulseMACD: Impulse MACD 主線
        - ImpulseSignal: 信號線
        - ImpulseHistogram: 柱狀圖
        
    Note:
        - 所有數值精確到小數點後兩位
        - 欄位名稱與原始 MACD (MACD, Signal, Histogram) 區分開
    """
    df = df.copy()
    
    # 確保有必要的欄位
    required_cols = ['High', 'Low', 'Close']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"DataFrame 缺少必要欄位: {col}")
    
    # 計算 HLC3 (典型價格)
    src = (df['High'] + df['Low'] + df['Close']) / 3
    
    # 計算高低點的 SMMA
    hi = calc_smma(df['High'], length_ma)
    lo = calc_smma(df['Low'], length_ma)
    
    # 計算中間值的 ZLEMA
    mi = calc_zlema(src, length_ma)
    
    # 計算 Impulse MACD
    # 當 mi 超出 [lo, hi] 範圍時計算差值,否則為 0
    impulse_macd = pd.Series(index=df.index, dtype=float)
    
    for i in range(len(df)):
        if pd.notna(mi.iloc[i]) and pd.notna(hi.iloc[i]) and pd.notna(lo.iloc[i]):
            mi_val = mi.iloc[i]
            hi_val = hi.iloc[i]
            lo_val = lo.iloc[i]
            
            if mi_val > hi_val:
                impulse_macd.iloc[i] = mi_val - hi_val
            elif mi_val < lo_val:
                impulse_macd.iloc[i] = mi_val - lo_val
            else:
                impulse_macd.iloc[i] = 0.0
        else:
            impulse_macd.iloc[i] = np.nan
    
    # 計算信號線 (SMA of impulse_macd)
    impulse_signal = impulse_macd.rolling(window=length_signal).mean()
    
    # 計算柱狀圖
    impulse_histogram = impulse_macd - impulse_signal
    
    # 添加到 DataFrame (精確到小數點後兩位)
    df['ImpulseMACD'] = impulse_macd.round(2)
    df['ImpulseSignal'] = impulse_signal.round(2)
    df['ImpulseHistogram'] = impulse_histogram.round(2)
    
    return df


if __name__ == '__main__':
    # 測試程式碼
    print("=== Impulse MACD 計算模組測試 ===\n")
    
    # 創建測試數據
    import numpy as np
    
    n = 100
    dates = pd.date_range('2024-01-01', periods=n, freq='D')
    
    # 生成模擬價格
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    high = close + np.abs(np.random.randn(n))
    low = close - np.abs(np.random.randn(n))
    
    test_df = pd.DataFrame({
        'High': high,
        'Low': low,
        'Close': close
    }, index=dates)
    
    print(f"測試資料筆數: {len(test_df)}")
    print("\n原始資料 (前 5 筆):")
    print(test_df.head())
    
    # 計算 Impulse MACD
    result_df = calculate_impulse_macd(test_df)
    
    print("\n計算後資料 (最後 10 筆):")
    print(result_df[['High', 'Low', 'Close', 'ImpulseMACD', 'ImpulseSignal', 'ImpulseHistogram']].tail(10))
    
    # 統計
    print("\n=== 統計資訊 ===")
    print(f"ImpulseMACD 非零值數量: {(result_df['ImpulseMACD'] != 0).sum()}")
    print(f"ImpulseMACD 最大值: {result_df['ImpulseMACD'].max():.2f}")
    print(f"ImpulseMACD 最小值: {result_df['ImpulseMACD'].min():.2f}")
    
    # 檢查數據完整性
    print(f"\n數據完整性檢查:")
    print(f"  ImpulseMACD NaN 數量: {result_df['ImpulseMACD'].isna().sum()}")
    print(f"  ImpulseSignal NaN 數量: {result_df['ImpulseSignal'].isna().sum()}")
    print(f"  ImpulseHistogram NaN 數量: {result_df['ImpulseHistogram'].isna().sum()}")
    
    print("\n✓ 測試完成")