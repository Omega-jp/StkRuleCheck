import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from datetime import datetime, timedelta
import os
import mplfinance as mpf

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] # 或其他支持中文的字體
plt.rcParams['axes.unicode_minus'] = False # 解決負號顯示問題

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

def plot_candlestick_chart(df, stock_id, buy_signals=None, sell_signals=None):
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
        wick='black',
        volume='inherit'
    )
    s = mpf.make_mpf_style(marketcolors=mc)
    
    # 準備買入和賣出信號的標記
    signals_plot = []
    
    # 添加移動平均線
    for ma in ['ma5', 'ma10', 'ma20']:
        if ma in recent_df.columns:
            signals_plot.append(
                mpf.make_addplot(recent_df[ma], type='line', width=1)
            )
    
    # 添加買入信號
    if buy_signals is not None:
        buy_markers = [date for date in buy_signals if date in recent_df.index]
        if buy_markers:
            buy_signal_data = pd.Series(np.nan, index=recent_df.index)
            buy_signal_data.loc[buy_markers] = recent_df.loc[buy_markers, 'Low'] * 0.99
            signals_plot.append(
                mpf.make_addplot(buy_signal_data, type='scatter',
                                marker='^', markersize=100, color='red')
            )
    
    # 添加賣出信號
    if sell_signals is not None:
        sell_markers = [date for date in sell_signals if date in recent_df.index]
        if sell_markers:
            sell_signal_data = pd.Series(np.nan, index=recent_df.index)
            sell_signal_data.loc[sell_markers] = recent_df.loc[sell_markers, 'High'] * 1.01
            signals_plot.append(
                mpf.make_addplot(sell_signal_data, type='scatter',
                                marker='v', markersize=100, color='blue')
            )
    
    # 添加均線和信號
    kwargs = {
        'type': 'candle',
        'style': s,
        'volume': True,
        'title': f'{stock_id} Daily K-Line Chart with Rule',
        'ylabel': '價格',
        'ylabel_lower': '成交量',
        'figsize': (15, 10),
        'addplot': signals_plot
    }
    
    # 保存圖表
    output_dir = 'output/chart'
    os.makedirs(output_dir, exist_ok=True)
    mpf.plot(recent_df, **kwargs, savefig=f'{output_dir}/{stock_id}_validation_chart.png')
    print(f"圖表已保存至 {output_dir}/{stock_id}_validation_chart.png")
    
    # 繪製移動平均線
    plot_moving_averages(ax1, recent_df)
    
    # 繪製買賣信號
    if buy_signals is not None:
        plot_signals(ax1, recent_df, buy_signals, 'buy')
    if sell_signals is not None:
        plot_signals(ax1, recent_df, sell_signals, 'sell')
    
    # 繪製成交量
    plot_volume(ax2, recent_df)
    
    # 設置圖表格式
    format_chart(ax1, ax2, stock_id, recent_df.index)
    
    plt.tight_layout()
    plt.savefig(f'output/chart/{stock_id}_validation_chart.png')
    plt.close(fig) # Close the figure to free memory

def plot_candlesticks(ax, df):
    """繪製K線"""
    # 確保數據列存在
    required_cols = ['Open', 'High', 'Low', 'Close']
    if not all(col in df.columns for col in required_cols):
        print("缺少必要的OHLC數據列")
        return
    
    # 使用數值索引作為X軸
    x_indices = np.arange(len(df))
    
    # 使用numpy數組提高效率
    opens = df['Open'].values
    highs = df['High'].values
    lows = df['Low'].values
    closes = df['Close'].values
    
    # 計算K棒寬度
    if len(x_indices) > 1:
        width = min(0.6, (x_indices[1] - x_indices[0]) * 0.8)
    else:
        width = 0.6
    
    for i, x_idx in enumerate(x_indices):
        open_price = opens[i]
        high_price = highs[i]
        low_price = lows[i]
        close_price = closes[i]
        
        # 跳過無效數據
        if pd.isna(open_price) or pd.isna(high_price) or pd.isna(low_price) or pd.isna(close_price):
            continue
        
        # 設置顏色
        color = 'red' if close_price >= open_price else 'green'
        
        # 先繪製實體
        height = abs(close_price - open_price)
        bottom = min(open_price, close_price)
        
        # 如果開盤價等於收盤價，設置最小高度
        if height == 0:
            height = (high_price - low_price) * 0.01
        
        rect = Rectangle((x_idx - width/2, bottom), width, height,
                        facecolor=color, alpha=0.8, linewidth=0)
        ax.add_patch(rect)
        
        # 後繪製影線
        ax.plot([x_idx, x_idx], [low_price, high_price],
                color='black', linewidth=2, alpha=1.0)

def plot_moving_averages(ax, df):
    """繪製移動平均線"""
    x_indices = np.arange(len(df))
    if 'ma5' in df.columns:
        ax.plot(x_indices, df['ma5'], label='MA5', color='blue', linewidth=1)
    if 'ma10' in df.columns:
        ax.plot(x_indices, df['ma10'], label='MA10', color='orange', linewidth=1)
    if 'ma20' in df.columns:
        ax.plot(x_indices, df['ma20'], label='MA20', color='purple', linewidth=1)

