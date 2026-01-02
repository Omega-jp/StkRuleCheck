#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試腳本：檢查 00981A 在 2025-12 月的底分型問題
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
if df is None or df.empty:
    print("無法載入數據")
    exit(1)

# 確保有日期索引
if not isinstance(df.index, pd.DatetimeIndex):
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")

# 計算 MA5
if "ma5" not in df.columns:
    df["ma5"] = df["Close"].rolling(window=5, min_periods=1).mean()

# 只看最近 120 天
df = df.tail(120)

# 識別轉折點
turning_points = identify_turning_points(df)
turning_points["date"] = pd.to_datetime(turning_points["date"])
turning_points = turning_points.set_index("date")

# 識別底分型（有上下文）
fractals_with_context = identify_bottom_fractals(
    df, left=2, right=2, tol=0.0, turning_points_df=turning_points.reset_index()
)
fractals_with_context["date"] = pd.to_datetime(fractals_with_context["date"])
fractals_with_context = fractals_with_context.set_index("date")

# 識別底分型（無上下文）
fractals_no_context = identify_bottom_fractals(
    df, left=2, right=2, tol=0.0, turning_points_df=None
)
fractals_no_context["date"] = pd.to_datetime(fractals_no_context["date"])
fractals_no_context = fractals_no_context.set_index("date")

# 找出 2025-12 月的數據
dec_data = df["2025-12":"2025-12"]
print("\n=== 2025-12 月數據 ===")
print(f"日期範圍: {dec_data.index[0]} 到 {dec_data.index[-1]}")

# 找出 12 月的轉折點
dec_tp = turning_points["2025-12":"2025-12"]
print("\n=== 2025-12 月轉折點 ===")
for idx, row in dec_tp.iterrows():
    if row["turning_high_point"] == "O":
        print(f"{idx.strftime('%Y-%m-%d')}: 轉折高點 (High={df.loc[idx, 'High']:.2f})")
    if row["turning_low_point"] == "O":
        print(f"{idx.strftime('%Y-%m-%d')}: 轉折低點 (Low={df.loc[idx, 'Low']:.2f})")

# 找出 12 月的底分型（有上下文）
dec_fractals_ctx = fractals_with_context["2025-12":"2025-12"]
dec_fractals_ctx = dec_fractals_ctx[dec_fractals_ctx["bottom_fractal"] == "O"]
print("\n=== 2025-12 月底分型（有上下文過濾）===")
if dec_fractals_ctx.empty:
    print("無底分型")
else:
    for idx, row in dec_fractals_ctx.iterrows():
        print(f"{idx.strftime('%Y-%m-%d')}: 底分型 (Low={row['fractal_low']:.2f}, 低點日期={row['fractal_low_date']})")

# 找出 12 月的底分型（無上下文）
dec_fractals_no_ctx = fractals_no_context["2025-12":"2025-12"]
dec_fractals_no_ctx = dec_fractals_no_ctx[dec_fractals_no_ctx["bottom_fractal"] == "O"]
print("\n=== 2025-12 月底分型（無上下文過濾）===")
if dec_fractals_no_ctx.empty:
    print("無底分型")
else:
    for idx, row in dec_fractals_no_ctx.iterrows():
        print(f"{idx.strftime('%Y-%m-%d')}: 底分型 (Low={row['fractal_low']:.2f}, 低點日期={row['fractal_low_date']})")

# 查看 12 月前後的轉折點序列
print("\n=== 最近的轉折點序列 ===")
all_tp = turning_points[
    (turning_points["turning_high_point"] == "O") | 
    (turning_points["turning_low_point"] == "O")
].tail(10)
for idx, row in all_tp.iterrows():
    tp_type = "高點" if row["turning_high_point"] == "O" else "低點"
    price = df.loc[idx, "High"] if row["turning_high_point"] == "O" else df.loc[idx, "Low"]
    print(f"{idx.strftime('%Y-%m-%d')}: 轉折{tp_type} ({price:.2f})")
