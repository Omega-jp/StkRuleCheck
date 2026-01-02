#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
詳細檢查 00981A 12月中旬的底分型問題
"""

import sys
import os
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.validate_buy_rule import load_stock_data
from src.baseRule.turning_point_identification import identify_turning_points
from src.baseRule.bottom_fractal_identification import identify_bottom_fractals

# 載入數據
df = load_stock_data("00981A", "D")
if not isinstance(df.index, pd.DatetimeIndex):
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")

if "ma5" not in df.columns:
    df["ma5"] = df["Close"].rolling(window=5, min_periods=1).mean()

df = df.tail(120)

# 識別轉折點
turning_points = identify_turning_points(df)

# 識別底分型（有上下文）
fractals = identify_bottom_fractals(
    df, left=2, right=2, tol=0.0, turning_points_df=turning_points
)

# 轉換為索引
tp_df = turning_points.copy()
tp_df["date"] = pd.to_datetime(tp_df["date"])
tp_df = tp_df.set_index("date")

frac_df = fractals.copy()
frac_df["date"] = pd.to_datetime(frac_df["date"])
frac_df = frac_df.set_index("date")

# 重點檢查 12/18 轉折低點之後的情況
print("\n=== 檢查 2025-12-18 轉折低點之後 ===")
print(f"2025-12-18 是轉折低點: {tp_df.loc['2025-12-18', 'turning_low_point'] == 'O'}")

# 查看 12/18 之後到 12/31 之間的所有底分型
after_1218 = frac_df["2025-12-19":"2025-12-30"]
after_1218_fractals = after_1218[after_1218["bottom_fractal"] == "O"]

print(f"\n12/18 之後到 12/30 之間偵測到的底分型:")
if after_1218_fractals.empty:
    print("  無（正確！）")
else:
    print("  有問題！不應該有底分型：")
    for idx, row in after_1218_fractals.iterrows():
        print(f"  - {idx.strftime('%Y-%m-%d')}: 底分型 (Low={row['fractal_low']:.2f})")

# 檢查每個日期的最近轉折點
print("\n=== 12/18 到 12/31 每日的最近轉折點 ===")
tp_list = []
for idx, row in tp_df.iterrows():
    if row["turning_high_point"] == "O":
        tp_list.append((idx, "high"))
    elif row["turning_low_point"] == "O":
        tp_list.append((idx, "low"))
tp_list.sort(key=lambda x: x[0])

for date in pd.date_range("2025-12-18", "2025-12-31"):
    if date not in df.index:
        continue
    
    # 找最近的轉折點
    recent_tp = None
    for tp_date, tp_type in reversed(tp_list):
        if tp_date <= date:
            recent_tp = (tp_date, tp_type)
            break
    
    has_fractal = frac_df.loc[date, "bottom_fractal"] == "O" if date in frac_df.index else False
    
    if recent_tp:
        tp_date_str = recent_tp[0].strftime('%m/%d')
        tp_type_str = "高" if recent_tp[1] == "high" else "低"
        fractal_str = "有底分型 ⚠️" if has_fractal else ""
        print(f"{date.strftime('%Y-%m-%d')}: 最近轉折={tp_date_str}({tp_type_str}) {fractal_str}")
