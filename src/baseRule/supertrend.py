import pandas as pd
import numpy as np

def calculate_atr(df: pd.DataFrame, period: int) -> pd.Series:
    """
    Calculate ATR using RMA (Running Moving Average / Wilder's Smoothing)
    to match Pine Script's ta.atr()
    """
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    # Calculate True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # RMA (Wilder's Smoothing) initialization
    # First value is usually SMA, subsequent are RMA
    # RMA_t = alpha * x_t + (1-alpha) * RMA_{t-1}, alpha = 1/period
    rma = tr.ewm(alpha=1/period, adjust=False).mean()
    
    return rma

def calculate_supertrend(df: pd.DataFrame, period: int, factor: float) -> pd.DataFrame:
    """
    Calculate Supertrend Indicator
    Returns DataFrame with:
    - Supertrend: The trend line value
    - Direction: 1 for Up, -1 for Down
    """
    # Create a copy to avoid SettingWithCopy warnings on input df
    local_df = df.copy()
    
    atr = calculate_atr(local_df, period)
    
    hl2 = (local_df['High'] + local_df['Low']) / 2
    
    basic_upper = hl2 + (factor * atr)
    basic_lower = hl2 - (factor * atr)
    
    final_upper = pd.Series(index=local_df.index, dtype='float64')
    final_lower = pd.Series(index=local_df.index, dtype='float64')
    trend = pd.Series(index=local_df.index, dtype='int64')
    supertrend = pd.Series(index=local_df.index, dtype='float64')
    
    # Initialize first values
    final_upper.iloc[0] = basic_upper.iloc[0]
    final_lower.iloc[0] = basic_lower.iloc[0]
    trend.iloc[0] = 1 # Assume Up initially
    supertrend.iloc[0] = final_lower.iloc[0]
    
    # Iterate (Vectorization is hard for recursive Supertrend logic, looping is safer for exact logic)
    # Using numpy arrays for speed
    close_vals = local_df['Close'].values
    bu_vals = basic_upper.values
    bl_vals = basic_lower.values
    
    fu_vals = np.zeros(len(local_df))
    fl_vals = np.zeros(len(local_df))
    trend_vals = np.zeros(len(local_df))
    st_vals = np.zeros(len(local_df))
    
    # Init
    fu_vals[0] = bu_vals[0]
    fl_vals[0] = bl_vals[0]
    trend_vals[0] = 1
    st_vals[0] = fl_vals[0]
    
    for i in range(1, len(local_df)):
        # Final Upper
        if (bu_vals[i] < fu_vals[i-1]) or (close_vals[i-1] > fu_vals[i-1]):
            fu_vals[i] = bu_vals[i]
        else:
            fu_vals[i] = fu_vals[i-1]
            
        # Final Lower
        if (bl_vals[i] > fl_vals[i-1]) or (close_vals[i-1] < fl_vals[i-1]):
            fl_vals[i] = bl_vals[i]
        else:
            fl_vals[i] = fl_vals[i-1]
            
        # Trend
        prev_trend = trend_vals[i-1]
        if prev_trend == -1: # Down
            if close_vals[i] > fu_vals[i-1]:
                trend_vals[i] = 1 # Turn Up
            else:
                trend_vals[i] = -1
        else: # Up
            if close_vals[i] < fl_vals[i-1]:
                trend_vals[i] = -1 # Turn Down
            else:
                trend_vals[i] = 1
        
        # Supertrend Value
        if trend_vals[i] == 1:
            st_vals[i] = fl_vals[i]
        else:
            st_vals[i] = fu_vals[i]
            
    result = pd.DataFrame(index=local_df.index)
    result['Supertrend'] = st_vals
    result['Direction'] = trend_vals
    
    return result
