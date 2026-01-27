import os
import re

import matplotlib.pyplot as plt # Keep for font settings
import mplfinance as mpf
import numpy as np
import pandas as pd

from src.data_initial.calculate_impulse_macd import calculate_impulse_macd
from src.data_initial.calculate_kd import calculate_kd
from src.data_initial.calculate_macd import calculate_macd
from src.data_initial.calculate_ma import calculate_ma
from src.data_initial.kbar_downloader import process_kbars
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def _base_name(col: str) -> str:
    """移除欄位尾端自動加的 .1/.2 後綴"""
    return re.sub(r"(?:\.\d+)+$", "", col)


def _dedup_columns(df: pd.DataFrame) -> pd.DataFrame:
    """以基礎名稱去重欄位，保留首次出現並扁平化名稱"""
    keep_indices = []
    new_cols = []
    seen = set()
    for idx, col in enumerate(df.columns):
        base = _base_name(col)
        if base in seen:
            continue
        seen.add(base)
        keep_indices.append(idx)
        new_cols.append(base)
    trimmed = df.iloc[:, keep_indices].copy()
    trimmed.columns = new_cols
    return trimmed


def _append_indicators_inline(df: pd.DataFrame) -> pd.DataFrame:
    """缺少指標時就地計算 KD/MACD/MA/Impulse MACD。"""
    if df.empty:
        return df

    base_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in base_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=base_cols)
    if df.empty:
        return df

    # 如果 ma5 已存在，視為已附加過主要指標，直接返回
    if 'ma5' in df.columns:
        return df

    kd_df = calculate_kd(df.copy())
    macd_df = calculate_macd(df.copy())
    ma_df = calculate_ma(df.copy())
    impulse_df = calculate_impulse_macd(df.copy())

    for col in ['RSV', '%K', '%D']:
        if col in kd_df.columns:
            kd_df[col] = kd_df[col].round(2)
    for col in ['MACD', 'Signal', 'Histogram']:
        if col in macd_df.columns:
            macd_df[col] = macd_df[col].round(2)
    for col in ma_df.columns:
        ma_df[col] = ma_df[col].round(2)
    for col in impulse_df.columns:
        impulse_df[col] = impulse_df[col].round(2)

    merged = pd.concat([df, kd_df, macd_df, ma_df, impulse_df], axis=1)
    # 去除重複欄位，保留首個出現的基礎欄位
    merged = _dedup_columns(merged)
    return merged


def _rebuild_from_raw(stock_id: str):
    """若 D/W 不存在且有 Raw，從 Raw 重建後回傳 (daily, weekly)。"""
    raw_path = f'Data/kbar/{stock_id}_Raw.csv'
    if not os.path.exists(raw_path):
        return None, None

    try:
        raw_df = pd.read_csv(raw_path, index_col='ts', parse_dates=True)
        column_mapping = {
            '開盤價': 'Open',
            '最高價': 'High',
            '最低價': 'Low',
            '收盤價': 'Close',
            '成交量': 'Volume',
        }
        if '收盤價' in raw_df.columns:
            raw_df.rename(columns=column_mapping, inplace=True)
        raw_df = raw_df[['Open', 'High', 'Low', 'Close', 'Volume']]
    except Exception as exc:
        print(f"  無法從 Raw 讀取 {stock_id}: {exc}")
        return None, None

    daily_k, weekly_k = process_kbars(raw_df)
    if daily_k is not None:
        daily_k.index.name = 'ts'
        daily_path = f'Data/kbar/{stock_id}_D.csv'
        daily_k.to_csv(daily_path)
        print(f"  已重建日線: {daily_path}")
    if weekly_k is not None:
        weekly_k.index.name = 'ts'
        weekly_path = f'Data/kbar/{stock_id}_W.csv'
        weekly_k.to_csv(weekly_path)
        print(f"  已重建週線: {weekly_path}")
    return daily_k, weekly_k


