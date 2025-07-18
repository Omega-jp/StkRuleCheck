import pandas as pd

def check_breakthrough_ma(df: pd.DataFrame) -> pd.DataFrame:
    """
    遍歷整個K線，如果當天收盤突破 5M or 10 MA or 20 Ma，
    並且收盤價大等於所有均線5MA/10/20MA ，回傳滿足該條件的K棒日期。

    Args:
        df (pd.DataFrame): 包含K線數據的DataFrame，需要包含 'close', 'ma5', 'ma10', 'ma20', 'ma60' 列。

    Returns:
        pd.DataFrame: 包含 'date' 和 'san_yang_kai_tai_check' 列的DataFrame，
                      'san_yang_kai_tai_check' 為 'O' 表示滿足條件，'' 表示不滿足。
    """
    results = []
    for index, row in df.iterrows():
        date = row['date']
        close = row['close']
        ma5 = row['ma5']
        ma10 = row['ma10']
        ma20 = row['ma20']
        ma60 = row['ma60']

        # 確保均線數據存在
        if pd.isna(ma5) or pd.isna(ma10) or pd.isna(ma20) or pd.isna(ma60):
            results.append({'date': date, 'san_yang_kai_tai_check': ''})
            continue

        # 獲取前一天的數據
        if index > 0:
            prev_row = df.iloc[index - 1]
            prev_close = prev_row['close']
            prev_ma5 = prev_row['ma5']
            prev_ma10 = prev_row['ma10']
            prev_ma20 = prev_row['ma20']
            prev_ma60 = prev_row['ma60']
        else:
            # 第一天沒有前一天數據，不滿足突破條件
            results.append({'date': date, 'san_yang_kai_tai_check': ''})
            continue

        # 檢查均線突破條件 (CrossOver)
        crossover_ma5 = (close > ma5) and (prev_close <= prev_ma5)
        crossover_ma10 = (close > ma10) and (prev_close <= prev_ma10)
        crossover_ma20 = (close > ma20) and (prev_close <= prev_ma20)
        crossover_ma60 = (close > ma60) and (prev_close <= prev_ma60)

        if (crossover_ma5 or crossover_ma10 or crossover_ma20 or crossover_ma60) and \
           (close >= ma5 and close >= ma10 and close >= ma20 and close >= ma60):
            results.append({'date': date, 'san_yang_kai_tai_check': 'O'})
        else:
            results.append({'date': date, 'san_yang_kai_tai_check': ''})

    return pd.DataFrame(results)


def check_four_seas_dragon(df: pd.DataFrame, ma_periods: list) -> pd.DataFrame:
    """
    遍歷整個K線，如果當天收盤突破任何一個指定的均線 (MA)，
    回傳滿足該條件的K棒日期。

    Args:
        df (pd.DataFrame): 包含K線數據的DataFrame，需要包含 'close' 和指定均線列。
        ma_periods (list): 包含需要檢查的均線週期的列表，例如 [5, 10, 20, 60]。

    Returns:
        pd.DataFrame: 包含 'date' 和 'si_hai_you_long_check' 列的DataFrame，
                      'si_hai_you_long_check' 為 'O' 表示滿足條件，'' 表示不滿足。
    """
    results = []
    last_signal_was_o = False # Track if the last signal was 'O'

    for index, row in df.iterrows():
        date = row['date']
        close = row['close']
        
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
        if index > 0:
            prev_row = df.iloc[index - 1]
            prev_close = prev_row['close']
            
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
        df (pd.DataFrame): 包含K線數據的DataFrame，需要包含 'close', 'ma5', 'ma10', 'ma20' 列，
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