def plot_signals(ax, df, signals, signal_type):
    """繪製買賣信號"""
    if signals is None or len(signals) == 0:
        return
    
    color = 'red' if signal_type == 'buy' else 'blue'
    marker = '^' if signal_type == 'buy' else 'v'
    label = '買入信號' if signal_type == 'buy' else '賣出信號'
    
    # 確保使用正確的欄位名稱
    close_col = 'Close' if 'Close' in df.columns else '收盤價'
    
    # Create a mapping from date to numerical index
    date_to_idx = {date: i for i, date in enumerate(df.index)}

    for signal_date in signals:
        if signal_date in df.index:
            x_idx = date_to_idx[signal_date]
            price = df.loc[signal_date, close_col]
            ax.scatter(x_idx, price, color=color, marker=marker,
                      s=100, label=label, zorder=5)

def plot_volume(ax, df):
    """繪製成交量"""
    # 確保使用正確的欄位名稱
    volume_col = 'Volume' if 'Volume' in df.columns else '成交量'
    close_col = 'Close' if 'Close' in df.columns else '收盤價'
    open_col = 'Open' if 'Open' in df.columns else '開盤價'
    
    # 清理成交量數據
    volume_data = df[volume_col].fillna(0)
    
    # 根據漲跌設置顏色
    colors = ['red' if close > open else 'green' 
              for close, open in zip(df[close_col], df[open_col])]
    
    x_indices = np.arange(len(df))
    # 繪製成交量柱狀圖
    ax.bar(x_indices, volume_data, color=colors, alpha=0.7, width=0.8)
    
    # 設置成交量軸
    ax.set_ylabel('成交量')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K'))

def format_chart(ax1, ax2, stock_id, dates):
    """格式化圖表"""
    # 設置主圖表
    ax1.set_title(f'{stock_id} Daily K-Line Chart with Rule', fontsize=16, fontweight='bold')
    ax1.set_ylabel('價格')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # 設置x軸格式
    num_days = len(dates)
    if num_days > 0:
        # Determine appropriate interval for ticks
        if num_days > 180: # More than 6 months, show monthly
            tick_interval = 30
        elif num_days > 90: # 3-6 months, show every 2 weeks
            tick_interval = 14
        else: # Less than 3 months, show weekly
            tick_interval = 7

        # Get indices for ticks
        tick_indices = np.arange(0, num_days, tick_interval)
        if num_days - 1 not in tick_indices: # Ensure last date is included
            tick_indices = np.append(tick_indices, num_days - 1)

        # Get corresponding dates for labels
        tick_labels = [dates[i].strftime('%Y-%m-%d') for i in tick_indices]

        ax1.set_xticks(tick_indices)
        ax2.set_xticks(tick_indices)
        ax2.set_xticklabels(tick_labels) # Only set for the bottom chart
    
    # 旋轉日期標籤
    ax1.tick_params(axis='x', rotation=45)
    ax2.tick_params(axis='x', rotation=45)
    
    # 隱藏上方圖表的x軸標籤
    ax1.set_xticklabels([])
    
    # 設置成交量圖表
    ax2.set_xlabel('日期')
    ax2.grid(True, alpha=0.3)

def get_stock_list(file_path='config/stklist.cfg'):
    """從配置文件讀取股票代碼列表"""
    stock_list = []
    if not os.path.exists(file_path):
        print(f"找不到股票列表文件: {file_path}")
        return stock_list
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                stock_id = line.strip()
                if stock_id:
                    stock_list.append(stock_id)
    except Exception as e:
        print(f"讀取股票列表時發生錯誤: {e}")
    return stock_list

def validate_buy_rule(stock_id):
    """驗證買入規則的主函數"""
    print(f"正在驗證股票 {stock_id} 的買入規則...")
    
    # 載入數據
    df = load_stock_data(stock_id, 'D')
    if df is None:
        return
    
    print(f"成功載入數據，共 {len(df)} 筆記錄")
    print(f"數據欄位: {list(df.columns)}")
    
    # 這裡可以添加您的買入規則邏輯
    # 例如：簡單的移動平均交叉策略
    buy_signals = []
    sell_signals = []
    
    if 'ma5' in df.columns and 'ma10' in df.columns:
        print("找到移動平均線數據，計算交叉信號...")
        for i in range(1, len(df)):
            # 買入信號：MA5從下方穿越MA10
            if (df.iloc[i]['ma5'] > df.iloc[i]['ma10'] and
                df.iloc[i-1]['ma5'] <= df.iloc[i-1]['ma10']):
                buy_signals.append(df.index[i])
            
            # 賣出信號：MA5從上方穿越MA10
            if (df.iloc[i]['ma5'] < df.iloc[i]['ma10'] and
                df.iloc[i-1]['ma5'] >= df.iloc[i-1]['ma10']):
                sell_signals.append(df.index[i])
    else:
        print("未找到移動平均線數據，跳過信號計算")
    
    # 繪製圖表
    plot_candlestick_chart(df, stock_id, buy_signals, sell_signals)
    
    print(f"找到 {len(buy_signals)} 個買入信號")
    print(f"找到 {len(sell_signals)} 個賣出信號")
    # 保存規則結果
    from src.buyRule.breakthrough_ma import combine_buy_rules
    rule_df = combine_buy_rules(df, [5,10,20,60])
    output_dir = 'output/breakthrought_ma'
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
    
    # 獲取股票列表並逐一驗證
    stock_ids = get_stock_list()
    if not stock_ids:
        print("未找到任何股票代碼，請檢查 config/stklist.cfg 文件。")
    else:
        for stock_id in stock_ids:
            # 驗證買入規則
            validate_buy_rule(stock_id)
            # debug_csv_structure(stock_id) # 可以取消註釋用於調試
    