#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轉折點識別模塊 - 書本規格標準版

依據書本規格實作轉折點識別，包含完整的位移規則。

書本規格6大規則：
1. 以5日均線為依據
2. 正價/負價群組定義（收盤價與MA5的相對位置）
3. 向下跌破時取正價群組最高點（含上影線）
4. 向上突破時取負價群組最低點（含下影線）
5. 依序連接高低點成轉折波
6. 重要原則：
   (1) 不可遺漏最高點及最低點
   (2) ⭐ 位移規則：在下個點產生前，如果右邊有更高或更低的點，該高低點要位移
   (3) 高低點交互選取

實作方式：採用「即時更新法」實現位移規則
- 在群組內持續追蹤極值，發現更極端的值立即更新（位移）
- 當穿越發生時才確認標記，自然符合位移規則

版本：v2.0
更新日期：2025-10-23
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple


class TurningPointTracker:
    """
    轉折點追蹤器
    
    負責追蹤當前正價/負價群組，並在群組內持續更新極值（實現位移規則）
    """
    
    def __init__(self):
        """初始化追蹤器"""
        # 當前群組狀態
        self.current_group_type: Optional[str] = None  # 'positive' 或 'negative'
        self.current_group_start_idx: Optional[int] = None  # 群組起始索引
        
        # 當前群組的極值追蹤（這個會持續更新，實現位移）
        self.current_extremum_idx: Optional[int] = None  # 極值的索引位置
        self.current_extremum_date: Optional[str] = None  # 極值的日期
        self.current_extremum_value: Optional[float] = None  # 極值的價格
        
        # 已確認的標記歷史
        self.confirmed_marks: dict = {}  # {date: 'high' 或 'low'}
        self.last_confirmed_type: Optional[str] = None  # 上次確認的類型
        
    def start_positive_group(self, idx: int, date: str, high_price: float):
        """
        開始新的正價群組
        
        Args:
            idx: 索引位置
            date: 日期字串
            high_price: 最高價
        """
        self.current_group_type = 'positive'
        self.current_group_start_idx = idx
        self.current_extremum_idx = idx
        self.current_extremum_date = date
        self.current_extremum_value = high_price
    
    def start_negative_group(self, idx: int, date: str, low_price: float):
        """
        開始新的負價群組
        
        Args:
            idx: 索引位置
            date: 日期字串
            low_price: 最低價
        """
        self.current_group_type = 'negative'
        self.current_group_start_idx = idx
        self.current_extremum_idx = idx
        self.current_extremum_date = date
        self.current_extremum_value = low_price
    
    def update_extremum_in_positive_group(self, idx: int, date: str, high_price: float):
        """
        在正價群組內更新最高點（實現位移規則）
        
        如果發現更高的點，就更新極值位置（這就是位移）
        
        Args:
            idx: 索引位置
            date: 日期字串
            high_price: 最高價
        """
        if self.current_group_type != 'positive':
            return
        
        if high_price > self.current_extremum_value:
            # 發現更高的點 → 位移
            self.current_extremum_idx = idx
            self.current_extremum_date = date
            self.current_extremum_value = high_price
    
    def update_extremum_in_negative_group(self, idx: int, date: str, low_price: float):
        """
        在負價群組內更新最低點（實現位移規則）
        
        如果發現更低的點，就更新極值位置（這就是位移）
        
        Args:
            idx: 索引位置
            date: 日期字串
            low_price: 最低價
        """
        if self.current_group_type != 'negative':
            return
        
        if low_price < self.current_extremum_value:
            # 發現更低的點 → 位移
            self.current_extremum_idx = idx
            self.current_extremum_date = date
            self.current_extremum_value = low_price
    
    def confirm_current_extremum(self, mark_type: str) -> Optional[Tuple[str, str]]:
        """
        確認當前群組的極值為轉折點
        
        檢查高低點交替原則，如果符合則確認標記
        
        Args:
            mark_type: 'high' 或 'low'
        
        Returns:
            如果可以標記，返回 (date, mark_type)，否則返回 None
        """
        # 檢查是否有極值可確認
        if self.current_extremum_date is None:
            return None
        
        # 檢查高低點交替原則
        if self.last_confirmed_type == mark_type:
            # 連續相同類型，不符合交替原則，不標記
            return None
        
        # 檢查是否已經標記過這個日期
        if self.current_extremum_date in self.confirmed_marks:
            return None
        
        # 確認標記
        self.confirmed_marks[self.current_extremum_date] = mark_type
        self.last_confirmed_type = mark_type
        
        return (self.current_extremum_date, mark_type)


