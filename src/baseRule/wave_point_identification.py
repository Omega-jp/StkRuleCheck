import pandas as pd
import numpy as np


def _remove_consecutive_wave_points(result_df: pd.DataFrame, price_df: pd.DataFrame) -> pd.DataFrame:
    """Ensure wave highs / lows alternate by dropping weaker duplicates."""
    if result_df is None or result_df.empty:
        return result_df

    working = result_df.copy()
    working["date"] = pd.to_datetime(working["date"], errors="coerce")
    working = working.sort_values("date").reset_index(drop=True)

    if price_df is None or price_df.empty:
        return working

    price_data = price_df.copy()
    if not isinstance(price_data.index, pd.DatetimeIndex):
        price_data = price_data.copy()
        price_data.index = pd.to_datetime(price_data.index, errors="coerce")

    if "High" not in price_data.columns or "Low" not in price_data.columns:
        return working

    last_kind: str | None = None
    last_idx: int | None = None
    last_price: float | None = None

    def _get_price(col: str, ts: pd.Timestamp) -> float | None:
        if pd.isna(ts):
            return None
        try:
            if ts not in price_data.index:
                return None
            value = price_data.loc[ts, col]
        except Exception:
            return None
        if isinstance(value, pd.Series):
            value = value.iloc[0]
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    for idx, row in working.iterrows():
        current_date = row["date"]
        if pd.isna(current_date):
            continue

        if row.get("wave_high_point") == "O":
            current_price = _get_price("High", current_date)
            if last_kind == "high" and last_idx is not None and last_price is not None and current_price is not None:
                if current_price >= last_price:
                    working.at[last_idx, "wave_high_point"] = ""
                    last_idx = idx
                    last_price = current_price
                else:
                    working.at[idx, "wave_high_point"] = ""
            else:
                last_kind = "high"
                last_idx = idx
                last_price = current_price

        if row.get("wave_low_point") == "O":
            current_price = _get_price("Low", current_date)
            if last_kind == "low" and last_idx is not None and last_price is not None and current_price is not None:
                if current_price <= last_price:
                    working.at[last_idx, "wave_low_point"] = ""
                    last_idx = idx
                    last_price = current_price
                else:
                    working.at[idx, "wave_low_point"] = ""
            else:
                last_kind = "low"
                last_idx = idx
                last_price = current_price

    # Re-score highs/lows to prefer more extreme turning points between opposite waves
    working["date_ts"] = working["date"]

    def _relocate_wave(kind: str, current_idx: int, target_date: pd.Timestamp) -> int:
        if pd.isna(target_date):
            return current_idx
        if kind == "high":
            working.at[current_idx, "wave_high_point"] = ""
        else:
            working.at[current_idx, "wave_low_point"] = ""

        match_idx = working.index[working["date_ts"] == target_date]
        if len(match_idx) == 0:
            # Ensure the row exists by appending a blank record (rare but defensive)
            new_record = {
                "date": target_date,
                "wave_high_point": "O" if kind == "high" else "",
                "wave_low_point": "O" if kind == "low" else "",
                "trend": None,
                "date_ts": target_date,
            }
            working.loc[len(working)] = new_record
            working.sort_values("date_ts", inplace=True, ignore_index=True)
            return int(working.index[working["date_ts"] == target_date][0])

        target_idx = int(match_idx[0])
        if kind == "high":
            working.at[target_idx, "wave_high_point"] = "O"
        else:
            working.at[target_idx, "wave_low_point"] = "O"
        return target_idx

    ordered_points: list[tuple[str, int]] = []
    for idx, row in working.iterrows():
        if row.get("wave_high_point") == "O":
            ordered_points.append(("high", idx))
        elif row.get("wave_low_point") == "O":
            ordered_points.append(("low", idx))

    price_data_sorted = price_data.sort_index()

    for i, (kind, idx_pos) in enumerate(ordered_points):
        current_date = working.at[idx_pos, "date_ts"]
        if pd.isna(current_date):
            continue

        prev_boundary = None
        next_boundary = None

        if kind == "high":
            for j in range(i - 1, -1, -1):
                if ordered_points[j][0] == "low":
                    prev_boundary = working.at[ordered_points[j][1], "date_ts"]
                    break
            for j in range(i + 1, len(ordered_points)):
                if ordered_points[j][0] == "low":
                    next_boundary = working.at[ordered_points[j][1], "date_ts"]
                    break

            mask = pd.Series(True, index=price_data_sorted.index)
            if prev_boundary is not None:
                mask &= pd.Series(price_data_sorted.index > prev_boundary, index=price_data_sorted.index)
            if next_boundary is not None:
                mask &= pd.Series(price_data_sorted.index < next_boundary, index=price_data_sorted.index)

            if "turning_high_point" in price_data_sorted.columns:
                mask &= price_data_sorted["turning_high_point"] == "O"

            if mask.any():
                candidates = price_data_sorted.loc[mask]
                if not candidates.empty:
                    best_idx = candidates["High"].astype(float).idxmax()
                    if pd.notna(best_idx) and best_idx != current_date:
                        new_idx_pos = _relocate_wave("high", idx_pos, best_idx)
                        ordered_points[i] = ("high", new_idx_pos)

        else:  # kind == "low"
            for j in range(i - 1, -1, -1):
                if ordered_points[j][0] == "high":
                    prev_boundary = working.at[ordered_points[j][1], "date_ts"]
                    break
            for j in range(i + 1, len(ordered_points)):
                if ordered_points[j][0] == "high":
                    next_boundary = working.at[ordered_points[j][1], "date_ts"]
                    break

            mask = pd.Series(True, index=price_data_sorted.index)
            if prev_boundary is not None:
                mask &= pd.Series(price_data_sorted.index > prev_boundary, index=price_data_sorted.index)
            if next_boundary is not None:
                mask &= pd.Series(price_data_sorted.index <= next_boundary, index=price_data_sorted.index)

            if "turning_low_point" in price_data_sorted.columns:
                mask &= price_data_sorted["turning_low_point"] == "O"

            if mask.any():
                candidates = price_data_sorted.loc[mask]
                if not candidates.empty:
                    best_idx = candidates["Low"].astype(float).idxmin()
                    if pd.notna(best_idx) and best_idx != current_date:
                        new_idx_pos = _relocate_wave("low", idx_pos, best_idx)
                        ordered_points[i] = ("low", new_idx_pos)

    working.sort_values("date_ts", inplace=True, ignore_index=True)
    working["date"] = working["date_ts"].dt.strftime("%Y-%m-%d")
    working = working.drop(columns=["date_ts"])
    return working


