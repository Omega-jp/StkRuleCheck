import pandas as pd

def calculate_ma(df, periods=[5, 10, 20, 60, 120]):
    """
    Calculate Simple Moving Average (MA) values for specified periods.

    Args:
        df (pd.DataFrame): DataFrame with a 'Close' column (收盤價).
        periods (list): A list of integers representing the periods for MA calculation.

    Returns:
        pd.DataFrame: DataFrame with MA columns for each specified period (e.g., 'MA_5', 'MA_10').
    """
    df_copy = df.copy()
    ma_columns = []
    for period in periods:
        col_name = f'MA_{period}'
        df_copy[col_name] = df_copy['收盤價'].rolling(window=period, min_periods=1).mean()
        ma_columns.append(col_name)
    return df_copy[ma_columns]

if __name__ == "__main__":
    # Example usage (for testing purposes)
    data = {
        '收盤價': [10, 12, 15, 13, 16, 18, 17, 19, 22, 20, 25, 23, 26, 28, 27, 30, 32, 31, 34, 33,
                   35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54,
                   55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74,
                   75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94,
                   95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111,
                   112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127]
    }
    df_test = pd.DataFrame(data)
    ma_results = calculate_ma(df_test)
    print(ma_results)