def load_stock_data(stock_id, data_type='D'):
    """載入股票數據；若 D/W 缺少且有 Raw，會先自動重建。"""
    file_path = f'Data/kbar/{stock_id}_{data_type}.csv'
    df = None

    if not os.path.exists(file_path):
        print(f"找不到文件: {file_path}")
        daily_k, weekly_k = _rebuild_from_raw(stock_id)
        if data_type == 'D':
            df = daily_k
        elif data_type == 'W':
            df = weekly_k
        if df is None:
            return None
    else:
        try:
            df = pd.read_csv(file_path, index_col='ts', parse_dates=True)
        except Exception as e:
            print(f"載入數據時發生錯誤: {e}")
            return None

    # 去除重複的尾碼欄位，保留首個並扁平化名稱
    df = _dedup_columns(df)

    # 檢查並統一欄位名稱
    column_mapping = {
        '開盤價': 'Open',
        '最高價': 'High',
        '最低價': 'Low',
        '收盤價': 'Close',
        '成交量': 'Volume'
    }

    if '收盤價' in df.columns:
        df.rename(columns=column_mapping, inplace=True)

    # 確保必要欄位存在
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"缺少必要欄位: {missing_cols}")
        print(f"現有欄位: {list(df.columns)}")
        return None

    df = _append_indicators_inline(df)
    return df

