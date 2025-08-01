import pandas as pd

def check_san_yang_kai_tai(df: pd.DataFrame) -> pd.DataFrame:
    results = []
    for i, (idx, row) in enumerate(df.iterrows()):
        date = idx.strftime('%Y-%m-%d')
        close = row['Close']
        ma5 = row['ma5']
        ma10 = row['ma10']
        ma20 = row['ma20']

        if pd.isna(ma5) or pd.isna(ma10) or pd.isna(ma20):
            results.append({'date': date, 'san_yang_kai_tai_check': ''})
            continue
        if i > 0:
            prev_row = df.iloc[i - 1]
            prev_close = prev_row['Close']
            prev_ma5 = prev_row['ma5']
            prev_ma10 = prev_row['ma10']
            prev_ma20 = prev_row['ma20']
        else:
            results.append({'date': date, 'san_yang_kai_tai_check': ''})
            continue
        # CROSS OVER: 當天首次突破且站上
        crossover_ma5 = (close >= ma5 and prev_close < prev_ma5)
        crossover_ma10 = (close >= ma10 and prev_close < prev_ma10)
        crossover_ma20 = (close >= ma20 and prev_close < prev_ma20)
        breakthrough_any = crossover_ma5 or crossover_ma10 or crossover_ma20
        above_all_ma = (close >= ma5) and (close >= ma10) and (close >= ma20)
        if breakthrough_any and above_all_ma:
            results.append({'date': date, 'san_yang_kai_tai_check': 'O'})
        else:
            results.append({'date': date, 'san_yang_kai_tai_check': ''})
    return pd.DataFrame(results)


def check_four_seas_dragon(df: pd.DataFrame, ma_periods: list) -> pd.DataFrame:
    """
    遍歷整個K線，如果當天收盤突破任何一個指定的均線 (MA)，
    回傳滿足該條件的K棒日期。

    Args:
        df (pd.DataFrame): 包含K線數據的DataFrame，需要包含 'Close' 和指定均線列。
        ma_periods (list): 包含需要檢查的均線週期的列表，例如 [5, 10, 20, 60]。

    Returns:
        pd.DataFrame: 包含 'date' 和 'si_hai_you_long_check' 列的DataFrame，
                      'si_hai_you_long_check' 為 'O' 表示滿足條件，'' 表示不滿足。
    """
    results = []
    last_signal_was_o = False # Track if the last signal was 'O'

    for i, (idx, row) in enumerate(df.iterrows()):
        date = idx.strftime('%Y-%m-%d')
        close = row['Close']
        
        # 確保所有需要的均線數據都存在
        all_ma_present = True
        for period in ma_periods:
            ma_col = f'ma{period}'
            if ma_col not in df.columns or pd.isna(row[ma_col]):
                all_ma_present = False
                break
        
        if not all_ma_present:
            results.append({'date': date, 'si_hai_you_long_check': ''})
            last_signal_was_o = False # Reset for no signal
            continue

        # 獲取前一天的數據
        if i > 0:
            prev_row = df.iloc[i - 1]
            prev_close = prev_row['Close']
            
            # 確保前一天的均線數據也存在
            prev_ma_present = True
            for period in ma_periods:
                ma_col = f'ma{period}'
                if ma_col not in prev_row or pd.isna(prev_row[ma_col]):
                    prev_ma_present = False
                    break
            
            if not prev_ma_present:
                results.append({'date': date, 'si_hai_you_long_check': ''})
                last_signal_was_o = False # Reset for no signal
                continue
        else:
            # 第一天沒有前一天數據，不滿足突破條件
            results.append({'date': date, 'si_hai_you_long_check': ''})
            last_signal_was_o = False # Reset for no signal
            continue

        # 檢查均線突破條件 (CrossOver)
        crossover_any_ma = False
        for period in ma_periods:
            ma_col = f'ma{period}'
            
            current_ma = row[ma_col]
            prev_ma = prev_row[ma_col]
 
            if (close > current_ma) and (prev_close <= prev_ma):
                crossover_any_ma = True
                break # 只要突破任何一條均線就滿足條件
        
        # Apply non-consecutive signal logic
        if crossover_any_ma and not last_signal_was_o:
            results.append({'date': date, 'si_hai_you_long_check': 'O'})
            last_signal_was_o = True
        else:
            results.append({'date': date, 'si_hai_you_long_check': ''})
            last_signal_was_o = False

    return pd.DataFrame(results)


def combine_buy_rules(df: pd.DataFrame, four_seas_ma_periods: list) -> pd.DataFrame:
    """
    結合三陽開泰和四海游龍兩種買入規則的檢查結果。

    Args:
        df (pd.DataFrame): 包含K線數據的DataFrame，需要包含 'Close', 'ma5', 'ma10', 'ma20' 列，
                           以及四海游龍所需的均線列。
        four_seas_ma_periods (list): 包含四海游龍需要檢查的均線週期的列表，例如 [5, 10, 20, 60]。

    Returns:
        pd.DataFrame: 包含 'date', 'san_yang_kai_tai_check', 和 'si_hai_you_long_check' 列的DataFrame。
    """
    san_yang_results = check_breakthrough_ma(df.copy())
    si_hai_results = check_four_seas_dragon(df.copy(), four_seas_ma_periods)

    # 合併兩個規則的結果
    combined_results = pd.merge(san_yang_results, si_hai_results, on='date', how='left')
    return combined_results
