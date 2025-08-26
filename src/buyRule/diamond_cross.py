import pandas as pd
import numpy as np
from ..baseRule.turning_point_identification import identify_turning_points

def check_diamond_cross(df: pd.DataFrame, turning_points_df: pd.DataFrame = None) -> pd.DataFrame:
    if turning_points_df is None:
        turning_points_df = identify_turning_points(df)  # 如果未提供，則計算
    """
    鑽石叉規則檢查函數
    
    偵測流程：
    1. 基礎條件檢查
       - 確認黃金交叉：檢查20日均線（月線）是否已向上穿越60日均線（季線）
       - 記錄黃金交叉發生的確切日期
    2. 識別關鍵高點
       - 找出黃金交叉「之前」的最近一個重要波段高點
       - 使用 turning_point_identification 模塊標記的轉折高點作為波段高點
       - 忽略黃金交叉後形成的任何高點
    3. 鑽石交叉確認
       - 突破判定：檢查當前股價是否突破步驟2識別的前波高點
       - 突破必須是收盤價基礎，不看盤中高點
    
    Args:
        df (pd.DataFrame): 包含K線數據的DataFrame，需要包含 'Close', 'High', 'Low' 和均線列 'ma5', 'ma20', 'ma60'。
    
    Returns:
        pd.DataFrame: 包含 'date' 和 'diamond_cross_check' 列的DataFrame，
                      'diamond_cross_check' 為 'O' 表示滿足條件，'' 表示不滿足。
    """
    results = []
    golden_cross_dates = []
    
    # 首先識別轉折點
    if 'ma5' not in df.columns:
        # 如果沒有ma5，計算它
        df['ma5'] = df['Close'].rolling(window=5, min_periods=1).mean()
    
    # 獲取轉折點數據
    turning_points_df = identify_turning_points(df)
    
    # 將轉折點數據與原始數據合併
    df_reset = df.reset_index()
    date_col = df_reset.columns[0]  # 获取重置索引后的第一列名称（通常是日期列）
    df_with_turning_points = pd.merge(df_reset, turning_points_df, left_on=df_reset[date_col].dt.strftime('%Y-%m-%d'), right_on='date', how='left')
    df_with_turning_points.set_index(date_col, inplace=True)
    
    # 步驟1: 找出所有黃金交叉點（20MA上穿60MA）
    for i in range(1, len(df)):
        current_row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        # 確保均線數據存在
        if 'ma20' not in df.columns or 'ma60' not in df.columns or \
           pd.isna(current_row['ma20']) or pd.isna(current_row['ma60']) or \
           pd.isna(prev_row['ma20']) or pd.isna(prev_row['ma60']):
            continue
        
        # 檢查黃金交叉：20MA上穿60MA
        if (current_row['ma20'] > current_row['ma60']) and (prev_row['ma20'] <= prev_row['ma60']):
            golden_cross_dates.append(i)  # 記錄黃金交叉的索引位置
    
    # 對每個日期進行檢查
    for i, (idx, row) in enumerate(df.iterrows()):
        date = idx.strftime('%Y-%m-%d')
        
        # 初始化為不滿足條件
        is_diamond_cross = False
        
        # 檢查當前日期是否在任何黃金交叉之後
        for gc_idx in golden_cross_dates:
            if i <= gc_idx:  # 當前日期在黃金交叉之前或就是黃金交叉日，跳過
                continue
                
            # 步驟2: 找出黃金交叉前的轉折高點
            lookback_start = max(0, gc_idx - 60)  # 向前看60天，但不超過數據起始
            
            # 獲取黃金交叉前的數據切片
            lookback_slice = df_with_turning_points.iloc[lookback_start:gc_idx]
            
            # 找出這段時間內的轉折高點
            high_points = lookback_slice[lookback_slice['turning_high_point'] == 'O']
            
            if len(high_points) == 0:
                continue
                
            # 獲取最近的轉折高點對應的收盤價
            latest_high_point = high_points.iloc[-1]
            high_point_date = latest_high_point.name
            high_point_price = df.loc[high_point_date, 'High']
            
            # 步驟3: 檢查當前收盤價是否突破前波高點
            if i > 0:
                prev_row = df.iloc[i-1]
                prev_close = prev_row['Close']
                if row['Close'] > high_point_price and prev_close <= high_point_price:
                    is_diamond_cross = True
                    break  # 一旦找到符合條件的情況，就不需要繼續檢查其他黃金交叉
        
        # 添加結果
        if is_diamond_cross:
            results.append({'date': date, 'diamond_cross_check': 'O'})
        else:
            results.append({'date': date, 'diamond_cross_check': ''})
    
    return pd.DataFrame(results)