def plot_candlestick_chart(df, stock_id, buy_signals_dict=None, sell_signals=None, turning_points_df=None, wave_points_df=None):
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
                # �ھڳW�h�W�ٳ]�m���P��������m
                if rule_name == '三陽開泰':
                    y_position = recent_df.loc[buy_markers, 'Low'] * 0.99
                elif rule_name == '四海游龍':
                    y_position = recent_df.loc[buy_markers, 'Low'] * 0.97
                elif rule_name == '鑽石叉':
                    y_position = recent_df.loc[buy_markers, 'Low'] * 0.95
                elif rule_name == '轉折高點':
                    y_position = recent_df.loc[buy_markers, 'High'] * 1.02
                elif rule_name == '轉折低點':
                    y_position = recent_df.loc[buy_markers, 'Low'] * 0.98
                elif rule_name == '波段高點':
                    y_position = recent_df.loc[buy_markers, 'High'] * 1.04
                elif rule_name == '波段低點':
                    y_position = recent_df.loc[buy_markers, 'Low'] * 0.96
                elif rule_name == '壓力線突破':
                    y_position = recent_df.loc[buy_markers, 'High'] * 1.02
                else:
                    y_position = recent_df.loc[buy_markers, 'Low'] * 0.99
                buy_signal_data.loc[buy_markers] = y_position

                # �ھڳW�h�W�ٳ]�m���P���b�Y�C��M�˦�
                if rule_name == '三陽開泰':
                    color = 'orange'
                    marker = '^'
                elif rule_name == '四海游龍':
                    color = 'royalblue'
                    marker = '^'
                elif rule_name == '鑽石叉':
                    color = 'magenta'
                    marker = 'D'
                elif rule_name == '轉折高點':
                    color = 'crimson'
                    marker = '^'
                elif rule_name == '轉折低點':
                    color = 'forestgreen'
                    marker = 'v'
                elif rule_name == '波段高點':
                    color = 'darkred'
                    marker = '*'
                elif rule_name == '波段低點':
                    color = 'darkgreen'
                    marker = '*'
                elif rule_name == '壓力線突破':
                    color = 'cyan'
                    marker = 'o'
                else:
                    color = buy_colors[i % len(buy_colors)]
                    marker = '^'

                # 為轉折高點和轉折低點設置更大的標記尺寸
                if rule_name in {'轉折高點', '轉折低點'}:
                    actual_marker_size = marker_size * 1.2
                elif rule_name in {'波段高點', '波段低點'}:
                    actual_marker_size = marker_size * 1.8
                else:
                    actual_marker_size = marker_size

                addplots.append(
                    mpf.make_addplot(buy_signal_data, type='scatter',
                                    marker=marker, markersize=actual_marker_size, color=color)
                )

    
    # Draw polylines for turning and wave sequences on K chart
    def _enforce_alternating_points(raw_points):
        ordered = sorted(raw_points, key=lambda x: x[1])
        filtered = []
        for point_type, date, price in ordered:
            if not filtered:
                filtered.append((point_type, date, price))
                continue
            last_type, last_date, last_price = filtered[-1]
            if point_type == last_type:
                if point_type == 'high':
                    if price >= last_price:
                        filtered[-1] = (point_type, date, price)
                else:
                    if price <= last_price:
                        filtered[-1] = (point_type, date, price)
                continue
            filtered.append((point_type, date, price))
        return filtered

    def _build_sequence_series(source_df, high_flag, low_flag):
        if source_df is None or source_df.empty:
            return None
        temp_df = source_df.copy()
        temp_df['date'] = pd.to_datetime(temp_df['date'], errors='coerce')
        temp_df = temp_df.dropna(subset=['date'])
        temp_df = temp_df[temp_df['date'].isin(recent_df.index)]
        temp_df = temp_df.sort_values('date')

        raw_points = []
        for _, row in temp_df.iterrows():
            date = row['date']
            if row.get(high_flag) == 'O':
                raw_points.append(('high', date, recent_df.loc[date, 'High']))
            if row.get(low_flag) == 'O':
                raw_points.append(('low', date, recent_df.loc[date, 'Low']))

        filtered_points = _enforce_alternating_points(raw_points)
        if len(filtered_points) < 2:
            return None

        dates, values = zip(*[(date, price) for _, date, price in filtered_points])
        series = pd.Series(values, index=dates, dtype=float)
        # 需與 recent_df 長度一致,避免 mpf.plot 維度錯誤
        return series.reindex(recent_df.index)

    turning_sequence_series = _build_sequence_series(turning_points_df, 'turning_high_point', 'turning_low_point')
    if turning_sequence_series is not None:
        addplots.append(
            mpf.make_addplot(
                turning_sequence_series,
                type='line',
                color='dimgray',
                linestyle='--',
                width=1.0,
                alpha=0.7
            )
        )

    wave_sequence_series = None
    if wave_points_df is not None and not wave_points_df.empty:
        wave_points_aligned = wave_points_df.copy()
        wave_points_aligned['date'] = pd.to_datetime(
            wave_points_aligned['date'], errors='coerce'
        )
        wave_points_aligned = wave_points_aligned.dropna(subset=['date'])
        wave_points_aligned = wave_points_aligned[
            wave_points_aligned['date'].isin(recent_df.index)
        ].sort_values('date')

        wave_sequence_series = _build_sequence_series(
            wave_points_aligned, 'wave_high_point', 'wave_low_point'
        )
    else:
        wave_sequence_series = _build_sequence_series(
            wave_points_df, 'wave_high_point', 'wave_low_point'
        )

    if wave_sequence_series is not None:
        addplots.append(
            mpf.make_addplot(
                wave_sequence_series,
                type='line',
                color='darkred',
                linestyle='-',
                width=1.2,
                alpha=0.85
            )
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
    from .baseRule.wave_point_identification import check_wave_points
    from .buyRule.breakthrough_resistance_line import check_resistance_line_breakthrough
    from .buyRule.breakthrough_descending_trendline import check_descending_trendline
    from .buyRule.td_sequential_buy_rule import check_td_sequential_buy_rule
    san_yang_rule_df = check_san_yang_kai_tai(df)
    four_seas_dragon_rule_df = check_four_seas_dragon(df, [5, 10, 20, 60], stock_id)
    macd_rule_df = check_macd_golden_cross_above_zero(df)
    macd_positive_hist_rule_df = check_macd_golden_cross_above_zero_positive_histogram(df)
    diamond_cross_rule_df = check_diamond_cross(df)
    turning_points_rule_df = check_turning_points(df)

    # 準備波段高低點資料，將轉折點資訊合併後計算波段高低點
    df_for_wave_points = df.sort_index().copy()
    df_for_wave_points_reset = df_for_wave_points.reset_index()
    date_col_name = df_for_wave_points_reset.columns[0]
    df_for_wave_points_reset[date_col_name] = pd.to_datetime(
        df_for_wave_points_reset[date_col_name], errors='coerce'
    )

    turning_points_aligned = turning_points_rule_df.copy()
    turning_points_aligned['date'] = pd.to_datetime(
        turning_points_aligned['date'], errors='coerce'
    )

    df_with_turning_points = pd.merge(
        df_for_wave_points_reset,
        turning_points_aligned,
        left_on=date_col_name,
        right_on='date',
        how='left'
    )

    df_with_turning_points['turning_high_point'] = df_with_turning_points['turning_high_point'].fillna('')
    df_with_turning_points['turning_low_point'] = df_with_turning_points['turning_low_point'].fillna('')
    df_with_turning_points.set_index(date_col_name, inplace=True)

    wave_points_rule_df = check_wave_points(df_with_turning_points)

    # 將轉折點結果傳遞給鑽石叉規則，修改 check_diamond_cross 來接受 turning_points_df 參數
    diamond_cross_rule_df = check_diamond_cross(df, turning_points_rule_df)  # 假設我們修改了函數簽名

    # 添加壓力線突破規則
    resistance_breakthrough_df = check_resistance_line_breakthrough(df, turning_points_rule_df)
    descending_trendline_df = check_descending_trendline(
        df,
        turning_points_df=turning_points_rule_df,
        wave_points_df=wave_points_rule_df,
    )
    td_sequential_df = check_td_sequential_buy_rule(df)

    # 合併規則結果
    rule_df = pd.merge(san_yang_rule_df, four_seas_dragon_rule_df, on='date', how='outer')
    rule_df = pd.merge(rule_df, macd_rule_df, on='date', how='outer')
    rule_df = pd.merge(rule_df, macd_positive_hist_rule_df, on='date', how='outer')
    rule_df = pd.merge(rule_df, diamond_cross_rule_df, on='date', how='outer')
    rule_df = pd.merge(rule_df, resistance_breakthrough_df, on='date', how='outer')
    rule_df = pd.merge(rule_df, descending_trendline_df, on='date', how='outer')
    rule_df = pd.merge(rule_df, td_sequential_df, on='date', how='outer')

    wave_points_rule_df['date'] = pd.to_datetime(
        wave_points_rule_df['date'], errors='coerce'
    ).dt.strftime('%Y-%m-%d')
    rule_df = pd.merge(rule_df, wave_points_rule_df, on='date', how='outer')

    # 保存基礎規則結果（轉折點識別）
    base_rule_dir = 'output/base_rule'
    os.makedirs(base_rule_dir, exist_ok=True)
    turning_points_rule_df.to_csv(f'{base_rule_dir}/{stock_id}_D_Rule.csv', index=False)
    wave_points_rule_df.to_csv(f'{base_rule_dir}/{stock_id}_D_Wave.csv', index=False)
    print(f'已產出波段規則檔案: {base_rule_dir}/{stock_id}_D_Wave.csv')
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

    descending_breakthrough_dates = []
    for _, row in rule_df.iterrows():
        if row.get('descending_trendline_breakthrough_check', '') == 'O':
            date_obj = pd.to_datetime(row['date'])
            descending_breakthrough_dates.append(date_obj)
    buy_signals_dict['下降趨勢線突破'] = descending_breakthrough_dates
    
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
    
    wave_high_dates = []
    wave_low_dates = []
    for _, row in wave_points_rule_df.iterrows():
        date_value = row.get('date')
        if pd.isna(date_value):
            continue
        date_obj = pd.to_datetime(date_value)
        if pd.isna(date_obj):
            continue
        if row.get('wave_high_point', '') == 'O':
            wave_high_dates.append(date_obj)
        if row.get('wave_low_point', '') == 'O':
            wave_low_dates.append(date_obj)
    buy_signals_dict['波段高點'] = wave_high_dates
    buy_signals_dict['波段低點'] = wave_low_dates
    
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

    td_buy_dates = []
    for _, row in rule_df.iterrows():
        if row.get('td_sequential_buy_check', '') == 'O':
            date_obj = pd.to_datetime(row['date'])
            td_buy_dates.append(date_obj)
    buy_signals_dict['TD 九轉買訊'] = td_buy_dates


    plot_candlestick_chart(
        df,
        stock_id,
        buy_signals_dict,
        turning_points_df=turning_points_rule_df,
        wave_points_df=wave_points_rule_df
    )
    
    # 保存規則結果
    output_dir = 'output/buy_rules'
    os.makedirs(output_dir, exist_ok=True)
    rule_df.to_csv(f'{output_dir}/{stock_id}_D_Rule.csv', index=False)
    print(f'已生成規則文件: {output_dir}/{stock_id}_D_Rule.csv')

def debug_csv_structure(stock_id='00631L', data_type='D'):
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
    


