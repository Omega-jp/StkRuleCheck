import pandas as pd

# 四海游龍規則檢查函數

def check_four_seas_dragon(df: pd.DataFrame, ma_periods: list, stock_id: str) -> None:
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
            # 第一天沒有前一天數據
            results.append({'date': date, 'si_hai_you_long_check': ''})
            last_signal_was_o = False # Reset for no signal
            continue

        # 檢查均線突破條件
        crossover_any_ma = False
        for period in ma_periods:
            ma_col = f'ma{period}'

            current_ma = row[ma_col]
            prev_ma = prev_row[ma_col]

            if (close > current_ma) and (prev_close <= prev_ma):
                crossover_any_ma = True
                break

        # Apply non-consecutive signal logic
        if crossover_any_ma and not last_signal_was_o:
            results.append({'date': date, 'si_hai_you_long_check': 'O'})
            last_signal_was_o = True
        else:
            results.append({'date': date, 'si_hai_you_long_check': ''})
            last_signal_was_o = False

    # 將結果寫入CSV文件
    results_df = pd.DataFrame(results)
    results_df.to_csv(f"{stock_id}_four_seas_dragon.csv", index=False)