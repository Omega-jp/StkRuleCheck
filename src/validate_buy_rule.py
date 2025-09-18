import pandas as pd
import numpy as np
import os
import mplfinance as mpf
import matplotlib.pyplot as plt # Keep for font settings
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_stock_data(stock_id, data_type='D'):
    """載入股票數據"""
    file_path = f'Data/kbar/{stock_id}_{data_type}.csv'
    if not os.path.exists(file_path):
        print(f"找不到文件: {file_path}")
        return None
    
    try:
        df = pd.read_csv(file_path, index_col='ts', parse_dates=True)
        
        # 檢查並統一欄位名稱
        column_mapping = {
            '開盤價': 'Open',
            '最高價': 'High', 
            '最低價': 'Low',
            '收盤價': 'Close',
            '成交量': 'Volume'
        }
        
        # 如果是中文欄位名稱，轉換為英文
        if '收盤價' in df.columns:
            df.rename(columns=column_mapping, inplace=True)
        
        # 確保必要欄位存在
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"缺少必要欄位: {missing_cols}")
            print(f"現有欄位: {list(df.columns)}")
            return None
            
        return df
    except Exception as e:
        print(f"載入數據時發生錯誤: {e}")
        return None

def plot_candlestick_chart(df, stock_id, buy_signals_dict=None, sell_signals=None):
    """繪製K線圖"""
    if df is None or df.empty:
        print("數據為空，無法繪製圖表")
        return
    
    # 確保數據按時間排序且去重
    df = df.sort_index().drop_duplicates()
    
    # 取最近180天的數據
    recent_df = df.tail(180)
    
    # 設置圖表樣式
    mc = mpf.make_marketcolors(
        up='red',
        down='green',
        edge='inherit',
        wick='inherit',
        volume='inherit'
    )
    s = mpf.make_mpf_style(marketcolors=mc)
    
    # 準備買入和賣出信號的標記
    addplots = []
    panels_to_include = [0, 1] # Always include main and volume (panel 0 and 1)
    panel_ratios_values = [6, 2] # Ratios for main and volume

    # Add moving averages
    for ma in ['ma5', 'ma10', 'ma20', 'ma60']:
        if ma in recent_df.columns:
            addplots.append(
                mpf.make_addplot(recent_df[ma], type='line', width=1, panel=0)
            )

    # Add KD indicator
    if '%K' in recent_df.columns and '%D' in recent_df.columns:
        # Check if there's actual non-NaN data for KD in the recent_df slice
        if recent_df[['%K', '%D']].notnull().sum().sum() > 0:
            kd_panel_idx = len(panels_to_include) # Next available panel index
            addplots.append(
                mpf.make_addplot(recent_df[['%K', '%D']], panel=kd_panel_idx, ylabel='KD', width=1)
            )
            panels_to_include.append(kd_panel_idx)
            panel_ratios_values.append(2) # Add ratio for KD panel
        else:
            print("KD data is all NaN for recent_df, skipping KD plot.")
    
    # Add MACD indicator
    if 'MACD' in recent_df.columns and 'Signal' in recent_df.columns and 'Histogram' in recent_df.columns:
        # Check if there's actual non-NaN data for MACD in the recent_df slice
        if recent_df[['MACD', 'Signal', 'Histogram']].notnull().sum().sum() > 0:
            macd_panel_idx = len(panels_to_include) # Next available panel index
            # Calculate symmetrical Y-axis limits for MACD panel
            macd_abs_max = max(
                abs(recent_df['MACD'].min()), abs(recent_df['MACD'].max()),
                abs(recent_df['Signal'].min()), abs(recent_df['Signal'].max()),
                abs(recent_df['Histogram'].min()), abs(recent_df['Histogram'].max())
            )
            macd_ylim = (-macd_abs_max * 1.1, macd_abs_max * 1.1)
            addplots.append(
                mpf.make_addplot(recent_df[['MACD', 'Signal']], panel=macd_panel_idx, ylabel='MACD', width=1, ylim=macd_ylim)
            )
            # 使用條件顏色：正值綠色，負值紅色
            histogram_colors = ['green' if h >= 0 else 'red' for h in recent_df['Histogram']]
            addplots.append(
                mpf.make_addplot(recent_df['Histogram'], type='bar', panel=macd_panel_idx, color=histogram_colors, width=0.7, alpha=0.7)
            )
            panels_to_include.append(macd_panel_idx)
            panel_ratios_values.append(2) # Add ratio for MACD panel
        else:
            print("MACD data is all NaN for recent_df, skipping MACD plot.")

    # Add buy signals (supports multiple rules)
    if buy_signals_dict is not None:
        buy_colors = ['red', 'blue', 'green', 'purple']
        marker_size = 100
        
        for i, (rule_name, buy_signals) in enumerate(buy_signals_dict.items()):
            buy_markers = [date for date in buy_signals if date in recent_df.index]
            if buy_markers:
                buy_signal_data = pd.Series(np.nan, index=recent_df.index)
                # 根據規則名稱設置不同的垂直位置
                if rule_name == '三陽開泰':
                    y_position = recent_df.loc[buy_markers, 'Low'] * 0.99
                    buy_signal_data.loc[buy_markers] = y_position
                elif rule_name == '四海游龍':
                    y_position = recent_df.loc[buy_markers, 'Low'] * 0.97
                    buy_signal_data.loc[buy_markers] = y_position
                elif rule_name == '鑽石叉':
                    y_position = recent_df.loc[buy_markers, 'Low'] * 0.95
                    buy_signal_data.loc[buy_markers] = y_position
                elif rule_name != '轉折高點' and rule_name != '轉折低點':
                    y_position = recent_df.loc[buy_markers, 'Low'] * 0.99
                    buy_signal_data.loc[buy_markers] = y_position
                
                # 根據規則名稱設置不同的箭頭顏色和樣式
                if rule_name == '三陽開泰':
                    color = 'orange'
                    marker = '^'
                elif rule_name == '鑽石叉':
                    color = 'magenta'  # 洋紅色，突出顯示鑽石叉信號
                    marker = 'D'  # 鑽石形狀的標記
                elif rule_name == '轉折高點':
                    color = 'darkred'  # 深紅色，突出顯示轉折高點
                    marker = '*'  # 星形標記
                    y_position = recent_df.loc[buy_markers, 'High'] * 1.03  # 在高點上方顯示，距離更遠
                    buy_signal_data.loc[buy_markers] = y_position  # 更新數據點位置
                elif rule_name == '轉折低點':
                    color = 'darkgreen'  # 深綠色，突出顯示轉折低點
                    marker = '*'  # 星形標記
                    y_position = recent_df.loc[buy_markers, 'Low'] * 0.97  # 在低點下方顯示，距離更遠
                    buy_signal_data.loc[buy_markers] = y_position  # 更新數據點位置
                elif rule_name == '壓力線突破':
                    color = 'cyan'  # 青色，突出顯示壓力線突破
                    marker = 'o'  # 圓形標記
                    y_position = recent_df.loc[buy_markers, 'High'] * 1.02  # 在高點上方顯示
                    buy_signal_data.loc[buy_markers] = y_position  # 更新數據點位置
                else:
                    color = buy_colors[i % len(buy_colors)]
                    marker = '^'
                
                # 為轉折高點和轉折低點設置更大的標記尺寸
                if rule_name == '轉折高點' or rule_name == '轉折低點':
                    actual_marker_size = marker_size * 1.5  # 增加50%的尺寸
                else:
                    actual_marker_size = marker_size
                
                addplots.append(
                    mpf.make_addplot(buy_signal_data, type='scatter',
                                    marker=marker, markersize=actual_marker_size, color=color)
                )
    
    # Add sell signals
    if sell_signals is not None:
        sell_markers = [date for date in sell_signals if date in recent_df.index]
        if sell_markers:
            sell_signal_data = pd.Series(np.nan, index=recent_df.index)
            sell_signal_data.loc[sell_markers] = recent_df.loc[sell_markers, 'High'] * 1.01
            addplots.append(
                mpf.make_addplot(sell_signal_data, type='scatter',
                                marker='v', markersize=100, color='blue')
            )
    
    kwargs = {
        'type': 'candle',
        'style': s,
        'volume': True,
        'title': f'{stock_id} Daily K-Line Chart with Rule',
        'ylabel': '價格',
        'ylabel_lower': '成交量',
        'figsize': (15, 10),
        'addplot': addplots,
        'panel_ratios': tuple(panel_ratios_values)
    }
    
    # 保存圖表
    output_dir = 'output/chart'
    os.makedirs(output_dir, exist_ok=True)
    mpf.plot(recent_df, **kwargs, savefig=f'{output_dir}/{stock_id}_validation_chart.png')
    print(f"圖表已保存至 {output_dir}/{stock_id}_validation_chart.png")
    

