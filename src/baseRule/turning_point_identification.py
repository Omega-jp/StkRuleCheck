import pandas as pd
import numpy as np

def identify_turning_points(df: pd.DataFrame, window_size: int = 5) -> pd.DataFrame:
    """
    識別股價的轉折高點和轉折低點。
    
    Args:
        df (pd.DataFrame): 包含K線數據的DataFrame，需要包含 'Close', 'High', 'Low' 和 'ma5' 列。
        window_size (int): 局部極值窗口大小，預設為5。
    
    Returns:
        pd.DataFrame: 包含 'date', 'turning_high_point', 和 'turning_low_point' 列的DataFrame。
        轉折高點基於K棒的最高價(High)，轉折低點基於K棒的最低價(Low)。
    """
    results = []
    # 記錄上一次穿越的方向和時間
    last_cross_up_idx = None  # 上次向上穿越的索引
    last_cross_down_idx = None  # 上次向下穿越的索引
    
    # 遍歷每個K線位置
    for i, (idx, row) in enumerate(df.iterrows()):
        date = idx.strftime('%Y-%m-%d')
        
        # 初始化結果
        turning_high_point = ''
        turning_low_point = ''
        
        # 🔧 修正1: 放寬邊界條件 - 移除末尾的邊界限制，允許處理接近末尾的穿越
        # 原始代碼：if i < window_size or i >= len(df) - window_size or 'ma5' not in df.columns or pd.isna(row['ma5']):
        # 修正為：只檢查開頭邊界和必要的數據完整性
        if i < 1 or 'ma5' not in df.columns or pd.isna(row['ma5']):  # 只需要前一天數據即可
            results.append({
                'date': date,
                'turning_high_point': turning_high_point,
                'turning_low_point': turning_low_point
            })
            continue
        
        # 獲取前一天的數據
        prev_row = df.iloc[i - 1]
        if pd.isna(prev_row['ma5']):
            results.append({
                'date': date,
                'turning_high_point': turning_high_point,
                'turning_low_point': turning_low_point
            })
            continue
        
        # 🔧 修正2: 移除不必要的局部高低點檢查（原始算法中沒有使用）
        # 原始代碼中計算了 is_local_high 和 is_local_low 但實際沒有使用，所以移除
        
        # 檢查MA穿越類型
        current_close = row['Close']
        current_ma5 = row['ma5']
        prev_close = prev_row['Close']
        prev_ma5 = prev_row['ma5']
        
        # 向上穿越: 收盤價由下向上穿越5MA
        cross_up = (current_close > current_ma5) and (prev_close <= prev_ma5)
        
        # 向下穿越: 收盤價由上向下穿越5MA
        cross_down = (current_close < current_ma5) and (prev_close >= prev_ma5)
        
        # 如果發生向上穿越
        if cross_up:
            # 記錄當前向上穿越的位置
            last_cross_up_idx = i
            
            # 如果之前有向下穿越記錄，尋找這段期間的最低點
            if last_cross_down_idx is not None:
                # 獲取上次向下穿越到當前向上穿越之間的數據
                period_data = df.iloc[last_cross_down_idx:i+1]
                
                # 找出這段期間的最低價及其索引
                min_low_idx = period_data['Low'].idxmin()
                min_low_date = min_low_idx.strftime('%Y-%m-%d')
                
                # 在最低點的日期標記轉折低點
                for j, result in enumerate(results):
                    if result['date'] == min_low_date:
                        results[j]['turning_low_point'] = 'O'
                        break
        
        # 如果發生向下穿越
        if cross_down:
            # 記錄當前向下穿越的位置
            last_cross_down_idx = i
            
            # 如果之前有向上穿越記錄，尋找這段期間的最高點
            if last_cross_up_idx is not None:
                # 獲取上次向上穿越到當前向下穿越之間的數據
                period_data = df.iloc[last_cross_up_idx:i+1]
                
                # 找出這段期間的最高價及其索引
                max_high_idx = period_data['High'].idxmax()
                max_high_date = max_high_idx.strftime('%Y-%m-%d')
                
                # 在最高點的日期標記轉折高點
                for j, result in enumerate(results):
                    if result['date'] == max_high_date:
                        results[j]['turning_high_point'] = 'O'
                        break
        
        # 添加當前日期的結果
        results.append({
            'date': date,
            'turning_high_point': turning_high_point,
            'turning_low_point': turning_low_point
        })
    
    # 🔧 修正3: 處理最後一個未完成的穿越事件
    # 在循環結束後，檢查是否有未處理的穿越事件需要回溯處理
    
    # 如果最後一個事件是向上穿越，且之前有向下穿越，需要處理最低點
    if last_cross_up_idx is not None and last_cross_down_idx is not None and last_cross_up_idx > last_cross_down_idx:
        # 這意味著最後一次是向上穿越，但可能沒有後續的向下穿越來觸發回溯
        # 檢查是否已經處理過這個區間的最低點
        period_data = df.iloc[last_cross_down_idx:last_cross_up_idx+1]
        min_low_idx = period_data['Low'].idxmin()
        min_low_date = min_low_idx.strftime('%Y-%m-%d')
        
        # 檢查這個最低點是否已經被標記
        already_marked = False
        for result in results:
            if result['date'] == min_low_date and result['turning_low_point'] == 'O':
                already_marked = True
                break
        
        # 如果沒有被標記，現在標記它
        if not already_marked:
            for j, result in enumerate(results):
                if result['date'] == min_low_date:
                    results[j]['turning_low_point'] = 'O'
                    break
    
    # 如果最後一個事件是向下穿越，且之前有向上穿越，需要處理最高點
    if last_cross_down_idx is not None and last_cross_up_idx is not None and last_cross_down_idx > last_cross_up_idx:
        # 這意味著最後一次是向下穿越，但可能沒有後續的向上穿越來觸發回溯
        period_data = df.iloc[last_cross_up_idx:last_cross_down_idx+1]
        max_high_idx = period_data['High'].idxmax()
        max_high_date = max_high_idx.strftime('%Y-%m-%d')
        
        # 檢查這個最高點是否已經被標記
        already_marked = False
        for result in results:
            if result['date'] == max_high_date and result['turning_high_point'] == 'O':
                already_marked = True
                break
        
        # 如果沒有被標記，現在標記它
        if not already_marked:
            for j, result in enumerate(results):
                if result['date'] == max_high_date:
                    results[j]['turning_high_point'] = 'O'
                    break
    
    return pd.DataFrame(results)


