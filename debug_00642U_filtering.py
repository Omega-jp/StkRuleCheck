#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試腳本：檢查 00642U 底分型消失的原因
"""

import sys
import os
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.validate_buy_rule import load_stock_data
from src.baseRule.turning_point_identification import identify_turning_points
from src.baseRule.bottom_fractal_identification import identify_bottom_fractals

# 載入數據
df = load_stock_data("00642U", "D")
if not isinstance(df.index, pd.DatetimeIndex):
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")

if "ma5" not in df.columns:
    df["ma5"] = df["Close"].rolling(window=5, min_periods=1).mean()

df = df.tail(120)

# 識別轉折點
turning_points = identify_turning_points(df)

# 為了調試，我們先用「無過濾」的方式跑一次，看看原本有哪些底分型
print("\n=== 原始底分型（無過濾）===")
raw_fractals = identify_bottom_fractals(
    df, left=2, right=2, tol=0.0, turning_points_df=None
)
raw_hits = raw_fractals[raw_fractals["bottom_fractal"] == "O"]

if raw_hits.empty:
    print("無原始底分型")
else:
    # 確保有日期索引以便打印
    if not isinstance(raw_hits.index, pd.DatetimeIndex) and "date" in raw_hits.columns:
        raw_hits = raw_hits.set_index(pd.to_datetime(raw_hits["date"]))
        
    for idx, row in raw_hits.iterrows():
        # idx 應該是 timestamp
        date_str = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)
        print(f"確立日: {date_str}, 低點日: {row['fractal_low_date']}, 低點: {row['fractal_low']:.2f}")

# 建立轉折點列表
tp = turning_points.copy()
if "date" in tp.columns:
    tp["date"] = pd.to_datetime(tp["date"])
    tp = tp.set_index("date")

tp_list = []
for idx, row in tp.iterrows():
    if row.get("turning_high_point") == "O":
        tp_list.append((idx, "high"))
    elif row.get("turning_low_point") == "O":
        tp_list.append((idx, "low"))
tp_list.sort(key=lambda x: x[0])

print("\n=== 轉折點序列 ===")
for t_date, t_type in tp_list:
    print(f"{t_date.strftime('%Y-%m-%d')}: {t_type}")

print("\n=== 過濾邏輯檢查 ===")
# 模擬過濾邏輯
for idx, row in raw_hits.iterrows():
    current_date = idx
    fractal_low_date_str = row['fractal_low_date']
    fractal_low_date = pd.to_datetime(fractal_low_date_str)
    
    # 找最近的轉折點
    recent_tp = None
    for t_date, t_type in reversed(tp_list):
        if t_date <= current_date:
            recent_tp = {"date": t_date, "type": t_type}
            break
            
    print(f"\n檢查底分型 (確立日 {current_date.strftime('%Y-%m-%d')}, 低點日 {fractal_low_date_str}):")
    if not recent_tp:
        print("  -> 無最近轉折點 (過濾結果: 視實作而定，目前 pass)")
        continue
        
    print(f"  -> 最近轉折點: {recent_tp['date'].strftime('%Y-%m-%d')} ({recent_tp['type']})")
    
    # 條件 1
    cond1 = (recent_tp['type'] == 'high')
    print(f"  -> 條件1 (最近是高點): {'PASS' if cond1 else 'FAIL'}")
    
    # 條件 2
    cond2 = (fractal_low_date >= recent_tp['date'])
    print(f"  -> 條件2 (低點日 >= 轉折日): {'PASS' if cond2 else 'FAIL'} [{fractal_low_date_str} >= {recent_tp['date'].strftime('%Y-%m-%d')}]")
    
    if cond1 and cond2:
        print("  => 結果: 保留 ✅")
    else:
        print("  => 結果: 過濾掉 ❌")
