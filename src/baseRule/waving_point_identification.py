#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
趨勢波偵測程式 (Waving Point Identification)
根據轉折點識別趨勢波，並標記波段高點和波段低點
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class TrendType(Enum):
    """趨勢類型"""
    UP = 'up'           # 上升趨勢：底底高、頭頭高
    DOWN = 'down'       # 下降趨勢：頭頭低、底底低
    CONSOLIDATION = 'consolidation'  # 盤整趨勢：頭不過頭、底不破底
    NONE = None         # 無趨勢（初始狀態）


class PendingReversalType(Enum):
    """等待確認的反轉類型"""
    DOWN_TO_UP = 'down_to_up'    # 下降轉上升（等待確認底底高）
    UP_TO_DOWN = 'up_to_down'    # 上升轉下降（等待確認頭頭低）
    NONE = None


@dataclass
class TurningPoint:
    """轉折點資料結構"""
    date: pd.Timestamp
    price: float
    point_type: str  # 'high' 或 'low'
    
    def __repr__(self):
        return f"TurningPoint({self.date.strftime('%Y-%m-%d')}, {self.point_type}, {self.price:.2f})"


@dataclass
class WavePoint:
    """波段點資料結構"""
    date: pd.Timestamp
    price: float
    point_type: str  # 'wave_high' 或 'wave_low'
    
    def __repr__(self):
        return f"WavePoint({self.date.strftime('%Y-%m-%d')}, {self.point_type}, {self.price:.2f})"


@dataclass
class TrendState:
    """趨勢狀態資料結構"""
    current_trend: TrendType = TrendType.NONE
    trend_start_date: Optional[pd.Timestamp] = None
    last_wave_high: Optional[WavePoint] = None
    last_wave_low: Optional[WavePoint] = None
    
    # 轉折點歷史（最近的幾個轉折點）
    recent_high_points: List[TurningPoint] = None
    recent_low_points: List[TurningPoint] = None
    
    def __post_init__(self):
        if self.recent_high_points is None:
            self.recent_high_points = []
        if self.recent_low_points is None:
            self.recent_low_points = []


@dataclass
class PendingReversal:
    """等待確認的反轉狀態"""
    active: bool = False
    reversal_type: PendingReversalType = PendingReversalType.NONE
    trigger_point: Optional[TurningPoint] = None  # Now的位置
    reference_high: Optional[TurningPoint] = None  # H1 或 H2
    reference_low: Optional[TurningPoint] = None   # L1 或 L2
    search_range_start: Optional[pd.Timestamp] = None  # 搜尋區間起點