def identify_wave_points(df: pd.DataFrame) -> pd.DataFrame:
    """識別波段高低點。基於 turning_point_identification 的輸出。"""
    if df is None or df.empty:
        return pd.DataFrame(columns=['date', 'wave_high_point', 'wave_low_point', 'trend'])

    working_df = df.copy().sort_index()
    if not isinstance(working_df.index, pd.DatetimeIndex):
        working_df.index = pd.to_datetime(working_df.index, errors='coerce')
    working_df = working_df.dropna(subset=['Close'])

    results: list[dict] = []
    record_lookup: dict[pd.Timestamp, dict] = {}

    current_trend: str | None = None

    # 追蹤轉折序列
    high_points: list[tuple[pd.Timestamp, float]] = []
    low_points: list[tuple[pd.Timestamp, float]] = []

    # 各階段累積的轉折點
    uptrend_high_points: list[tuple[pd.Timestamp, float]] = []
    downtrend_low_points: list[tuple[pd.Timestamp, float]] = []
    consolidation_high_points: list[tuple[pd.Timestamp, float]] = []
    consolidation_low_points: list[tuple[pd.Timestamp, float]] = []
    trend_before_consolidation_high_points: list[tuple[pd.Timestamp, float]] = []
    trend_before_consolidation_low_points: list[tuple[pd.Timestamp, float]] = []

    # 頭頭低 / 底底高 尚待確認的候選
    pending_downtrend_high: dict | None = None
    pending_uptrend_low: dict | None = None

    wave_high_dates: set[pd.Timestamp] = set()
    wave_low_dates: set[pd.Timestamp] = set()

    def ensure_record(ts: pd.Timestamp) -> dict:
        record = record_lookup.get(ts)
        if record is None:
            record = {
                'date': ts.strftime('%Y-%m-%d'),
                'wave_high_point': '',
                'wave_low_point': '',
                'trend': current_trend
            }
            record_lookup[ts] = record
            results.append(record)
        return record

    def promote_wave(ts: pd.Timestamp, kind: str):
        record = ensure_record(ts)
        if kind == 'high':
            record['wave_high_point'] = 'O'
            wave_high_dates.add(ts)
        else:
            record['wave_low_point'] = 'O'
            wave_low_dates.add(ts)

    for idx, row in working_df.iterrows():
        if pd.isna(idx):
            continue
        date_str = idx.strftime('%Y-%m-%d')

        if row.get('turning_high_point') == 'O':
            high_points.append((idx, row['High']))
            if current_trend == 'up':
                uptrend_high_points.append((idx, row['High']))
            elif current_trend == 'consolidation':
                consolidation_high_points.append((idx, row['High']))

            if len(high_points) >= 2 and low_points:
                prev_high = high_points[-2]
                last_high = high_points[-1]
                support_low = low_points[-1]
                if last_high[1] < prev_high[1]:
                    pending_downtrend_high = {
                        'pivot': prev_high,
                        'support': support_low
                    }

        if row.get('turning_low_point') == 'O':
            low_points.append((idx, row['Low']))
            if current_trend == 'down':
                downtrend_low_points.append((idx, row['Low']))
            elif current_trend == 'consolidation':
                consolidation_low_points.append((idx, row['Low']))

            if len(low_points) >= 2 and high_points:
                prev_low = low_points[-2]
                last_low = low_points[-1]
                resistance_high = high_points[-1]
                if last_low[1] > prev_low[1]:
                    pending_uptrend_low = {
                        'pivot': prev_low,
                        'resistance': resistance_high
                    }

        # 先處理尚未完成的新趨勢候選（頭頭低 / 底底高）
        if pending_downtrend_high is not None:
            support_dt, support_value = pending_downtrend_high['support']
            curr_low = row.get('Low')
            if pd.notna(curr_low) and curr_low < support_value:
                pivot_dt, _ = pending_downtrend_high['pivot']
                if pivot_dt not in wave_high_dates:
                    promote_wave(pivot_dt, 'high')
                current_trend = 'down'
                downtrend_low_points = []
                pending_downtrend_high = None
                consolidation_high_points.clear()
                consolidation_low_points.clear()
                trend_before_consolidation_high_points.clear()
                trend_before_consolidation_low_points.clear()

        if pending_uptrend_low is not None:
            resistance_dt, resistance_value = pending_uptrend_low['resistance']
            curr_high = row.get('High')
            if pd.notna(curr_high) and curr_high > resistance_value:
                pivot_dt, _ = pending_uptrend_low['pivot']
                if pivot_dt not in wave_low_dates:
                    promote_wave(pivot_dt, 'low')
                current_trend = 'up'
                uptrend_high_points = []
                pending_uptrend_low = None
                consolidation_high_points.clear()
                consolidation_low_points.clear()
                trend_before_consolidation_high_points.clear()
                trend_before_consolidation_low_points.clear()

        new_trend = current_trend
        if len(high_points) >= 2 and len(low_points) >= 2:
            high1_val = high_points[-2][1]
            high2_val = high_points[-1][1]
            low1_val = low_points[-2][1]
            low2_val = low_points[-1][1]
            if high2_val > high1_val and low2_val > low1_val:
                new_trend = 'up'
            elif high2_val < high1_val and low2_val < low1_val:
                new_trend = 'down'
            else:
                new_trend = 'consolidation'
        else:
            new_trend = current_trend

        if current_trend == 'up' and new_trend != 'up':
            candidate_high = None
            if len(high_points) >= 2:
                prev_high = high_points[-2]
                last_high = high_points[-1]
                if last_high[1] < prev_high[1]:
                    candidate_high = prev_high
            if candidate_high is None and uptrend_high_points:
                candidate_high = max(uptrend_high_points, key=lambda x: x[1])
            if candidate_high is None and high_points:
                candidate_high = max(high_points, key=lambda x: x[1])
            if candidate_high is not None and candidate_high[0] not in wave_high_dates:
                promote_wave(candidate_high[0], 'high')
            if new_trend == 'consolidation':
                trend_before_consolidation_high_points = uptrend_high_points.copy()
            pending_downtrend_high = None
            uptrend_high_points = []

        if current_trend == 'down' and new_trend != 'down':
            candidate_low = None
            if len(low_points) >= 2:
                prev_low = low_points[-2]
                last_low = low_points[-1]
                if last_low[1] > prev_low[1]:
                    candidate_low = prev_low
            if candidate_low is None and downtrend_low_points:
                candidate_low = min(downtrend_low_points, key=lambda x: x[1])
            if candidate_low is None and low_points:
                candidate_low = min(low_points, key=lambda x: x[1])
            if candidate_low is not None and candidate_low[0] not in wave_low_dates:
                promote_wave(candidate_low[0], 'low')
            if new_trend == 'consolidation':
                trend_before_consolidation_low_points = downtrend_low_points.copy()
                if (not trend_before_consolidation_low_points) and low_points:
                    trend_before_consolidation_low_points = [low_points[-1]]
            pending_uptrend_low = None
            downtrend_low_points = []

        if current_trend == 'consolidation' and new_trend != 'consolidation':
            if new_trend == 'down':
                candidates = []
                candidates.extend(trend_before_consolidation_high_points)
                candidates.extend(consolidation_high_points)
                if len(high_points) >= 1:
                    candidates.append(high_points[-1])
                if candidates:
                    pivot_dt, _ = max(candidates, key=lambda x: x[1])
                    if pivot_dt not in wave_high_dates:
                        promote_wave(pivot_dt, 'high')
                pending_downtrend_high = None
                downtrend_low_points = list(consolidation_low_points)
            elif new_trend == 'up':
                candidates = []
                candidates.extend(trend_before_consolidation_low_points)
                candidates.extend(consolidation_low_points)
                if len(low_points) >= 1:
                    candidates.append(low_points[-1])
                if candidates:
                    pivot_dt, _ = min(candidates, key=lambda x: x[1])
                    if pivot_dt not in wave_low_dates:
                        promote_wave(pivot_dt, 'low')
                pending_uptrend_low = None
                uptrend_high_points = list(consolidation_high_points)
            consolidation_high_points = []
            consolidation_low_points = []
            trend_before_consolidation_high_points = []
            trend_before_consolidation_low_points = []

        current_trend = new_trend
        record = ensure_record(idx)
        record['trend'] = current_trend

    result_df = pd.DataFrame(results).sort_values('date')
    result_df = _remove_consecutive_wave_points(result_df, working_df)
    return result_df