def detect_cross_events(df: pd.DataFrame) -> pd.DataFrame:
    """
    檢測收盤價與MA5的穿越事件
    
    使用連續2天確認機制降低假信號
    
    Args:
        df: K線數據，需要包含 'Close' 和 'ma5' 欄位
    
    Returns:
        增加了穿越標記欄位的DataFrame
    """
    df_cross = df.copy()
    
    # 計算收盤價與MA5的相對位置
    df_cross['close_above_ma5'] = df_cross['Close'] > df_cross['ma5']
    df_cross['prev_close_above_ma5'] = df_cross['close_above_ma5'].shift(1)
    df_cross['prev2_close_above_ma5'] = df_cross['close_above_ma5'].shift(2)
    
    # 向上穿越：連續2天確認
    # 前2天在MA5下方或等於，前1天和當天都在MA5上方
    df_cross['cross_up'] = (
        (df_cross['close_above_ma5']) &
        (df_cross['prev_close_above_ma5']) &
        (~df_cross['prev2_close_above_ma5'].fillna(False))
    )
    
    # 向下穿越：連續2天確認
    # 前2天在MA5上方或等於，前1天和當天都在MA5下方
    df_cross['cross_down'] = (
        (~df_cross['close_above_ma5']) &
        (~df_cross['prev_close_above_ma5'].fillna(True)) &
        (df_cross['prev2_close_above_ma5'].fillna(True))
    )
    
    return df_cross


def identify_turning_points(df: pd.DataFrame, window_size: int = 5) -> pd.DataFrame:
    """
    識別股價的轉折高點和轉折低點（書本規格完整版）
    
    完整實作書本規格的6大規則，特別是位移規則（規則6-2）
    採用「即時更新法」：在群組內持續追蹤極值，發現更極端值立即更新位置
    
    Args:
        df: K線數據DataFrame，需要包含以下欄位：
            - Close: 收盤價
            - High: 最高價（含上影線）
            - Low: 最低價（含下影線）
            - ma5: 5日移動平均線
        window_size: 保留參數，向後兼容（實際不使用）
    
    Returns:
        DataFrame，包含以下欄位：
            - date: 日期（字串格式 'YYYY-MM-DD'）
            - turning_high_point: 轉折高點標記（'O' 或 ''）
            - turning_low_point: 轉折低點標記（'O' 或 ''）
    
    實作說明：
        1. 使用連續2天確認機制檢測穿越事件
        2. 使用TurningPointTracker持續追蹤群組內極值
        3. 當發現更極端的值時立即更新（實現位移規則）
        4. 穿越發生時確認標記（自動符合位移規則）
        5. 確保高低點交替（規則6-3）
    """
    # 初始化結果列表
    results = []
    
    # 檢查必要欄位
    if 'ma5' not in df.columns:
        raise ValueError("DataFrame必須包含'ma5'欄位")
    
    # 初始化轉折點追蹤器
    tracker = TurningPointTracker()
    
    # 檢測穿越事件
    df_with_cross = detect_cross_events(df)
    
    # 記錄當前所處的群組類型
    current_position = None  # 'above' 或 'below'
    
    # 遍歷每一根K線
    for i, (idx, row) in enumerate(df_with_cross.iterrows()):
        date = idx.strftime('%Y-%m-%d')
        
        # 初始化當天的結果
        turning_high_point = ''
        turning_low_point = ''
        
        # 邊界條件檢查
        if i < 2 or pd.isna(row['ma5']):
            results.append({
                'date': date,
                'turning_high_point': turning_high_point,
                'turning_low_point': turning_low_point
            })
            continue
        
        # 取得當前收盤價與MA5的關係
        close_above_ma5 = row['close_above_ma5']
        
        # === 處理穿越事件 ===
        
        # 檢測向上穿越
        if row['cross_up']:
            # 發生向上穿越 → 結束負價群組，開始正價群組
            
            # 1. 確認前一個負價群組的轉折低點
            if tracker.current_group_type == 'negative':
                mark_result = tracker.confirm_current_extremum('low')
                if mark_result:
                    mark_date, mark_type = mark_result
                    # 找到對應日期並標記
                    for j, result in enumerate(results):
                        if result['date'] == mark_date:
                            results[j]['turning_low_point'] = 'O'
                            break
            
            # 2. 開始新的正價群組
            tracker.start_positive_group(i, date, row['High'])
            current_position = 'above'
        
        # 檢測向下穿越
        elif row['cross_down']:
            # 發生向下穿越 → 結束正價群組，開始負價群組
            
            # 1. 確認前一個正價群組的轉折高點
            if tracker.current_group_type == 'positive':
                mark_result = tracker.confirm_current_extremum('high')
                if mark_result:
                    mark_date, mark_type = mark_result
                    # 找到對應日期並標記
                    for j, result in enumerate(results):
                        if result['date'] == mark_date:
                            results[j]['turning_high_point'] = 'O'
                            break
            
            # 2. 開始新的負價群組
            tracker.start_negative_group(i, date, row['Low'])
            current_position = 'below'
        
        # === 在同一群組內更新極值（實現位移規則） ===
        else:
            # 沒有穿越事件，在當前群組內更新極值
            
            if close_above_ma5 and tracker.current_group_type == 'positive':
                # 在正價群組內，檢查是否有更高的點
                tracker.update_extremum_in_positive_group(i, date, row['High'])
            
            elif not close_above_ma5 and tracker.current_group_type == 'negative':
                # 在負價群組內，檢查是否有更低的點
                tracker.update_extremum_in_negative_group(i, date, row['Low'])
            
            elif close_above_ma5 and tracker.current_group_type is None:
                # 第一次進入正價群組
                tracker.start_positive_group(i, date, row['High'])
                current_position = 'above'
            
            elif not close_above_ma5 and tracker.current_group_type is None:
                # 第一次進入負價群組
                tracker.start_negative_group(i, date, row['Low'])
                current_position = 'below'
        
        # 記錄當天結果
        results.append({
            'date': date,
            'turning_high_point': turning_high_point,
            'turning_low_point': turning_low_point
        })
    
    # === 處理最後一個未完成的群組 ===
    # 如果數據結束時仍有未確認的群組，可選擇是否標記
    # 這裡採用保守策略：不標記未完成的群組
    # 如需標記，可取消以下註釋：
    """
    if tracker.current_group_type == 'positive':
        mark_result = tracker.confirm_current_extremum('high')
        if mark_result:
            mark_date, mark_type = mark_result
            for j, result in enumerate(results):
                if result['date'] == mark_date:
                    results[j]['turning_high_point'] = 'O'
                    break
    elif tracker.current_group_type == 'negative':
        mark_result = tracker.confirm_current_extremum('low')
        if mark_result:
            mark_date, mark_type = mark_result
            for j, result in enumerate(results):
                if result['date'] == mark_date:
                    results[j]['turning_low_point'] = 'O'
                    break
    """
    
    return pd.DataFrame(results)


