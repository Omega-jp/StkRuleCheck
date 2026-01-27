#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triple Supertrend Visualization Test
"""
import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.dirname(__file__))

from src.validate_buy_rule import load_stock_data
from src.buyRule.triple_supertrend import check_triple_supertrend
from src.baseRule.supertrend import calculate_supertrend

def plot_triple_supertrend(stock_id='00631L', days=180):
    print(f"\n{'='*60}")
    print(f"Triple Supertrend Test: {stock_id}")
    print(f"{'='*60}")
    
    # 1. Load Data
    df = load_stock_data(stock_id, 'D')
    if df is None:
        print(f"Cannot load data for {stock_id}")
        return
        
    recent_df = df.tail(days).copy()
    
    # 2. Calculate Indicators (Re-calculate for plotting to get lines)
    # The buy rule returns checks, but we need the actual lines for plotting
    
    # Group 1 (Scalp)
    st1 = calculate_supertrend(recent_df, 10, 1.0)
    # Group 2 (Standard)
    st2 = calculate_supertrend(recent_df, 11, 2.0)
    # Group 3 (Major)
    st3 = calculate_supertrend(recent_df, 12, 3.0)
    
    # Get Buy Signals
    signals = check_triple_supertrend(recent_df)
    
    # 3. Setup Plot
    plt.figure(figsize=(16, 10))
    
    # Chinese Font support
    preferred_fonts = ['Microsoft JhengHei', 'Arial Unicode MS', 'SimHei']
    selected_font = None
    for font_name in preferred_fonts:
        try:
            fm.findfont(font_name, fallback_to_default=False)
            selected_font = font_name
            break
        except ValueError:
            continue
    if selected_font:
        plt.rcParams['font.sans-serif'] = [selected_font]
    plt.rcParams['axes.unicode_minus'] = False

    # Main Subplot
    ax = plt.subplot(1, 1, 1)
    
    # Plot K-Candles (Simplified)
    dates = recent_df.index
    opens = recent_df['Open']
    closes = recent_df['Close']
    highs = recent_df['High']
    lows = recent_df['Low']
    
    col_up = 'red'
    col_down = 'blue' # Changed from green to avoid confusion
    
    # 4. Draw Candles and Supertrends
    for i, date in enumerate(dates):
        o, c, h, l = opens.iloc[i], closes.iloc[i], highs.iloc[i], lows.iloc[i]
        
        # Shadow Line (Single black line)
        ax.plot([date, date], [l, h], color='black', linewidth=0.8, alpha=0.5, zorder=5)
        
        # Body
        body_bottom = min(o, c)
        body_height = abs(o - c)
        
        if c >= o:
            rect = plt.Rectangle((date - pd.Timedelta(days=0.3), body_bottom), 
                               pd.Timedelta(days=0.6), body_height,
                               facecolor='white', edgecolor=col_up, zorder=10)
        else:
            rect = plt.Rectangle((date - pd.Timedelta(days=0.3), body_bottom), 
                               pd.Timedelta(days=0.6), body_height,
                               facecolor=col_down, edgecolor=col_down, zorder=10)
        ax.add_patch(rect)

    # Calculate 3 Supertrends
    line1 = st1['Supertrend']
    line2 = st2['Supertrend']
    line3 = st3['Supertrend']
    dir1 = st1['Direction']
    
    # Fills between lines (G1-G2, G2-G3) to show the "envelope"
    # Logic: Fill green if G2 (Std) is UP, red if G2 is DOWN
    is_up = st2['Direction'] == 1
    is_down = st2['Direction'] == -1
    
    ax.fill_between(dates, line1, line2, where=is_up, color='green', alpha=0.08, zorder=0)
    ax.fill_between(dates, line1, line2, where=is_down, color='red', alpha=0.08, zorder=0)
    
    ax.fill_between(dates, line2, line3, where=is_up, color='green', alpha=0.05, zorder=0)
    ax.fill_between(dates, line2, line3, where=is_down, color='red', alpha=0.05, zorder=0)

    # Helper to plot one ST line continuously
    def draw_continuous_line(dates, line_series, direction_series, color_up, color_down, label, linestyle='-', linewidth=1.0):
        g = direction_series.ne(direction_series.shift()).cumsum()
        for gid, group in line_series.groupby(g):
            d = direction_series.loc[group.index[0]]
            c = color_up if d == 1 else color_down
            
            idx_start = line_series.index.get_loc(group.index[0])
            idx_end = line_series.index.get_loc(group.index[-1])
            
            # Plot segment
            ax.plot(dates[idx_start:idx_end+1], line_series.iloc[idx_start:idx_end+1], 
                    color=c, linestyle=linestyle, linewidth=linewidth, alpha=0.9, zorder=12)
            
            # Connect to next segment if exists
            if idx_end < len(line_series) - 1:
                next_d = direction_series.iloc[idx_end + 1]
                next_c = color_up if next_d == 1 else color_down
                
                # Vertical line at the transition (connection line)
                # Use next_c (the new trend color) as requested
                ax.plot([dates[idx_end], dates[idx_end+1]], 
                        [line_series.iloc[idx_end], line_series.iloc[idx_end+1]], 
                        color=next_c, linestyle=linestyle, linewidth=linewidth, alpha=0.9, zorder=12)

    # Plot the 3 lines with distinct styles/labels
    draw_continuous_line(dates, line1, dir1, 'lime', 'maroon', 'ST1 (Scalp)', linestyle=':', linewidth=0.8)
    draw_continuous_line(dates, line2, st2['Direction'], 'green', 'red', 'ST2 (Std)', linestyle='--', linewidth=1.0)
    draw_continuous_line(dates, line3, st3['Direction'], 'darkgreen', 'darkred', 'ST3 (Major)', linestyle='-', linewidth=1.2)
    
    # Dummy plots for legend
    ax.plot([], [], color='green', linestyle=':', label='G1: Scalp (10, 1.0)')
    ax.plot([], [], color='green', linestyle='--', label='G2: Standard (11, 2.0)')
    ax.plot([], [], color='green', linestyle='-', label='G3: Major (12, 3.0)')
    ax.plot([], [], color='red', linestyle='-', label='Down Trend (Red Fill)')

    # 5. Mark Signals
    # G2: Standard (Triangle Up)
    g2_idx = signals[signals['triple_supertrend_g2_check'] == 'O'].index
    if len(g2_idx) > 0:
        ax.scatter(g2_idx, lows.loc[g2_idx]*0.99, marker='^', color='blue', s=80, label='Std Break (G2)', zorder=15)
        
    # G1: Scalp (Small dot)
    g1_idx = signals[signals['triple_supertrend_g1_check'] == 'O'].index
    if len(g1_idx) > 0:
        ax.scatter(g1_idx, lows.loc[g1_idx]*0.995, marker='.', color='purple', s=50, label='Scalp Break (G1)', zorder=15)
        
    # All: Resonance (Big Star)
    all_idx = signals[signals['triple_supertrend_all_check'] == 'O'].index
    if len(all_idx) > 0:
        ax.scatter(all_idx, lows.loc[all_idx]*0.98, marker='*', color='gold', edgecolor='black', s=200, label='TRIPLE RESONANCE', zorder=20)
        
    plt.title(f"{stock_id} Triple Supertrend Strategy Visualization")
    plt.legend(loc='best', framealpha=0.5)
    plt.grid(True, alpha=0.3)
    
    # Save
    output_dir = 'output/test_charts'
    os.makedirs(output_dir, exist_ok=True)
    fpath = f"{output_dir}/{stock_id}_triple_supertrend.png"
    plt.savefig(fpath)
    print(f"Chart saved to {fpath}")
    # plt.show() # Interactive mode often not avail

def main():
    while True:
        sid = input("Stock ID (default 00631L, q to quit): ").strip()
        if sid.lower() == 'q': break
        if not sid: sid = '00631L'
        plot_triple_supertrend(sid)

if __name__ == "__main__":
    main()
