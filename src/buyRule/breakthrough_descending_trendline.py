import pandas as pd
import numpy as np
from ..baseRule.turning_point_identification import identify_turning_points
from .long_term_descending_trendline import identify_long_term_descending_trendlines

def check_breakthrough_descending_trendline_buy_rule(df: pd.DataFrame, 
                                                   turning_points_df: pd.DataFrame = None,
                                                   min_days_long_term: int = 180,
                                                   min_points_short_term: int = 3,
                                                   volume_confirmation: bool = True,
                                                   volume_multiplier: float = 1.2,
                                                   min_breakthrough_percentage: float = 0.5) -> pd.DataFrame:
    """
    收盤站上下降趨勢線買入規則檢查函數
    
    買入條件：
    1. 識別有效的下降趨勢線（長期2點或短期多點）
    2. 當日收盤價向上突破下降趨勢線
    3. 突破幅度達到最小百分比要求（可選）
    4. 成交量放大確認（可選）
    5. 優先考慮長期趨勢線突破
    
    Args:
        df (pd.DataFrame): 包含K線數據的DataFrame，需要包含 'Close', 'High', 'Low'，可選 'Volume' 列
        turning_points_df (pd.DataFrame, optional): 轉折點識別結果
        min_days_long_term (int): 長期趨勢線的最小天數定義，預設180天
        min_points_short_term (int): 短期趨勢線所需最小點數，預設3
        volume_confirmation (bool): 是否需要成交量確認，預設True
        volume_multiplier (float): 成交量放大倍數，預設1.2倍
        min_breakthrough_percentage (float): 最小突破百分比，預設0.5%
    
    Returns:
        pd.DataFrame: 包含買入信號的DataFrame，包含以下欄位：
        - date: 日期
        - breakthrough_descending_trendline_buy: 'O' 表示滿足條件，'' 表示不滿足
        - signal_strength: 信號強度 (1-5分)
        - breakthrough_type: 突破類型 ('long_term_two_point' 或 'short_term_multi_point')
        - days_span: 趨勢線時間跨度
        - breakthrough_percentage: 突破百分比
        - volume_ratio: 成交量比率
        - trendline_slope: 趨勢線斜率
    """
    
    # 準備轉折點數據
    if turning_points_df is None:
        if 'ma5' not in df.columns:
            df['ma5'] = df['Close'].rolling(window=5, min_periods=1).mean()
        turning_points_df = identify_turning_points(df)
    
    # 識別下降趨勢線
    trendlines = identify_long_term_descending_trendlines(
        df, turning_points_df, min_days_long_term, min_points_short_term
    )
    
    results = []
    all_lines = trendlines['all_lines']
    
    # 預計算成交量移動平均（如果需要）
    volume_ma = None
    if volume_confirmation and 'Volume' in df.columns:
        volume_ma = df['Volume'].rolling(window=20, min_periods=5).mean()
    
    # 對每個日期進行檢查
    for i, (idx, row) in enumerate(df.iterrows()):
        date = idx.strftime('%Y-%m-%d')
        
        # 初始化結果
        buy_signal = ''
        signal_strength = 0
        breakthrough_type = ''
        days_span = 0
        breakthrough_percentage = 0.0
        volume_ratio = 1.0
        trendline_slope = 0.0
        
        current_close = row['Close']
        valid_breakthroughs = []
        
        # 檢查每條趨勢線的突破情況
        for line in all_lines:
            # 檢查是否在趨勢線的有效時間範圍內
            if idx < line['start_date']:
                continue
            
            # 計算當前日期趨勢線的理論價格
            equation = line['equation']
            current_line_price = equation['intercept'] + equation['slope'] * i
            
            # 檢查收盤價是否站上趨勢線
            if current_close > current_line_price:
                
                # 計算突破百分比
                breakthrough_pct = ((current_close - current_line_price) / current_line_price) * 100
                
                # 檢查是否達到最小突破百分比
                if breakthrough_pct >= min_breakthrough_percentage:
                    
                    # 成交量確認
                    volume_ok = True
                    current_volume_ratio = 1.0
                    
                    if volume_confirmation and volume_ma is not None and not pd.isna(volume_ma.iloc[i]):
                        current_volume_ratio = row['Volume'] / volume_ma.iloc[i]
                        volume_ok = current_volume_ratio >= volume_multiplier
                    
                    if volume_ok:
                        valid_breakthroughs.append({
                            'line': line,
                            'breakthrough_pct': breakthrough_pct,
                            'volume_ratio': current_volume_ratio,
                            'line_price': current_line_price
                        })
        
        # 如果有有效的突破，選擇最佳的一個
        if valid_breakthroughs:
            
            # 選擇策略：優先考慮長期趨勢線，其次考慮突破強度
            best_breakthrough = _select_best_breakthrough(valid_breakthroughs)
            
            if best_breakthrough:
                buy_signal = 'O'
                line = best_breakthrough['line']
                breakthrough_type = line['type']
                days_span = line['days_span']
                breakthrough_percentage = best_breakthrough['breakthrough_pct']
                volume_ratio = best_breakthrough['volume_ratio']
                trendline_slope = abs(line['slope'])  # 取絕對值，斜率越陡越好
                
                # 計算信號強度 (1-5分)
                signal_strength = _calculate_signal_strength(
                    line, breakthrough_percentage, volume_ratio
                )
        
        # 添加結果
        results.append({
            'date': date,
            'breakthrough_descending_trendline_buy': buy_signal,
            'signal_strength': signal_strength,
            'breakthrough_type': breakthrough_type,
            'days_span': days_span,
            'breakthrough_percentage': round(breakthrough_percentage, 2),
            'volume_ratio': round(volume_ratio, 2),
            'trendline_slope': round(trendline_slope, 6)
        })
    
    return pd.DataFrame(results)


