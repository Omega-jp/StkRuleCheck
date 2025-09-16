import pandas as pd
import numpy as np
from ..baseRule.turning_point_identification import identify_turning_points

def check_resistance_line_breakthrough(df: pd.DataFrame, turning_points_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    壓力線突破規則檢查函數
    
    偵測流程：
    1. 識別轉折高點
       - 使用 turning_point_identification 模塊標記的轉折高點
    2. 計算壓力線
       - 以當前K棒為基準，往前找最近兩個轉折高點
       - 利用兩點畫出壓力切線（阻力線）
    3. 突破檢測
       - 檢查當前收盤價是否向上穿越（CrossOver）壓力線
       - 前一日收盤價在壓力線下方，當日收盤價在壓力線上方
    
    Args:
        df (pd.DataFrame): 包含K線數據的DataFrame，需要包含 'Close', 'High', 'Low' 和 'ma5' 列。
        turning_points_df (pd.DataFrame, optional): 轉折點識別結果，如果未提供則自動計算
    
    Returns:
        pd.DataFrame: 包含 'date' 和 'resistance_line_breakthrough_check' 列的DataFrame，
                      'resistance_line_breakthrough_check' 為 'O' 表示滿足條件，'' 表示不滿足。
    """
    results = []
    
    # 如果未提供轉折點數據，則計算它
    if turning_points_df is None:
        # 確保有ma5欄位用於轉折點計算
        if 'ma5' not in df.columns:
            df['ma5'] = df['Close'].rolling(window=5, min_periods=1).mean()
        turning_points_df = identify_turning_points(df)
    
    # 將轉折點數據與原始數據合併
    df_reset = df.reset_index()
    date_col = df_reset.columns[0]  # 獲取重置索引後的第一列名稱（通常是日期列）
    df_with_turning_points = pd.merge(
        df_reset, 
        turning_points_df, 
        left_on=df_reset[date_col].dt.strftime('%Y-%m-%d'), 
        right_on='date', 
        how='left'
    )
    df_with_turning_points.set_index(date_col, inplace=True)
    
    # 獲取所有轉折高點的索引位置和對應的最高價
    turning_high_points = []
    for i, (idx, row) in enumerate(df_with_turning_points.iterrows()):
        if row.get('turning_high_point') == 'O':
            turning_high_points.append({
                'index': i,
                'date': idx,
                'high_price': df.loc[idx, 'High']
            })
    
    # 對每個日期進行檢查
    for i, (idx, row) in enumerate(df.iterrows()):
        date = idx.strftime('%Y-%m-%d')
        
        # 初始化為不滿足條件
        is_breakthrough = False
        
        # 需要至少兩個轉折高點才能畫壓力線
        if len(turning_high_points) < 2:
            results.append({'date': date, 'resistance_line_breakthrough_check': ''})
            continue
        
        # 找出當前日期之前的轉折高點
        previous_high_points = [
            hp for hp in turning_high_points 
            if hp['index'] < i  # 只考慮當前日期之前的轉折高點
        ]
        
        # 需要至少兩個之前的轉折高點
        if len(previous_high_points) < 2:
            results.append({'date': date, 'resistance_line_breakthrough_check': ''})
            continue
        
        # 取最近的兩個轉折高點
        recent_high_points = previous_high_points[-2:]
        
        # 獲取兩個高點的數據
        point1 = recent_high_points[0]
        point2 = recent_high_points[1]
        
        # 計算壓力線在當前日期的價格
        # 使用線性插值：y = y1 + (y2-y1) * (x-x1) / (x2-x1)
        x1, y1 = point1['index'], point1['high_price']
        x2, y2 = point2['index'], point2['high_price']
        
        # 避免除以零的情況
        if x2 == x1:
            results.append({'date': date, 'resistance_line_breakthrough_check': ''})
            continue
        
        # 計算當前日期在壓力線上的理論價格
        current_resistance_price = y1 + (y2 - y1) * (i - x1) / (x2 - x1)
        
        # 檢查是否為突破（CrossOver）
        current_close = row['Close']
        
        # 需要有前一日數據進行比較
        if i > 0:
            prev_row = df.iloc[i-1]
            prev_close = prev_row['Close']
            
            # 計算前一日的壓力線價格
            prev_resistance_price = y1 + (y2 - y1) * ((i-1) - x1) / (x2 - x1)
            
            # 突破條件：前一日收盤價在壓力線下方，當日收盤價在壓力線上方
            if (prev_close <= prev_resistance_price) and (current_close > current_resistance_price):
                is_breakthrough = True
        
        # 添加結果
        if is_breakthrough:
            results.append({'date': date, 'resistance_line_breakthrough_check': 'O'})
        else:
            results.append({'date': date, 'resistance_line_breakthrough_check': ''})
    
    return pd.DataFrame(results)


def get_resistance_line_data(df: pd.DataFrame, turning_points_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    獲取壓力線數據，用於繪圖或進一步分析
    
    Args:
        df (pd.DataFrame): 包含K線數據的DataFrame
        turning_points_df (pd.DataFrame, optional): 轉折點識別結果
    
    Returns:
        pd.DataFrame: 包含每日壓力線價格的DataFrame
    """
    # 如果未提供轉折點數據，則計算它
    if turning_points_df is None:
        if 'ma5' not in df.columns:
            df['ma5'] = df['Close'].rolling(window=5, min_periods=1).mean()
        turning_points_df = identify_turning_points(df)
    
    # 將轉折點數據與原始數據合併
    df_reset = df.reset_index()
    date_col = df_reset.columns[0]
    df_with_turning_points = pd.merge(
        df_reset, 
        turning_points_df, 
        left_on=df_reset[date_col].dt.strftime('%Y-%m-%d'), 
        right_on='date', 
        how='left'
    )
    df_with_turning_points.set_index(date_col, inplace=True)
    
    # 獲取所有轉折高點
    turning_high_points = []
    for i, (idx, row) in enumerate(df_with_turning_points.iterrows()):
        if row.get('turning_high_point') == 'O':
            turning_high_points.append({
                'index': i,
                'date': idx,
                'high_price': df.loc[idx, 'High']
            })
    
    # 計算每日的壓力線價格
    resistance_data = []
    for i, (idx, row) in enumerate(df.iterrows()):
        date = idx.strftime('%Y-%m-%d')
        
        # 找出當前日期之前的轉折高點
        previous_high_points = [
            hp for hp in turning_high_points 
            if hp['index'] < i
        ]
        
        if len(previous_high_points) >= 2:
            # 取最近的兩個轉折高點
            recent_high_points = previous_high_points[-2:]
            point1 = recent_high_points[0]
            point2 = recent_high_points[1]
            
            # 計算壓力線價格
            x1, y1 = point1['index'], point1['high_price']
            x2, y2 = point2['index'], point2['high_price']
            
            if x2 != x1:
                resistance_price = y1 + (y2 - y1) * (i - x1) / (x2 - x1)
                resistance_data.append({
                    'date': date,
                    'resistance_price': resistance_price,
                    'point1_date': point1['date'].strftime('%Y-%m-%d'),
                    'point1_price': point1['high_price'],
                    'point2_date': point2['date'].strftime('%Y-%m-%d'),
                    'point2_price': point2['high_price']
                })
            else:
                resistance_data.append({
                    'date': date,
                    'resistance_price': np.nan,
                    'point1_date': '',
                    'point1_price': np.nan,
                    'point2_date': '',
                    'point2_price': np.nan
                })
        else:
            resistance_data.append({
                'date': date,
                'resistance_price': np.nan,
                'point1_date': '',
                'point1_price': np.nan,
                'point2_date': '',
                'point2_price': np.nan
            })
    
    return pd.DataFrame(resistance_data)