
import pandas as pd
import numpy as np
import sys
import os

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), 'src'))
from src.validate_buy_rule import load_stock_data

def debug_fractals(stock_id='00652', days=60):
    df = load_stock_data(stock_id, 'D')
    if df is None:
        print("Data not found")
        return

    df = df.tail(days).copy()
    highs = df['High'].values
    lows = df['Low'].values
    
    s_high = pd.Series(highs)
    s_low = pd.Series(lows)
    
    # Logic copied from momentum_shift.py
    c1_h = s_high > s_high.shift(1)
    c2_h = s_high > s_high.shift(2)
    c3_h = s_high > s_high.shift(-1)
    c4_h = s_high > s_high.shift(-2)
    fractal_high_mask = c1_h & c2_h & c3_h & c4_h
    
    c1_l = s_low < s_low.shift(1)
    c2_l = s_low < s_low.shift(2)
    c3_l = s_low < s_low.shift(-1)
    c4_l = s_low < s_low.shift(-2)
    fractal_low_mask = c1_l & c2_l & c3_l & c4_l
    
    is_fractal_high = fractal_high_mask.fillna(False).values
    is_fractal_low = fractal_low_mask.fillna(False).values
    
    print(f"Total rows: {len(df)}")
    print(f"Fractal Highs found: {np.sum(is_fractal_high)}")
    print(f"Fractal Lows found: {np.sum(is_fractal_low)}")
    
    for i in range(len(df)):
        date = df.index[i].strftime('%Y-%m-%d')
        if is_fractal_high[i]:
            print(f"[{date}] Fractal High: {highs[i]}")
        if is_fractal_low[i]:
            print(f"[{date}] Fractal Low: {lows[i]}")

if __name__ == "__main__":
    debug_fractals()
