import pandas as pd

# 四海游龍規則檢查函數

def check_four_seas_dragon(df: pd.DataFrame, ma_periods: list, stock_id: str) -> pd.DataFrame:
    """
    四海游龍規則：與三陽開泰相同邏輯，只要滿足三陽開泰突破條件，且當天收盤價站上最後一個均線（例如60MA），則標記信號 'O'
    """
    from .breakthrough_san_yang_kai_tai import check_san_yang_kai_tai

    # 先取得三陽開泰規則結果
    san_df = check_san_yang_kai_tai(df)

    confirm_period = ma_periods[-1]
    confirm_col = f"ma{confirm_period}"

    results = []
    for _, row in san_df.iterrows():
        date = row['date']
        # 當三陽開泰有信號，且收盤價站上確認線，則四海游龍也標記
        if row.get('san_yang_kai_tai_check') == 'O' and date in df.index:
            close = df.loc[date, 'Close']
            if 'ma' + str(confirm_period) in df.columns and close >= df.loc[date, confirm_col]:
                results.append({'date': date, 'si_hai_you_long_check': 'O'})
            else:
                results.append({'date': date, 'si_hai_you_long_check': ''})
        else:
            results.append({'date': date, 'si_hai_you_long_check': ''})

    return pd.DataFrame(results)