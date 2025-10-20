import pandas as pd

def calculate_macd(df, short_period=10, long_period=20, signal_period=10):
    """
    Calculate Moving Average Convergence Divergence (MACD) values.

    Args:
        df (pd.DataFrame): DataFrame with a 'Close' column (收盤價).
        short_period (int): Period for the short-term EMA (default 10).
        long_period (int): Period for the long-term EMA (default 20).
        signal_period (int): Period for the signal line EMA (default 10).

    Returns:
        pd.DataFrame: DataFrame with 'EMA_short', 'EMA_long', 'MACD', 'Signal', 'Histogram' columns.
    """
    df_copy = df.copy()

    # Calculate Short-term EMA
    df_copy['EMA_short'] = df_copy['Close'].ewm(span=short_period, adjust=False).mean()

    # Calculate Long-term EMA
    df_copy['EMA_long'] = df_copy['Close'].ewm(span=long_period, adjust=False).mean()

    # Calculate MACD Line
    df_copy['MACD'] = df_copy['EMA_short'] - df_copy['EMA_long']

    # Calculate Signal Line
    df_copy['Signal'] = df_copy['MACD'].ewm(span=signal_period, adjust=False).mean()

    # Calculate MACD Histogram
    df_copy['Histogram'] = df_copy['MACD'] - df_copy['Signal']

    return df_copy[['MACD', 'Signal', 'Histogram']]

if __name__ == "__main__":
    # Example usage (for testing purposes)
    data = {
        'Close': [10, 12, 15, 13, 16, 18, 17, 19, 22, 20, 25, 23, 26, 28, 27, 30, 32, 31, 34, 33]
    }
    df_test = pd.DataFrame(data)
    macd_results = calculate_macd(df_test)
    print(macd_results)