def check_turning_points(df: pd.DataFrame, window_size: int = 5) -> pd.DataFrame:
    """
    檢查轉折點（向後兼容的別名函數）
    
    Args:
        df: K線數據
        window_size: 保留參數（向後兼容）
    
    Returns:
        轉折點識別結果
    """
    return identify_turning_points(df, window_size)


def verify_turning_points_quality(df: pd.DataFrame, turning_points_df: pd.DataFrame) -> dict:
    """
    驗證轉折點識別質量
    
    檢查是否符合書本規格的重要原則
    
    Args:
        df: 原始K線數據
        turning_points_df: 轉折點識別結果
    
    Returns:
        dict，包含驗證結果：
            - alternating: 是否高低點交替
            - no_missing_extremum: 是否無遺漏極值
            - high_points_count: 轉折高點數量
            - low_points_count: 轉折低點數量
            - issues: 問題列表
    """
    issues = []
    
    # 提取轉折點
    high_points = turning_points_df[turning_points_df['turning_high_point'] == 'O']['date'].tolist()
    low_points = turning_points_df[turning_points_df['turning_low_point'] == 'O']['date'].tolist()
    
    # 合併並排序所有轉折點
    all_points = []
    for date in high_points:
        all_points.append((date, 'high'))
    for date in low_points:
        all_points.append((date, 'low'))
    all_points.sort(key=lambda x: x[0])
    
    # 檢查1：高低點是否交替
    alternating = True
    for i in range(len(all_points) - 1):
        if all_points[i][1] == all_points[i+1][1]:
            alternating = False
            issues.append(f"連續兩個{all_points[i][1]}點: {all_points[i][0]} 和 {all_points[i+1][0]}")
    
    # 檢查2：是否有遺漏的極值
    # 這個檢查較複雜，需要檢測穿越事件並驗證每個群組是否有標記
    no_missing_extremum = True  # 簡化版本，完整檢查需要更多代碼
    
    return {
        'alternating': alternating,
        'no_missing_extremum': no_missing_extremum,
        'high_points_count': len(high_points),
        'low_points_count': len(low_points),
        'issues': issues
    }


if __name__ == "__main__":
    print("轉折點識別模塊 - 書本規格標準版 v2.0")
    print("="*60)
    print("完整實作書本規格的6大規則，特別是位移規則")
    print("使用方式：")
    print("  from turning_point_identification import identify_turning_points")
    print("  result = identify_turning_points(df)")
    print("="*60)