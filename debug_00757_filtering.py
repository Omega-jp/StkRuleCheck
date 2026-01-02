#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試腳本：檢查 00757 底分型消失的原因
"""

import sys
import os
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.validate_buy_rule import load_stock_data
from src.baseRule.turning_point_identification import identify_turning_points
from src.baseRule.bottom_fractal_identification import identify_bottom_fractals

# 載入數據
stock_id = "00757"
df = load_stock_data(stock_id, "D")
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
print(f"\n=== {stock_id} 原始底分型（無過濾）===")
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
    if not isinstance(idx, pd.Timestamp):
        continue
        
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
        print("  -> 無最近轉折點 (過濾結果: 視實作而定)")
        continue
        
    print(f"  -> 最近轉折點: {recent_tp['date'].strftime('%Y-%m-%d')} ({recent_tp['type']})")
    
    # 條件檢查 (模擬新邏輯)
    should_keep = True
    
    if recent_tp['type'] == 'high':
        # 條件 1: 若最近是高點，分型低點日期必須 >= 轉折高點日期
        if fractal_low_date < recent_tp['date']:
            should_keep = False
            print(f"  -> 條件(高點): FAIL [低點 {fractal_low_date_str} < 轉折 {recent_tp['date'].strftime('%Y-%m-%d')}]")
        else:
            print(f"  -> 條件(高點): PASS")
            
    elif recent_tp['type'] == 'low':
        # 條件 2: 若最近是低點，只有當分型低點日期 == 轉折低點日期才允許
        if fractal_low_date != recent_tp['date']:
            should_keep = False
            print(f"  -> 條件(低點): FAIL [低點 {fractal_low_date_str} != 轉折 {recent_tp['date'].strftime('%Y-%m-%d')}]")
        else:
            print(f"  -> 條件(低點): PASS [低點 == 轉折日]")

    # 檢查價格是否有創新高（輔助判斷）
    if recent_tp['type'] == 'high':
        tp_high_price = df.loc[recent_tp['date'], "High"]
        fractal_high_price = df.loc[fractal_low_date, "High"]
        if tp_high_price < fractal_high_price:
             print("     (警告: 分型日價格更高，轉折點可能滯後)")

    if should_keep:
        print("  => 結果: 保留 ✅")
    else:
        print("  => 結果: 過濾掉 ❌")
