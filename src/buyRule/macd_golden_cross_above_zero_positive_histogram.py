import pandas as pd

def check_macd_golden_cross_above_zero_positive_histogram(df: pd.DataFrame) -> pd.DataFrame:
    results = []
    for i, (idx, row) in enumerate(df.iterrows()):
        date = idx.strftime('%Y-%m-%d')
        if 'MACD' not in row or 'Signal' not in row or 'Histogram' not in row or pd.isna(row['MACD']) or pd.isna(row['Signal']) or pd.isna(row['Histogram']):
            results.append({'date': date, 'macd_golden_cross_above_zero_positive_histogram_check': ''})
            continue
        if i > 0:
            prev_row = df.iloc[i - 1]
            if pd.isna(prev_row['MACD']) or pd.isna(prev_row['Signal']) or pd.isna(prev_row['Histogram']):
                results.append({'date': date, 'macd_golden_cross_above_zero_positive_histogram_check': ''})
                continue
            # 黃金交叉: MACD向上穿越Signal
            golden_cross = (row['MACD'] > row['Signal']) and (prev_row['MACD'] <= prev_row['Signal'])
            # 在零軸之上: MACD > 0
            above_zero = row['MACD'] > 0
            # 柱狀體為正值: Histogram > 0
            positive_histogram = row['Histogram'] > 0
            if golden_cross and above_zero and positive_histogram:
                results.append({'date': date, 'macd_golden_cross_above_zero_positive_histogram_check': 'O'})
            else:
                results.append({'date': date, 'macd_golden_cross_above_zero_positive_histogram_check': ''})
        else:
            results.append({'date': date, 'macd_golden_cross_above_zero_positive_histogram_check': ''})
    return pd.DataFrame(results)