def get_stock_list(file_path='config/stklist.cfg'):
    """從配置文件讀取股票代碼列表"""
    stock_list = []
    if not os.path.exists(file_path):
        print(f"找不到股票列表文件: {file_path}")
        return stock_list
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            next(f)  # 跳過標頭行
            for line in f:
                parts = line.strip().split(',')
                if parts:
                    stock_id = parts[0].strip()
                    if stock_id:
                        stock_list.append(stock_id)
    except Exception as e:
        print(f"讀取股票列表時發生錯誤: {e}")
    return stock_list

def validate_buy_rule(stock_id):
    print(f"正在驗證股票 {stock_id} 的買入規則...")
    
    # 載入數據
    df = load_stock_data(stock_id, 'D')
    if df is None:
        return
    
    print(f"成功載入數據，共 {len(df)} 筆記錄")
    print(f"數據欄位: {list(df.columns)}")
    
    # 调用 各种买入规则检查
    from .buyRule.breakthrough_san_yang_kai_tai import check_san_yang_kai_tai
    from .buyRule.breakthrough_four_seas_dragon import check_four_seas_dragon
    from .buyRule.macd_golden_cross_above_zero import check_macd_golden_cross_above_zero
    from .buyRule.macd_golden_cross_above_zero_positive_histogram import check_macd_golden_cross_above_zero_positive_histogram
    from .buyRule.diamond_cross import check_diamond_cross
    from .baseRule.turning_point_identification import check_turning_points
    from .buyRule.breakthrough_resistance_line import check_resistance_line_breakthrough
    san_yang_rule_df = check_san_yang_kai_tai(df)
    four_seas_dragon_rule_df = check_four_seas_dragon(df, [5, 10, 20, 60], stock_id)
    macd_rule_df = check_macd_golden_cross_above_zero(df)
    macd_positive_hist_rule_df = check_macd_golden_cross_above_zero_positive_histogram(df)
    diamond_cross_rule_df = check_diamond_cross(df)
    turning_points_rule_df = check_turning_points(df)

    # 將轉折點結果傳遞給鑽石叉規則，修改 check_diamond_cross 來接受 turning_points_df 參數
    diamond_cross_rule_df = check_diamond_cross(df, turning_points_rule_df)  # 假設我們修改了函數簽名

    # 添加壓力線突破規則
    resistance_breakthrough_df = check_resistance_line_breakthrough(df, turning_points_rule_df)

    # 合併規則結果
    rule_df = pd.merge(san_yang_rule_df, four_seas_dragon_rule_df, on='date', how='outer')
    rule_df = pd.merge(rule_df, macd_rule_df, on='date', how='outer')
    rule_df = pd.merge(rule_df, macd_positive_hist_rule_df, on='date', how='outer')
    rule_df = pd.merge(rule_df, diamond_cross_rule_df, on='date', how='outer')
    rule_df = pd.merge(rule_df, resistance_breakthrough_df, on='date', how='outer')
    
    # 保存基礎規則結果（轉折點識別）
    base_rule_dir = 'output/base_rule'
    os.makedirs(base_rule_dir, exist_ok=True)
    turning_points_rule_df.to_csv(f'{base_rule_dir}/{stock_id}_D_Rule.csv', index=False)
    print(f'已生成基礎規則文件: {base_rule_dir}/{stock_id}_D_Rule.csv')
    
    # 提取買入信號，並按規則名稱組織
    buy_signals_dict = {}
    
    # 處理三陽開泰規則
    san_yang_dates = []
    for i, row in rule_df.iterrows():
        if row['san_yang_kai_tai_check'] == 'O':
            date_obj = pd.to_datetime(row['date'])
            san_yang_dates.append(date_obj)
    buy_signals_dict['三陽開泰'] = san_yang_dates
    
    # 處理四海游龍規則
    four_seas_dates = []
    for i, row in rule_df.iterrows():
        if row.get('si_hai_you_long_check', '') == 'O':
            date_obj = pd.to_datetime(row['date'])
            four_seas_dates.append(date_obj)
    buy_signals_dict['四海游龍'] = four_seas_dates
    
    # 處理MACD黃金交叉零軸上規則
    macd_dates = []
    for i, row in rule_df.iterrows():
        if row.get('macd_golden_cross_above_zero_check', '') == 'O':
            date_obj = pd.to_datetime(row['date'])
            macd_dates.append(date_obj)
    buy_signals_dict['MACD黃金交叉零軸上'] = macd_dates

    # 處理MACD黃金交叉零軸上正柱規則
    macd_positive_hist_dates = []
    for i, row in rule_df.iterrows():
        if row.get('macd_golden_cross_above_zero_positive_histogram_check', '') == 'O':
            date_obj = pd.to_datetime(row['date'])
            macd_positive_hist_dates.append(date_obj)
    buy_signals_dict['MACD黃金交叉零軸上正柱'] = macd_positive_hist_dates
    
    # 先處理轉折點識別規則
    turning_high_dates = []
    turning_low_dates = []
    for i, row in turning_points_rule_df.iterrows():
        date_obj = pd.to_datetime(row['date'])
        if row.get('turning_high_point', '') == 'O':
            turning_high_dates.append(date_obj)
        if row.get('turning_low_point', '') == 'O':
            turning_low_dates.append(date_obj)
    buy_signals_dict['轉折高點'] = turning_high_dates
    buy_signals_dict['轉折低點'] = turning_low_dates
    
    # 處理鑽石叉規則
    diamond_cross_dates = []
    for i, row in rule_df.iterrows():
        if row.get('diamond_cross_check', '') == 'O':
            date_obj = pd.to_datetime(row['date'])
            diamond_cross_dates.append(date_obj)
    buy_signals_dict['鑽石叉'] = diamond_cross_dates

    # 處理壓力線突破規則
    resistance_breakthrough_dates = []
    for i, row in rule_df.iterrows():
        if row.get('resistance_line_breakthrough_check', '') == 'O':
            date_obj = pd.to_datetime(row['date'])
            resistance_breakthrough_dates.append(date_obj)
    buy_signals_dict['壓力線突破'] = resistance_breakthrough_dates

    plot_candlestick_chart(df, stock_id, buy_signals_dict)
    
    # 保存規則結果
    output_dir = 'output/buy_rules'
    os.makedirs(output_dir, exist_ok=True)
    rule_df.to_csv(f'{output_dir}/{stock_id}_D_Rule.csv', index=False)
    print(f'已生成規則文件: {output_dir}/{stock_id}_D_Rule.csv')