def check_wave_points(df: pd.DataFrame) -> pd.DataFrame:
    """
    檢查股價的波段高低點（對外接口）。
    
    Args:
        df (pd.DataFrame): 包含K線數據和轉折點的DataFrame，需要包含：
                          'Close', 'High', 'Low', 'turning_high_point', 'turning_low_point'
    
    Returns:
        pd.DataFrame: 包含 'date', 'wave_high_point', 'wave_low_point', 'trend' 列的DataFrame。
    """
    return identify_wave_points(df)


if __name__ == "__main__":
    # 測試用例
    import matplotlib.pyplot as plt
    from turning_point_identification import check_turning_points
    
    # 創建測試數據
    dates = pd.date_range(start='2023-01-01', periods=200)
    
    # 生成模擬的波段行情：上升 → 盤整 → 下降 → 盤整 → 上升
    close_prices = []
    high_prices = []
    low_prices = []
    
    base_price = 100
    for i in range(200):
        if i < 50:  # 上升段
            trend = 0.5
        elif i < 80:  # 盤整段
            trend = 0
        elif i < 130:  # 下降段
            trend = -0.4
        elif i < 160:  # 盤整段
            trend = 0
        else:  # 上升段
            trend = 0.6
        
        noise = np.random.normal(0, 1.5)
        base_price += trend + noise
        
        close_prices.append(base_price)
        high_prices.append(base_price + abs(np.random.normal(1, 0.5)))
        low_prices.append(base_price - abs(np.random.normal(1, 0.5)))
    
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
    
    # 合併轉折點
    test_df = pd.merge(
        test_df.reset_index(),
        turning_points,
        left_on='index',
        right_on='date',
        how='left'
    ).set_index('index')
    
    # 識別波段點
    wave_points = check_wave_points(test_df)
    
    # 合併波段點
    result_df = pd.merge(
        test_df.reset_index(),
        wave_points,
        left_on='date',
        right_on='date',
        how='left'
    )
    
    # 繪製圖表
    plt.figure(figsize=(20, 10))
    
    # 繪製價格和均線
    plt.plot(result_df['index'], result_df['Close'], label='Close Price', linewidth=1)
    plt.plot(result_df['index'], result_df['ma5'], label='5-day MA', linewidth=1, alpha=0.7)
    
    # 標記轉折高點（紅色小三角）
    turning_highs = result_df[result_df['turning_high_point'] == 'O']
    plt.scatter(turning_highs['index'], turning_highs['High'], 
                color='red', marker='^', s=50, label='Turning High Points', alpha=0.6)
    
    # 標記轉折低點（綠色小三角）
    turning_lows = result_df[result_df['turning_low_point'] == 'O']
    plt.scatter(turning_lows['index'], turning_lows['Low'], 
                color='green', marker='v', s=50, label='Turning Low Points', alpha=0.6)
    
    # 標記波段高點（紅色大星星）
    wave_highs = result_df[result_df['wave_high_point'] == 'O']
    plt.scatter(wave_highs['index'], wave_highs['High'], 
                color='darkred', marker='*', s=300, label='Wave High Points', 
                edgecolors='black', linewidths=1.5, zorder=5)
    
    # 標記波段低點（綠色大星星）
    wave_lows = result_df[result_df['wave_low_point'] == 'O']
    plt.scatter(wave_lows['index'], wave_lows['Low'], 
                color='darkgreen', marker='*', s=300, label='Wave Low Points',
                edgecolors='black', linewidths=1.5, zorder=5)
    
    plt.title('Price with Turning Points and Wave Points', fontsize=16)
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend(loc='best')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    # 輸出統計信息
    print("\n=== 波段識別統計 ===")
    print(f"轉折高點數量: {len(turning_highs)}")
    print(f"轉折低點數量: {len(turning_lows)}")
    print(f"波段高點數量: {len(wave_highs)}")
    print(f"波段低點數量: {len(wave_lows)}")
    print(f"\n最終趨勢狀態: {result_df['trend'].iloc[-1]}")
