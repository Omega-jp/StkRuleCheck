#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查 00642U 價格高點確認過濾邏輯
"""

import sys
import os
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.validate_buy_rule import load_stock_data

# 載入數據
df = load_stock_data("00642U", "D")
if not isinstance(df.index, pd.DatetimeIndex):
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")

# 檢查 11/12 附近的數據
print("\n=== 2025-11-12 轉折高點附近數據 ===")
near_nov = df["2025-11-05":"2025-11-15"]
for idx, row in near_nov.iterrows():
    print(f"{idx.strftime('%Y-%m-%d')}: High={row['High']}, Low={row['Low']}, Close={row['Close']}")

print("\n=== 分析 ===")
print("底分型低點在 11/11 (Low=15.58)")
print("轉折高點在 11/12")
high_1112 = df.loc["2025-11-12", "High"]
high_1111 = df.loc["2025-11-11", "High"]
print(f"11/12 High: {high_1112}")
print(f"11/11 High: {high_1111}")

if high_1112 >= high_1111:
    print("結論: 11/12 價格更高，所以 11/11 的低點確實在最高點之前。過濾正確 ✅")
else:
    print("結論: 11/11 價格更高，轉折點滯後。可能誤殺 ⚠️")

# 檢查 9/17 附近的數據
print("\n=== 2025-09-17 轉折高點附近數據 ===")
near_sep = df["2025-09-10":"2025-09-20"]
for idx, row in near_sep.iterrows():
    print(f"{idx.strftime('%Y-%m-%d')}: High={row['High']}, Low={row['Low']}, Close={row['Close']}")

print("\n=== 分析 ===")
print("底分型低點在 9/12")
print("轉折高點在 9/17")
high_0917 = df.loc["2025-09-17", "High"]
high_0912 = df.loc["2025-09-12", "High"]
if high_0917 >= high_0912:
    print("結論: 9/17 價格更高，過濾正確 ✅")
else:
    print("結論: 9/12 價格更高，過濾正確嗎？")