def _select_best_breakthrough(valid_breakthroughs: list) -> dict:
    """
    從多個有效突破中選擇最佳的一個
    
    選擇優先級：
    1. 長期趨勢線 > 短期趨勢線
    2. 時間跨度越長越好
    3. 突破幅度適中（不要太極端）
    4. 成交量放大倍數適中
    """
    if not valid_breakthroughs:
        return None
    
    # 按優先級排序
    def breakthrough_score(bt):
        line = bt['line']
        score = 0
        
        # 1. 趨勢線類型得分 (最重要)
        if line['type'] == 'long_term_two_point':
            score += 1000
        else:  # short_term_multi_point
            score += 800
        
        # 2. 時間跨度得分
        score += min(line['days_span'] / 10, 100)  # 最多100分
        
        # 3. 突破幅度得分 (1-3%比較理想，太大可能是假突破)
        breakthrough_pct = bt['breakthrough_pct']
        if 0.5 <= breakthrough_pct <= 3.0:
            score += 50 - abs(breakthrough_pct - 1.5) * 10  # 1.5%是最佳
        elif breakthrough_pct > 3.0:
            score += max(0, 30 - (breakthrough_pct - 3.0) * 5)  # 過大扣分
        
        # 4. 成交量得分 (1.2-2.0倍比較理想)
        volume_ratio = bt['volume_ratio']
        if 1.2 <= volume_ratio <= 2.0:
            score += 30
        elif volume_ratio > 2.0:
            score += max(0, 20 - (volume_ratio - 2.0) * 5)  # 過大扣分
        
        # 5. R²得分 (多點線才有)
        if 'r_squared' in line and line['r_squared'] > 0:
            score += line['r_squared'] * 20  # 最多20分
        
        return score
    
    # 選擇得分最高的
    best_breakthrough = max(valid_breakthroughs, key=breakthrough_score)
    return best_breakthrough


def _calculate_signal_strength(line: dict, breakthrough_pct: float, volume_ratio: float) -> int:
    """
    計算信號強度 (1-5分)
    
    評分標準：
    - 5分: 強烈買入 (長期趨勢線 + 理想突破)
    - 4分: 買入 (長期趨勢線 或 高品質短期線)
    - 3分: 中性偏多 (一般品質突破)
    - 2分: 弱買入 (勉強符合條件)
    - 1分: 非常弱 (剛好達到門檻)
    """
    score = 1  # 基礎分數
    
    # 趨勢線類型加分
    if line['type'] == 'long_term_two_point':
        if line['days_span'] >= 365:  # 超過1年
            score += 2
        elif line['days_span'] >= 180:  # 6個月到1年
            score += 1.5
    else:  # short_term_multi_point
        if line.get('r_squared', 0) >= 0.9:
            score += 1
        elif line.get('r_squared', 0) >= 0.8:
            score += 0.5
    
    # 突破幅度加分
    if 1.0 <= breakthrough_pct <= 2.5:  # 理想突破幅度
        score += 1
    elif 0.5 <= breakthrough_pct < 1.0 or 2.5 < breakthrough_pct <= 4.0:  # 可接受範圍
        score += 0.5
    
    # 成交量加分
    if 1.5 <= volume_ratio <= 2.0:  # 理想成交量
        score += 1
    elif 1.2 <= volume_ratio < 1.5 or 2.0 < volume_ratio <= 3.0:  # 可接受範圍
        score += 0.5
    
    # 趨勢線斜率加分 (越陡峭的下降線被突破越重要)
    slope_abs = abs(line['slope'])
    if slope_abs >= 0.5:  # 陡峭下降
        score += 0.5
    
    return min(5, max(1, round(score)))


def get_breakthrough_summary_stats(breakthrough_df: pd.DataFrame) -> dict:
    """
    獲取突破信號的統計摘要
    
    Returns:
        dict: 包含各種統計數據的字典
    """
    signals = breakthrough_df[breakthrough_df['breakthrough_descending_trendline_buy'] == 'O']
    
    if len(signals) == 0:
        return {
            'total_signals': 0,
            'avg_signal_strength': 0,
            'long_term_signals': 0,
            'short_term_signals': 0,
            'avg_days_span': 0,
            'avg_breakthrough_percentage': 0,
            'avg_volume_ratio': 0
        }
    
    return {
        'total_signals': len(signals),
        'avg_signal_strength': round(signals['signal_strength'].mean(), 2),
        'long_term_signals': len(signals[signals['breakthrough_type'] == 'long_term_two_point']),
        'short_term_signals': len(signals[signals['breakthrough_type'] == 'short_term_multi_point']),
        'avg_days_span': round(signals['days_span'].mean(), 0),
        'avg_breakthrough_percentage': round(signals['breakthrough_percentage'].mean(), 2),
        'avg_volume_ratio': round(signals['volume_ratio'].mean(), 2),
        'signal_strength_distribution': signals['signal_strength'].value_counts().to_dict()
    }