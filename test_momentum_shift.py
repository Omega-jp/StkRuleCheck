#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Momentum Shift 系統測試與視覺化腳本
"""

import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

# 添加 src 目錄到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.buyRule.momentum_shift import compute_momentum_shift
from src.validate_buy_rule import load_stock_data

def test_momentum_shift_logic(stock_id='2330', days=120):
    print(f"\n🚀 開始測試 Momentum Shift 分析: {stock_id}")
    
    # 1. 載入數據
    df = load_stock_data(stock_id, 'D')
    if df is None or df.empty:
        print(f"❌ 無法載入 {stock_id} 的數據")
        return
    
    # 2. 計算 Momentum Shift
    recent_df = df.tail(days).copy()
    results = compute_momentum_shift(recent_df)
    
    # 3. 視覺化
    plt.figure(figsize=(15, 10))
    
    # 設置字體
    preferred_fonts = ['Microsoft JhengHei', 'Arial Unicode MS', 'SimHei']
    for font_name in preferred_fonts:
        try:
            fm.findfont(font_name, fallback_to_default=False)
            plt.rcParams['font.sans-serif'] = [font_name]
            break
        except:
            continue
    plt.rcParams['axes.unicode_minus'] = False

    # A. K線圖與 Momentum Shift Level
    plt.subplot(2, 1, 1)
    dates = results.index
    
    # 繪製 K 棒 (簡化版)
    for i in range(len(results)):
        row = results.iloc[i]
        color = 'red' if row['Close'] >= row['Open'] else 'green'
        plt.plot([dates[i], dates[i]], [row['Low'], row['High']], color='black', linewidth=0.8)
        plt.vlines(dates[i], row['Open'], row['Close'], color=color, linewidth=4)

    # 繪製 Momentum Shift Level (階梯線)
    # 使用更穩健的繪圖方式：逐點繪製線段，並在跳階處連線（或不連線，依需求）
    # 這裡採逐日繪製小段，確保不遺漏任何一天的 Level
    for i in range(len(results) - 1):
        row = results.iloc[i]
        next_row = results.iloc[i+1]
        
        if not np.isnan(row['ms_level']):
            color = 'green' if row['ms_type'] == "Bullish" else 'red'
            # 繪製當天的水平線段 (從當天到隔天)
            plt.hlines(row['ms_level'], xmin=dates[i], xmax=dates[i+1], 
                      colors=color, linewidth=2.5, alpha=0.8)
            
            # 如果隔天跳階了，繪製一條虛擬垂直線連起來 (可選)
            if not np.isnan(next_row['ms_level']) and next_row['ms_level'] != row['ms_level']:
               plt.vlines(dates[i+1], row['ms_level'], next_row['ms_level'], 
                          colors=color, linestyles=':', alpha=0.5)

    # 最後一天的 Level 補一個短線
    last_idx = len(results) - 1
    last_row = results.iloc[last_idx]
    if not np.isnan(last_row['ms_level']):
        color = 'green' if last_row['ms_type'] == "Bullish" else 'red'
        # 往後延一點點點方便看見 (xmin == xmax 在有些 plt 版本可能不顯示，所以加一點位移)
        plt.hlines(last_row['ms_level'], xmin=dates[last_idx], xmax=dates[last_idx] + pd.Timedelta(hours=12), 
                  colors=color, linewidth=2.5, alpha=0.8)

    # 標記買進訊號
    buy_signals = results[results['ms_buy_signal'] == 'O']
    if not buy_signals.empty:
        plt.scatter(buy_signals.index, buy_signals['Low'] * 0.98, marker='^', color='orange', s=100, label='Buy Signal')
        print(f"   買進訊號日期: {buy_signals.index.strftime('%Y-%m-%d').tolist()}")
    
    # 標記賣出訊號
    sell_signals = results[results['ms_sell_signal'] == 'O']
    if not sell_signals.empty:
        plt.scatter(sell_signals.index, sell_signals['High'] * 1.02, marker='v', color='blue', s=100, label='Sell Signal')
        print(f"   賣出訊號日期: {sell_signals.index.strftime('%Y-%m-%d').tolist()}")

    # 打印 Level 更新日期
    levels_info = results[results['ms_level'].diff() != 0].copy()
    jan_levels = levels_info[levels_info.index.month == 1]
    print(f"   一月份 Level 更新日期: {jan_levels.index.strftime('%Y-%m-%d').tolist()}")
    print(f"   一月份總更新次數: {len(jan_levels)}")

    plt.title(f'{stock_id} Momentum Shift 綜合分析')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # B. 成交量
    plt.subplot(2, 1, 2)
    plt.bar(dates, results['Volume'], color='gray', alpha=0.5)
    plt.title('成交量')
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    output_path = f'output/test_charts/{stock_id}_momentum_shift.png'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    print(f"✅ 測試圖表已存至: {output_path}")
    plt.close()

if __name__ == "__main__":
    # 測試多種股票，模型已自動並行計算
    test_momentum_shift_logic('0050')
    test_momentum_shift_logic('00631L')