def debug_csv_structure(stock_id='2330', data_type='D'):
    """調試CSV文件結構"""
    file_path = f'Data/kbar/{stock_id}_{data_type}.csv'
    if not os.path.exists(file_path):
        print(f"找不到文件: {file_path}")
        return
    
    try:
        # 讀取前幾行來檢查結構
        df = pd.read_csv(file_path, nrows=5)
        print(f"CSV文件: {file_path}")
        print(f"欄位名稱: {list(df.columns)}")
        print(f"數據預覽:")
        print(df.head())
        print("-" * 50)
        
        # 嘗試以ts為索引讀取
        df_full = pd.read_csv(file_path, index_col='ts', parse_dates=True)
        print(f"以ts為索引後的欄位: {list(df_full.columns)}")
        print(f"總共 {len(df_full)} 筆記錄")
        
    except Exception as e:
        print(f"讀取文件時發生錯誤: {e}")

if __name__ == "__main__":
    # 設置中文字體支持
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS', 'SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 確保 output/chart 目錄存在
    output_dir = 'output/chart'
    os.makedirs(output_dir, exist_ok=True)
    
    validate_buy_rule('00894')
    # 獲取股票列表並逐一驗證
    stock_ids = get_stock_list()
    if not stock_ids:
        print("未找到任何股票代碼，請檢查 config/stklist.cfg 文件。")
    else:
        for stock_id in stock_ids:
            # 驗證買入規則
            validate_buy_rule(stock_id)
            # debug_csv_structure(stock_id) # 可以取消註釋用於調試
    