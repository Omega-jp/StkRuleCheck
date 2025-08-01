import pandas as pd

def check_macd_golden_cross_above_zero(df: pd.DataFrame) -> pd.DataFrame:
    results = []
    for i, (idx, row) in enumerate(df.iterrows()):
        date = idx.strftime('%Y-%m-%d')
        if 'MACD' not in row or 'Signal' not in row or pd.isna(row['MACD']) or pd.isna(row['Signal']):
            results.append({'date': date, 'macd_golden_cross_above_zero_check': ''})
            continue
        if i > 0:
            prev_row = df.iloc[i - 1]
            if pd.isna(prev_row['MACD']) or pd.isna(prev_row['Signal']):
                results.append({'date': date, 'macd_golden_cross_above_zero_check': ''})
                continue
            # 黃金交叉: MACD向上穿越Signal
            golden_cross = (row['MACD'] > row['Signal']) and (prev_row['MACD'] <= prev_row['Signal'])
            # 在零軸之上: MACD > 0
            above_zero = row['MACD'] > 0
            if golden_cross and above_zero:
                results.append({'date': date, 'macd_golden_cross_above_zero_check': 'O'})
            else:
                results.append({'date': date, 'macd_golden_cross_above_zero_check': ''})
        else:
            results.append({'date': date, 'macd_golden_cross_above_zero_check': ''})
    return pd.DataFrame(results)