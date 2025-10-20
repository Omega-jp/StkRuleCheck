import pandas as pd
import numpy as np

def calculate_kd(df, n=5, m1=3, m2=3):
    """
    Calculate Stochastic Oscillator (KD) values.
    RSV = (Current Close - Lowest Low) / (Highest High - Lowest Low) * 100
    %K = m1-period SMMA of RSV
    %D = m2-period SMMA of %K

    Args:
        df (pd.DataFrame): DataFrame with 'High', 'Low', 'Close' columns.
        n (int): Lookback period for Highest High and Lowest Low (default 5).
        m1 (int): Smoothing period for %K (default 3).
        m2 (int): Smoothing period for %D (default 3).
    Returns:
        pd.DataFrame: DataFrame with 'RSV', '%K' and '%D' columns.
    """
    df_copy = df.copy()

    # Calculate Lowest Low (LLV) and Highest High (HHV) over n periods, including current day
    df_copy['LLV'] = df_copy['Low'].rolling(window=n, min_periods=1).min()
    df_copy['HHV'] = df_copy['High'].rolling(window=n, min_periods=1).max()

    # Calculate RSV with proper pandas chaining and handle edge cases
    range_hl = df_copy['HHV'] - df_copy['LLV']
    df_copy = df_copy.assign(
        RSV=((df_copy['Close'] - df_copy['LLV']) / range_hl.replace(0, np.nan)) * 100
    ).fillna({'RSV': 0})


    # Calculate %K (m1-period SMMA of RSV)
    # Use adjust=True for SMMA calculation
    df_copy['%K'] = df_copy['RSV'].ewm(alpha=1/m1, adjust=False, min_periods=1).mean()

    # Calculate %D (m2-period SMMA of %K)
    # Use adjust=True for SMMA calculation
    df_copy['%D'] = df_copy['%K'].ewm(alpha=1/m2, adjust=False, min_periods=1).mean()

    return df_copy[['RSV', '%K', '%D']]
