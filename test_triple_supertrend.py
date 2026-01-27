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

def plot_triple_supertrend(stock_id='2330', days=180):
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
    
    # Group 1 (Standard)
    st1 = calculate_supertrend(recent_df, 11, 2.0)
    # Group 2 (Scalp)
    st2 = calculate_supertrend(recent_df, 10, 1.0)
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
    col_down = 'green'
    
    # Draw simple candles
    width = 0.6
    width2 = 0.05
    
    up = closes >= opens
    down = ~up
    
    # High-Low lines
    ax.vlines(dates[up], lows[up], highs[up], color=col_up, linewidth=1)
    ax.vlines(dates[down], lows[down], highs[down], color=col_down, linewidth=1)
    
    # Bodies
    # Up: white face, red edge
    # Down: green face, green edge
    # Matplotlib dates handling needs conversion if using plot_date, but standard plot with index works if index is DatetimeIndex??
    # Actually standard plot with datetime index works fine usually.
    # To draw rectangles we might need numeric dates. Let's use simple iterating plot for robustness similar to previous script or vlines/bar.
    # Using bar for bodies
    # Shift index to numeric for bar width control
    
    # Wait, let's stick to the previous script's method or simplified 'plot'
    # Use simple HLOC plot? No, let's use the helper provided in previous script or just manual loop if small data.
    # 180 days is small.
    
    for i, date in enumerate(dates):
        o, c, h, l = opens.iloc[i], closes.iloc[i], highs.iloc[i], lows.iloc[i]
        
        # Line
        ax.plot([date, date], [l, h], color='black', linewidth=0.8, alpha=0.5)
        
        # Body
        body_bottom = min(o, c)
        body_height = abs(o - c)
        
        if c >= o:
            rect = plt.Rectangle((date - pd.Timedelta(days=0.3), body_bottom), 
                               pd.Timedelta(days=0.6), body_height,
                               facecolor='white', edgecolor='red', zorder=10)
        else:
            rect = plt.Rectangle((date - pd.Timedelta(days=0.3), body_bottom), 
                               pd.Timedelta(days=0.6), body_height,
                               facecolor='green', edgecolor='green', zorder=10)
        ax.add_patch(rect)

    # 4. Plot Supertrends and Fills
    body_middle = (opens + closes) / 2
    
    # Helper to plot one ST
    def plot_st(st_df, name, color_list, linestyle='-'):
        # color_list = [up_color, down_color] (simple names or hex)
        # Using the standard names passed: ('green', 'red'), ('lime', 'maroon'), ('darkgreen', 'darkred')
        line = st_df['Supertrend']
        direction = st_df['Direction']
        
        # 1. Fill Logic (remains similar, using mask)
        is_up = direction == 1
        is_down = direction == -1
        
        # Fill Up (Green-ish)
        ax.fill_between(dates, body_middle, line, where=is_up, 
                        color=color_list[0], alpha=0.1, interpolate=True, zorder=0)
        # Fill Down (Red-ish)
        ax.fill_between(dates, body_middle, line, where=is_down, 
                        color=color_list[1], alpha=0.1, interpolate=True, zorder=0)
        
        # 2. Line Logic (Group by trend for continuous style rendering)
        g = direction.ne(direction.shift()).cumsum()
        
        # Re-implementing correctly using global integer index
        st_df_reset = st_df.reset_index(drop=True) # 0..N index
        g_reset = g.reset_index(drop=True)
        
        for gid, group in st_df_reset.groupby(g_reset):
            d = group['Direction'].iloc[0]
            c = color_list[0] if d == 1 else color_list[1]
            
            idx_start = group.index[0]
            idx_end = group.index[-1]
            
            # Extend end by 1 if not last group
            if idx_end < len(st_df_reset) - 1:
                idx_end += 1
                
            # Plot
            x_seg = dates[idx_start : idx_end+1]
            y_seg = line.iloc[idx_start : idx_end+1]
            
            ax.plot(x_seg, y_seg, color=c, 
                    linewidth=1.0 if linestyle=='-' else 0.8, 
                    linestyle=linestyle, alpha=0.8, zorder=1)

    # Plot Group 1 (Standard) - Dashed
    plot_st(st1, "ST1", ('green', 'red'), linestyle='--')
    # Plot Group 2 (Scalp) - Dotted
    plot_st(st2, "ST2", ('lime', 'maroon'), linestyle=':')
    # Plot Group 3 (Major) - Solid
    plot_st(st3, "ST3", ('darkgreen', 'darkred'), linestyle='-')
    
    # 5. Mark Signals
    # Signals are in `signals` DataFrame
    # triple_supertrend_g1_check, etc.
    
    # G1: Standard (Triangle Up)
    g1_idx = signals[signals['triple_supertrend_g1_check'] == 'O'].index
    if len(g1_idx) > 0:
        ax.scatter(g1_idx, lows.loc[g1_idx]*0.99, marker='^', color='blue', s=60, label='Std Break', zorder=10)
        
    # G2: Short (Small dot)
    g2_idx = signals[signals['triple_supertrend_g2_check'] == 'O'].index
    if len(g2_idx) > 0:
        ax.scatter(g2_idx, lows.loc[g2_idx]*0.995, marker='.', color='purple', s=40, label='Scalp Break', zorder=10)
        
    # All: Resonance (Big Star)
    all_idx = signals[signals['triple_supertrend_all_check'] == 'O'].index
    if len(all_idx) > 0:
        ax.scatter(all_idx, lows.loc[all_idx]*0.98, marker='*', color='gold', edgecolor='black', s=150, label='TRIPLE RESONANCE', zorder=20)
        
    plt.title(f"{stock_id} Triple Supertrend Strategy")
    plt.legend()
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
        sid = input("Stock ID (default 2330, q to quit): ").strip()
        if sid.lower() == 'q': break
        if not sid: sid = '2330'
        plot_triple_supertrend(sid)

if __name__ == "__main__":
    main()
