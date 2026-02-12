import pandas as pd
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict
from src.baseRule.turning_point_identification import identify_turning_points

class TrendType(Enum):
    UP = "UP"
    DOWN = "DOWN"
    CONSOLIDATION = "CONSOLIDATION"
    UNKNOWN = "UNKNOWN"

@dataclass
class TrendResult:
    stock_id: str
    date: str
    status: TrendType
    last_high: Optional[float]
    last_low: Optional[float]
    details: str

def calculate_trend(df: pd.DataFrame, stock_id: str = "") -> TrendResult:
    """
    Calculates the trend status for the latest date in the dataframe.
    """
    
    # Validation
    if df is None or df.empty:
         return TrendResult(stock_id, "", TrendType.UNKNOWN, None, None, "No data")

    # Ensure ma5 exists for turning point identification
    local_df = df.copy()
    if 'ma5' not in local_df.columns:
        local_df['ma5'] = local_df['Close'].rolling(window=5, min_periods=1).mean()
        
    tp_df = identify_turning_points(local_df)
    
    # Extract points into a single chronological list
    points = []
    
    for idx, row in tp_df.iterrows():
        date = row['date']
        # Convert date string to timestamp if needed, but keeping as string is fine for sorting if format is YYYY-MM-DD
        
        if row['turning_high_point'] == 'O':
            # Check if date exists in local_df index
            try:
                price = local_df.loc[date]['High']
                points.append({'date': date, 'price': price, 'type': 'high'})
            except KeyError:
                pass
                
        if row['turning_low_point'] == 'O':
            try:
                price = local_df.loc[date]['Low']
                points.append({'date': date, 'price': price, 'type': 'low'})
            except KeyError:
                pass
    
    # Sort by date
    points.sort(key=lambda x: x['date'])
    
    latest_date = local_df.index[-1]
    latest_close = local_df.iloc[-1]['Close']
    date_str = latest_date.strftime('%Y-%m-%d')
    
    if len(points) < 3:
         return TrendResult(stock_id, date_str, TrendType.UNKNOWN, None, None, "Insufficient turning points")

    # Get last 3 points
    p1 = points[-3]
    p2 = points[-2]
    p3 = points[-1]
    
    # Logic 1: UPTREND (N-Pattern)
    # Sequence: Low(p1) -> High(p2) -> Low(p3) -> Breakout
    if p1['type'] == 'low' and p2['type'] == 'high' and p3['type'] == 'low':
        L_prev = p1['price']
        H_prev = p2['price']
        L_curr = p3['price']
        
        # Condition 1: Higher Low
        if L_curr > L_prev:
            # Condition 2: Breakout
            if latest_close > H_prev:
                return TrendResult(stock_id, date_str, TrendType.UP, H_prev, L_curr, f"N-Breakout: Close({latest_close:.2f}) > H_prev({H_prev:.2f}), HL({L_curr:.2f}>{L_prev:.2f})")
    
    # Logic 2: DOWNTREND (Inverted N-Pattern)
    # Sequence: High(p1) -> Low(p2) -> High(p3) -> Breakdown
    if p1['type'] == 'high' and p2['type'] == 'low' and p3['type'] == 'high':
        H_prev = p1['price']
        L_prev = p2['price']
        H_curr = p3['price']
        
        # Condition 1: Lower High
        if H_curr < H_prev:
            # Condition 2: Breakdown
            if latest_close < L_prev:
                return TrendResult(stock_id, date_str, TrendType.DOWN, H_curr, L_prev, f"N-Breakdown: Close({latest_close:.2f}) < L_prev({L_prev:.2f}), LH({H_curr:.2f}<{H_prev:.2f})")

    # Logic 3: UPTREND Continuation (Extension)
    # Sometimes we might have L -> H -> L -> H sequence where we are just in uptrend
    # But strictly following the "3 points lookback" request:
    # If the last 3 points don't fit the reversal pattern, we check if we are maintaining trend?
    # The user asked for "curr forward look 3 points + breakout".
    # Let's stick to the strict definition first. If not N-Breakout or N-Breakdown, it's Consolidation.
    
    return TrendResult(stock_id, date_str, TrendType.CONSOLIDATION, points[-1]['price'], points[-1]['price'], "No N-pattern confirmed")