class WavingPointIdentifier:
    """趨勢波識別器"""
    
    def __init__(self, debug: bool = False):
        """
        初始化識別器
        
        Args:
            debug: 是否輸出調試信息
        """
        self.debug = debug
        self.state = TrendState()
        self.pending = PendingReversal()
        self.log_messages = []
        
    def log(self, message: str, level: str = "INFO"):
        """記錄日誌"""
        log_entry = f"[{level}] {message}"
        self.log_messages.append(log_entry)
        if self.debug:
            print(log_entry)
    
    def identify_waving_points(self, df: pd.DataFrame, turning_points_df: pd.DataFrame) -> pd.DataFrame:
        """
        識別趨勢波和波段點
        
        Args:
            df: 原始K線數據（包含 Open, High, Low, Close 等）
            turning_points_df: 轉折點數據（包含 date, turning_high_point, turning_low_point）
        
        Returns:
            包含波段點標記的DataFrame
        """
        self.log("="*80)
        self.log("開始識別趨勢波和波段點")
        self.log("="*80)
        
        # 初始化結果DataFrame
        result = turning_points_df.copy()
        result['wave_high_point'] = ''
        result['wave_low_point'] = ''
        result['trend_type'] = ''
        result['pending_reversal'] = ''
        
        # 提取所有轉折點
        turning_points = self._extract_turning_points(df, turning_points_df)
        
        if not turning_points:
            self.log("警告：沒有找到任何轉折點", "WARNING")
            return result
        
        self.log(f"總共找到 {len(turning_points)} 個轉折點")
        
        # 逐個處理轉折點
        for i, tp in enumerate(turning_points):
            self.log(f"\n{'='*60}")
            self.log(f"處理轉折點 {i+1}/{len(turning_points)}: {tp}")
            self.log(f"當前趨勢: {self.state.current_trend.value}")
            
            # 更新轉折點歷史
            if tp.point_type == 'high':
                self.state.recent_high_points.append(tp)
                if len(self.state.recent_high_points) > 3:
                    self.state.recent_high_points.pop(0)
            else:
                self.state.recent_low_points.append(tp)
                if len(self.state.recent_low_points) > 3:
                    self.state.recent_low_points.pop(0)
            
            # 檢查是否有待確認的反轉
            if self.pending.active:
                self._check_pending_reversal(tp, df, result)
            
            # 檢查趨勢反轉條件
            self._check_trend_reversal(tp, df, result)
            
            # 更新當前行的趨勢類型
            date_str = tp.date.strftime('%Y-%m-%d')
            result.loc[result['date'] == date_str, 'trend_type'] = self.state.current_trend.value or ''
            if self.pending.active:
                result.loc[result['date'] == date_str, 'pending_reversal'] = self.pending.reversal_type.value
        
        self.log("\n" + "="*80)
        self.log("趨勢波識別完成")
        self.log("="*80)
        
        return result
    
    def _extract_turning_points(self, df: pd.DataFrame, turning_points_df: pd.DataFrame) -> List[TurningPoint]:
        """從DataFrame中提取轉折點列表"""
        turning_points = []
        
        for _, row in turning_points_df.iterrows():
            date = pd.to_datetime(row['date'])
            
            # 找到對應的K線數據
            if date not in df.index:
                continue
            
            k_data = df.loc[date]
            
            # 檢查是否為轉折高點
            if row['turning_high_point'] == 'O':
                tp = TurningPoint(
                    date=date,
                    price=float(k_data['High']),
                    point_type='high'
                )
                turning_points.append(tp)
            
            # 檢查是否為轉折低點
            if row['turning_low_point'] == 'O':
                tp = TurningPoint(
                    date=date,
                    price=float(k_data['Low']),
                    point_type='low'
                )
                turning_points.append(tp)
        
        # 按日期排序
        turning_points.sort(key=lambda x: x.date)
        
        return turning_points
    
    def _check_trend_reversal(self, current_tp: TurningPoint, df: pd.DataFrame, result: pd.DataFrame):
        """
        檢查趨勢反轉條件
        
        根據規格書的邏輯：
        1. 下降趨勢 → 上升趨勢：突破前高（Now > H1）
        2. 上升趨勢 → 下降趨勢：跌破前低（Now < L1）
        """
        
        # 情況1：下降趨勢中出現新高點，檢查是否突破前高
        if self.state.current_trend == TrendType.DOWN and current_tp.point_type == 'high':
            self._check_down_to_up_reversal(current_tp, df, result)
        
        # 情況2：上升趨勢中出現新低點，檢查是否跌破前低
        elif self.state.current_trend == TrendType.UP and current_tp.point_type == 'low':
            self._check_up_to_down_reversal(current_tp, df, result)
        
        # 情況3：無趨勢或盤整時，建立初始趨勢
        elif self.state.current_trend in [TrendType.NONE, TrendType.CONSOLIDATION]:
            self._establish_initial_trend(current_tp)
    
    def _check_down_to_up_reversal(self, current_tp: TurningPoint, df: pd.DataFrame, result: pd.DataFrame):
        """
        檢查下降趨勢 → 上升趨勢的反轉
        
        轉折點序列：... → L1 → H1 → L2 → Now（高點）
        檢測條件：Now > H1（突破前高）
        """
        if len(self.state.recent_high_points) < 1 or len(self.state.recent_low_points) < 2:
            self.log("轉折點數量不足，無法判斷反轉")
            return
        
        # Now = 當前高點
        Now = current_tp
        # H1 = 前一個高點
        H1 = self.state.recent_high_points[-1]
        # L2 = 最近的低點
        L2 = self.state.recent_low_points[-1]
        # L1 = 前一個低點
        L1 = self.state.recent_low_points[-2] if len(self.state.recent_low_points) >= 2 else None
        
        self.log(f"檢查下降→上升反轉：Now={Now.price:.2f}, H1={H1.price:.2f}, L2={L2.price:.2f}, L1={L1.price:.2f if L1 else 'N/A'}")
        
        # 檢查是否突破前高
        if Now.price > H1.price:
            self.log(f"✅ 突破前高！Now({Now.price:.2f}) > H1({H1.price:.2f})")
            
            if L1 is None:
                self.log("L1不存在，無法判斷底底關係")
                return
            
            # 情境A：底底高已完成（L2 > L1）
            if L2.price > L1.price:
                self.log(f"✅ 情境A：底底高已完成 L2({L2.price:.2f}) > L1({L1.price:.2f})")
                self.log("立即確認上升趨勢")
                
                # 確認趨勢反轉
                self.state.current_trend = TrendType.UP
                self.state.trend_start_date = Now.date
                
                # 標記波段低點
                self._mark_wave_low_point(L1.date, L2.date, df, result)
            
            # 情境B：底底低（L2 < L1）
            else:
                self.log(f"⏸️ 情境B：底底低 L2({L2.price:.2f}) < L1({L1.price:.2f})")
                self.log("進入等待確認狀態，等待新低點L3出現")
                
                # 設置等待確認狀態
                self.pending.active = True
                self.pending.reversal_type = PendingReversalType.DOWN_TO_UP
                self.pending.trigger_point = Now
                self.pending.reference_high = H1
                self.pending.reference_low = L2
                
                # 確定搜尋區間起點（前波段高點）
                if self.state.last_wave_high:
                    self.pending.search_range_start = self.state.last_wave_high.date
                else:
                    # 回溯60天或使用趨勢開始點
                    self.pending.search_range_start = L1.date
                
                self.log(f"搜尋區間起點：{self.pending.search_range_start.strftime('%Y-%m-%d')}")
    
    def _check_up_to_down_reversal(self, current_tp: TurningPoint, df: pd.DataFrame, result: pd.DataFrame):
        """
        檢查上升趨勢 → 下降趨勢的反轉
        
        轉折點序列：... → H1 → L1 → H2 → Now（低點）
        檢測條件：Now < L1（跌破前低）
        """
        if len(self.state.recent_low_points) < 1 or len(self.state.recent_high_points) < 2:
            self.log("轉折點數量不足，無法判斷反轉")
            return
        
        # Now = 當前低點
        Now = current_tp
        # L1 = 前一個低點
        L1 = self.state.recent_low_points[-1]
        # H2 = 最近的高點
        H2 = self.state.recent_high_points[-1]
        # H1 = 前一個高點
        H1 = self.state.recent_high_points[-2] if len(self.state.recent_high_points) >= 2 else None
        
        self.log(f"檢查上升→下降反轉：Now={Now.price:.2f}, L1={L1.price:.2f}, H2={H2.price:.2f}, H1={H1.price:.2f if H1 else 'N/A'}")
        
        # 檢查是否跌破前低
        if Now.price < L1.price:
            self.log(f"✅ 跌破前低！Now({Now.price:.2f}) < L1({L1.price:.2f})")
            
            if H1 is None:
                self.log("H1不存在，無法判斷頭頭關係")
                return
            
            # 情境A：頭頭低已完成（H2 < H1）
            if H2.price < H1.price:
                self.log(f"✅ 情境A：頭頭低已完成 H2({H2.price:.2f}) < H1({H1.price:.2f})")
                self.log("立即確認下降趨勢")
                
                # 確認趨勢反轉
                self.state.current_trend = TrendType.DOWN
                self.state.trend_start_date = Now.date
                
                # 標記波段高點
                self._mark_wave_high_point(H1.date, H2.date, df, result)
            
            # 情境B：頭頭高（H2 > H1）
            else:
                self.log(f"⏸️ 情境B：頭頭高 H2({H2.price:.2f}) > H1({H1.price:.2f})")
                self.log("進入等待確認狀態，等待新高點H3出現")
                
                # 設置等待確認狀態
                self.pending.active = True
                self.pending.reversal_type = PendingReversalType.UP_TO_DOWN
                self.pending.trigger_point = Now
                self.pending.reference_low = L1
                self.pending.reference_high = H2
                
                # 確定搜尋區間起點（前波段低點）
                if self.state.last_wave_low:
                    self.pending.search_range_start = self.state.last_wave_low.date
                else:
                    # 回溯60天或使用趨勢開始點
                    self.pending.search_range_start = H1.date
                
                self.log(f"搜尋區間起點：{self.pending.search_range_start.strftime('%Y-%m-%d')}")
    
    def _check_pending_reversal(self, current_tp: TurningPoint, df: pd.DataFrame, result: pd.DataFrame):
        """檢查等待確認的反轉狀態"""
        
        if not self.pending.active:
            return
        
        self.log(f"檢查等待確認狀態：{self.pending.reversal_type.value}")
        
        # 下降→上升：等待新低點L3
        if self.pending.reversal_type == PendingReversalType.DOWN_TO_UP:
            if current_tp.point_type == 'low':
                L3 = current_tp
                L2 = self.pending.reference_low
                
                self.log(f"出現新低點L3={L3.price:.2f}, L2={L2.price:.2f}")
                
                # L3 > L2（底底高）→ 確認上升趨勢
                if L3.price > L2.price:
                    self.log(f"✅ 確認：L3({L3.price:.2f}) > L2({L2.price:.2f}) 底底高")
                    self.log("上升趨勢成形")
                    
                    self.state.current_trend = TrendType.UP
                    self.state.trend_start_date = L3.date
                    
                    # 標記波段低點
                    self._mark_wave_low_point(self.pending.search_range_start, L2.date, df, result)
                    
                    # 清除等待狀態
                    self.pending = PendingReversal()
                
                # L3 < L2（再破底）→ 假突破
                else:
                    self.log(f"❌ 假突破：L3({L3.price:.2f}) < L2({L2.price:.2f}) 再破底")
                    self.log("繼續下降趨勢，取消等待")
                    
                    # 清除等待狀態，繼續下降趨勢
                    self.pending = PendingReversal()
                    self.state.current_trend = TrendType.DOWN
        
        # 上升→下降：等待新高點H3
        elif self.pending.reversal_type == PendingReversalType.UP_TO_DOWN:
            if current_tp.point_type == 'high':
                H3 = current_tp
                H2 = self.pending.reference_high
                
                self.log(f"出現新高點H3={H3.price:.2f}, H2={H2.price:.2f}")
                
                # H3 < H2（頭頭低）→ 確認下降趨勢
                if H3.price < H2.price:
                    self.log(f"✅ 確認：H3({H3.price:.2f}) < H2({H2.price:.2f}) 頭頭低")
                    self.log("下降趨勢成形")
                    
                    self.state.current_trend = TrendType.DOWN
                    self.state.trend_start_date = H3.date
                    
                    # 標記波段高點
                    self._mark_wave_high_point(self.pending.search_range_start, H2.date, df, result)
                    
                    # 清除等待狀態
                    self.pending = PendingReversal()
                
                # H3 > H2（再創高）→ 假跌破
                else:
                    self.log(f"❌ 假跌破：H3({H3.price:.2f}) > H2({H2.price:.2f}) 再創高")
                    self.log("繼續上升趨勢，取消等待")
                    
                    # 清除等待狀態，繼續上升趨勢
                    self.pending = PendingReversal()
                    self.state.current_trend = TrendType.UP
    
    def _mark_wave_low_point(self, start_date: pd.Timestamp, end_date: pd.Timestamp, 
                             df: pd.DataFrame, result: pd.DataFrame):
        """
        標記波段低點
        
        在搜尋區間內找出所有轉折低點，選擇價格最低者標記為波段低點
        """
        self.log(f"標記波段低點：搜尋區間 {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
        
        # 提取搜尋區間
        mask = (result['date'] >= start_date.strftime('%Y-%m-%d')) & \
               (result['date'] <= end_date.strftime('%Y-%m-%d'))
        period_df = result[mask]
        
        # 找出所有轉折低點
        turning_lows = period_df[period_df['turning_low_point'] == 'O']
        
        if len(turning_lows) == 0:
            self.log("⚠️ 區間內無轉折低點，使用區間終點", "WARNING")
            # 使用終點日期
            wave_date = end_date.strftime('%Y-%m-%d')
            if wave_date in df.index.strftime('%Y-%m-%d'):
                wave_price = df[df.index.strftime('%Y-%m-%d') == wave_date]['Low'].iloc[0]
            else:
                return
        else:
            # 找出價格最低的轉折低點
            min_low_idx = None
            min_low_price = float('inf')
            
            for _, row in turning_lows.iterrows():
                date_str = row['date']
                date_ts = pd.to_datetime(date_str)
                if date_ts in df.index:
                    low_price = df.loc[date_ts, 'Low']
                    if low_price < min_low_price:
                        min_low_price = low_price
                        min_low_idx = date_str
            
            wave_date = min_low_idx
            wave_price = min_low_price
        
        # 標記波段低點
        result.loc[result['date'] == wave_date, 'wave_low_point'] = 'O'
        
        # 更新狀態
        self.state.last_wave_low = WavePoint(
            date=pd.to_datetime(wave_date),
            price=wave_price,
            point_type='wave_low'
        )
        
        self.log(f"✅ 波段低點已標記：{wave_date} (價格: {wave_price:.2f})")
    
    def _mark_wave_high_point(self, start_date: pd.Timestamp, end_date: pd.Timestamp,
                              df: pd.DataFrame, result: pd.DataFrame):
        """
        標記波段高點
        
        在搜尋區間內找出所有轉折高點，選擇價格最高者標記為波段高點
        """
        self.log(f"標記波段高點：搜尋區間 {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
        
        # 提取搜尋區間
        mask = (result['date'] >= start_date.strftime('%Y-%m-%d')) & \
               (result['date'] <= end_date.strftime('%Y-%m-%d'))
        period_df = result[mask]
        
        # 找出所有轉折高點
        turning_highs = period_df[period_df['turning_high_point'] == 'O']
        
        if len(turning_highs) == 0:
            self.log("⚠️ 區間內無轉折高點，使用區間終點", "WARNING")
            # 使用終點日期
            wave_date = end_date.strftime('%Y-%m-%d')
            if wave_date in df.index.strftime('%Y-%m-%d'):
                wave_price = df[df.index.strftime('%Y-%m-%d') == wave_date]['High'].iloc[0]
            else:
                return
        else:
            # 找出價格最高的轉折高點
            max_high_idx = None
            max_high_price = float('-inf')
            
            for _, row in turning_highs.iterrows():
                date_str = row['date']
                date_ts = pd.to_datetime(date_str)
                if date_ts in df.index:
                    high_price = df.loc[date_ts, 'High']
                    if high_price > max_high_price:
                        max_high_price = high_price
                        max_high_idx = date_str
            
            wave_date = max_high_idx
            wave_price = max_high_price
        
        # 標記波段高點
        result.loc[result['date'] == wave_date, 'wave_high_point'] = 'O'
        
        # 更新狀態
        self.state.last_wave_high = WavePoint(
            date=pd.to_datetime(wave_date),
            price=wave_price,
            point_type='wave_high'
        )
        
        self.log(f"✅ 波段高點已標記：{wave_date} (價格: {wave_price:.2f})")
    
    def _establish_initial_trend(self, current_tp: TurningPoint):
        """建立初始趨勢"""
        if self.state.current_trend == TrendType.NONE:
            self.log("初始化趨勢狀態")
            # 暫時不設定趨勢，等待更多轉折點
            if len(self.state.recent_high_points) >= 2 and len(self.state.recent_low_points) >= 2:
                # 簡單判斷初始趨勢
                latest_high = self.state.recent_high_points[-1]
                prev_high = self.state.recent_high_points[-2]
                latest_low = self.state.recent_low_points[-1]
                prev_low = self.state.recent_low_points[-2]
                
                # 判斷趨勢
                if latest_high.price > prev_high.price and latest_low.price > prev_low.price:
                    self.state.current_trend = TrendType.UP
                    self.log("初始趨勢：上升")
                elif latest_high.price < prev_high.price and latest_low.price < prev_low.price:
                    self.state.current_trend = TrendType.DOWN
                    self.log("初始趨勢：下降")
                else:
                    self.state.current_trend = TrendType.CONSOLIDATION
                    self.log("初始趨勢：盤整")


def identify_waving_points(df: pd.DataFrame, turning_points_df: pd.DataFrame, 
                          debug: bool = False) -> pd.DataFrame:
    """
    識別趨勢波和波段點（便捷函數）
    
    Args:
        df: 原始K線數據
        turning_points_df: 轉折點數據
        debug: 是否輸出調試信息
    
    Returns:
        包含波段點標記的DataFrame
    """
    identifier = WavingPointIdentifier(debug=debug)
    return identifier.identify_waving_points(df, turning_points_df)


if __name__ == "__main__":
    # 測試代碼
    print("趨勢波識別模組")
    print("使用方式：")
    print("  from waving_point_identification import identify_waving_points")
    print("  result = identify_waving_points(df, turning_points_df, debug=True)")