def check_turning_points(df: pd.DataFrame, window_size: int = 5) -> pd.DataFrame:
    """
    檢查股價的轉折高點和轉折低點。
    
    Args:
        df (pd.DataFrame): 包含K線數據的DataFrame，需要包含 'Close', 'High', 'Low' 和 'ma5' 列。
        window_size (int): 局部極值窗口大小，預設為5。
    
    Returns:
        pd.DataFrame: 包含 'date', 'turning_high_point', 和 'turning_low_point' 列的DataFrame。
        轉折高點基於K棒的最高價(High)，轉折低點基於K棒的最低價(Low)。
    """
    return identify_turning_points(df, window_size)


if __name__ == "__main__":
    # 測試用例
    import matplotlib.pyplot as plt
    
    # 創建測試數據
    dates = pd.date_range(start='2023-01-01', periods=100)
    close_prices = [100]
    high_prices = [102]
    low_prices = [98]
    for i in range(1, 100):
        # 生成一些波動的價格
        close_change = np.random.normal(0, 2)
        close_prices.append(close_prices[-1] + close_change)
        high_prices.append(close_prices[-1] + abs(np.random.normal(1, 1)))
        low_prices.append(close_prices[-1] - abs(np.random.normal(1, 1)))
    
    # 創建DataFrame
    test_df = pd.DataFrame({
        'Close': close_prices,
        'High': high_prices,
        'Low': low_prices
    }, index=dates)
    
    # 計算5日移動平均線
    test_df['ma5'] = test_df['Close'].rolling(window=5, min_periods=1).mean()
    
    # 識別轉折點
    turning_points = check_turning_points(test_df)
    
    # 合併結果
    result_df = pd.merge(test_df.reset_index(), turning_points, left_on='index', right_on='date', how='left')
    
    # 繪製圖表
    plt.figure(figsize=(15, 8))
    plt.plot(result_df['index'], result_df['Close'], label='Close Price')
    plt.plot(result_df['index'], result_df['ma5'], label='5-day MA')
    
    # 標記轉折高點
    high_points = result_df[result_df['turning_high_point'] == 'O']
    plt.scatter(high_points['index'], high_points['High'], color='red', marker='^', s=100, label='Turning High Points')
    
    # 標記轉折低點
    low_points = result_df[result_df['turning_low_point'] == 'O']
    plt.scatter(low_points['index'], low_points['Low'], color='green', marker='v', s=100, label='Turning Low Points')
    
    plt.title('Price with Turning Points')
    plt.legend()
    plt.grid(True)
    plt.show()