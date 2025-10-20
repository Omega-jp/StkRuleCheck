#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
波段高低點算法執行過程診斷程式
逐步追蹤 wave_point_identification.py 的執行邏輯
"""

import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


_configured_font_family = None
_registered_wave_fonts = False


def _register_wave_fonts():
    """Register bundled CJK fonts so matplotlib can render labels without warnings."""
    global _registered_wave_fonts
    if _registered_wave_fonts:
        return

    local_font_paths = [
        os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'NotoSansCJKtc-Regular.otf'),
    ]

    for font_path in local_font_paths:
        if os.path.isfile(font_path):
            font_manager.fontManager.addfont(font_path)

    _registered_wave_fonts = True


def _wave_font_available(font_family: str) -> bool:
    """Check whether matplotlib can resolve the given font family."""
    try:
        prop = font_manager.FontProperties(family=font_family)
        font_manager.findfont(prop, fallback_to_default=False)
        return True
    except (ValueError, RuntimeError):
        return False


def _ensure_wave_plot_fonts():
    """Select a usable sans-serif font that supports zh-TW characters."""
    global _configured_font_family
    if _configured_font_family:
        return _configured_font_family

    _register_wave_fonts()

    preferred_order = [
        'Microsoft JhengHei',
        'Arial Unicode MS',
        'SimHei',
        'Noto Sans CJK TC',
        'Noto Sans CJK SC',
        'PingFang TC',
        'PingFang SC',
        'Heiti TC',
        'Heiti SC',
        'STHeiti',
        'WenQuanYi Zen Hei',
        'Source Han Sans TC',
        'Source Han Sans SC',
        'DejaVu Sans',
    ]

    for family in preferred_order:
        if _wave_font_available(family):
            plt.rcParams['font.sans-serif'] = [family]
            _configured_font_family = family
            break
    else:
        default_family = plt.rcParams.get('font.sans-serif', ['DejaVu Sans'])
        _configured_font_family = default_family[0] if default_family else 'DejaVu Sans'

    plt.rcParams['axes.unicode_minus'] = False
    return _configured_font_family


def debug_wave_point_execution(stock_id='2330', days=120):
    """
    逐步追蹤波段高低點識別算法的執行過程
    """
    print(f"\n{'='*80}")
    print(f"波段高低點算法執行過程診斷：{stock_id}")
    print(f"{'='*80}")
    
    try:
        # 導入必要模塊
        from src.validate_buy_rule import load_stock_data
        from src.baseRule.turning_point_identification import identify_turning_points
        
        # 載入數據
        print("🔄 載入股票數據...")
        df = load_stock_data(stock_id, 'D')
        if df is None:
            print(f"❌ 無法載入股票 {stock_id} 的數據")
            return False
        
        # 確保有ma5欄位
        if 'ma5' not in df.columns:
            df['ma5'] = df['Close'].rolling(window=5, min_periods=1).mean()
        
        # 取最近的數據
        recent_df = df.tail(days).copy()
        print(f"📊 分析最近 {len(recent_df)} 天的數據")
        print(f"   數據範圍：{recent_df.index[0].strftime('%Y-%m-%d')} 到 {recent_df.index[-1].strftime('%Y-%m-%d')}")
        
        # 步驟1：先識別轉折點
        print(f"\n🔍 步驟1：識別轉折高低點")
        turning_points_df = identify_turning_points(recent_df)
        # Align merge keys by ensuring datetime dtype consistency
        turning_points_df = turning_points_df.copy()
        turning_points_df['date'] = pd.to_datetime(turning_points_df['date'], errors='coerce')
        
        # 🔧 修正：正確處理索引名稱
        # 重置索引並保存原索引名稱
        recent_df_reset = recent_df.reset_index()
        index_col_name = recent_df_reset.columns[0]  # 獲取索引列的名稱
        recent_df_reset[index_col_name] = pd.to_datetime(recent_df_reset[index_col_name], errors='coerce')
        
        # 合併轉折點到原始數據
        recent_df = pd.merge(
            recent_df_reset,
            turning_points_df,
            left_on=index_col_name,
            right_on='date',
            how='left'
        ).set_index(index_col_name)
        
        # 收集轉折點
        turning_high_points = recent_df[recent_df['turning_high_point'] == 'O']
        turning_low_points = recent_df[recent_df['turning_low_point'] == 'O']
        
        print(f"   ✓ 轉折高點數量：{len(turning_high_points)}")
        print(f"   ✓ 轉折低點數量：{len(turning_low_points)}")
        
        print(f"\n   轉折高點列表：")
        for i, (date, row) in enumerate(turning_high_points.iterrows()):
            print(f"     {i+1:2d}. {date.strftime('%Y-%m-%d')}: {row['High']:7.2f}")
        
        print(f"\n   轉折低點列表：")
        for i, (date, row) in enumerate(turning_low_points.iterrows()):
            print(f"     {i+1:2d}. {date.strftime('%Y-%m-%d')}: {row['Low']:7.2f}")
        
        # 步驟2：手動執行波段識別算法
        print(f"\n{'='*80}")
        print(f"🔍 步驟2：手動執行波段高低點識別算法")
        print(f"{'='*80}")
        
        # 建立轉折點序列
        high_points = []  # [(date, price, index), ...]
        low_points = []   # [(date, price, index), ...]
        
        for i, (date, row) in enumerate(recent_df.iterrows()):
            if row.get('turning_high_point') == 'O':
                high_points.append((date, row['High'], i))
            if row.get('turning_low_point') == 'O':
                low_points.append((date, row['Low'], i))
        
        print(f"\n2.1 收集轉折點序列")
        print(f"    轉折高點：{len(high_points)} 個")
        print(f"    轉折低點：{len(low_points)} 個")
        
        # 手動執行趨勢判定邏輯
        print(f"\n2.2 逐步判定趨勢變化")
        
        current_trend = None
        prev_trend = None
        trend_history = []
        wave_points_identified = []
        
        # 用於記錄波段期間的轉折點
        uptrend_high_points = []
        downtrend_low_points = []
        consolidation_high_points = []
        consolidation_low_points = []
        trend_before_consolidation_high_points = []
        trend_before_consolidation_low_points = []
        
        # 逐日遍歷
        for i, (date, row) in enumerate(recent_df.iterrows()):
            date_str = date.strftime('%Y-%m-%d')
            
            # 收集轉折點
            if row.get('turning_high_point') == 'O':
                if current_trend == 'up':
                    uptrend_high_points.append((date, row['High'], i))
                elif current_trend == 'consolidation':
                    consolidation_high_points.append((date, row['High'], i))
            
            if row.get('turning_low_point') == 'O':
                if current_trend == 'down':
                    downtrend_low_points.append((date, row['Low'], i))
                elif current_trend == 'consolidation':
                    consolidation_low_points.append((date, row['Low'], i))
            
            # 判斷趨勢
            if len(high_points) >= 2 and len(low_points) >= 2:
                高1 = high_points[-2][1]
                高2 = high_points[-1][1]
                低1 = low_points[-2][1]
                低2 = low_points[-1][1]
                
                # 計算新趨勢
                new_trend = None
                if 高2 > 高1 and 低2 > 低1:
                    new_trend = 'up'
                elif 高2 < 高1 and 低2 < 低1:
                    new_trend = 'down'
                else:
                    new_trend = 'consolidation'
                
                # 檢測趨勢變化
                if new_trend != current_trend:
                    trend_change_info = {
                        'date': date_str,
                        'from': current_trend,
                        'to': new_trend,
                        'high1': 高1,
                        'high2': 高2,
                        'low1': 低1,
                        'low2': 低2
                    }
                    
                    print(f"\n    📍 {date_str}: 趨勢變化 [{current_trend or 'None'} → {new_trend}]")
                    print(f"       高點比較: {高1:.2f} → {高2:.2f} ({'↑' if 高2 > 高1 else '↓' if 高2 < 高1 else '='} {abs(高2-高1):.2f})")
                    print(f"       低點比較: {低1:.2f} → {低2:.2f} ({'↑' if 低2 > 低1 else '↓' if 低2 < 低1 else '='} {abs(低2-低1):.2f})")
                    
                    # 處理波段點標記
                    wave_marked = []
                    
                    # === 上升波段結束 ===
                    if current_trend == 'up' and new_trend != 'up':
                        if uptrend_high_points:
                            max_high = max(uptrend_high_points, key=lambda x: x[1])
                            wave_marked.append(('high', max_high[0], max_high[1]))
                            print(f"       🔺 標記波段高點: {max_high[0].strftime('%Y-%m-%d')} ({max_high[1]:.2f})")
                            
                            if new_trend == 'consolidation':
                                trend_before_consolidation_high_points = uptrend_high_points.copy()
                                print(f"       📦 保存上升波段高點 ({len(uptrend_high_points)}個) 供盤整後使用")
                        
                        uptrend_high_points = []
                    
                    # === 下降波段結束 ===
                    if current_trend == 'down' and new_trend != 'down':
                        if downtrend_low_points:
                            min_low = min(downtrend_low_points, key=lambda x: x[1])
                            wave_marked.append(('low', min_low[0], min_low[1]))
                            print(f"       🔻 標記波段低點: {min_low[0].strftime('%Y-%m-%d')} ({min_low[1]:.2f})")
                            
                            if new_trend == 'consolidation':
                                trend_before_consolidation_low_points = downtrend_low_points.copy()
                                print(f"       📦 保存下降波段低點 ({len(downtrend_low_points)}個) 供盤整後使用")
                        
                        downtrend_low_points = []
                    
                    # === 盤整結束 ===
                    if current_trend == 'consolidation' and new_trend != 'consolidation':
                        print(f"       📊 盤整結束，前趨勢: {prev_trend}")
                        
                        # 情境A：下降 → 盤整 → 下降
                        if prev_trend == 'down' and new_trend == 'down':
                            if consolidation_high_points:
                                max_high = max(consolidation_high_points, key=lambda x: x[1])
                                wave_marked.append(('high', max_high[0], max_high[1]))
                                print(f"       🔺 標記盤整反彈高點: {max_high[0].strftime('%Y-%m-%d')} ({max_high[1]:.2f})")
                        
                        # 情境B：上升 → 盤整 → 上升
                        elif prev_trend == 'up' and new_trend == 'up':
                            if consolidation_low_points:
                                min_low = min(consolidation_low_points, key=lambda x: x[1])
                                wave_marked.append(('low', min_low[0], min_low[1]))
                                print(f"       🔻 標記盤整回檔低點: {min_low[0].strftime('%Y-%m-%d')} ({min_low[1]:.2f})")
                        
                        # 情境C：下降 → 盤整 → 上升（趨勢反轉）
                        elif prev_trend == 'down' and new_trend == 'up':
                            all_low_points = trend_before_consolidation_low_points + consolidation_low_points
                            if all_low_points:
                                min_low = min(all_low_points, key=lambda x: x[1])
                                wave_marked.append(('low', min_low[0], min_low[1]))
                                print(f"       🔻 標記新上升起始低點: {min_low[0].strftime('%Y-%m-%d')} ({min_low[1]:.2f})")
                                print(f"          (合併 {len(trend_before_consolidation_low_points)}個下降波段點 + {len(consolidation_low_points)}個盤整點)")
                        
                        # 情境D：上升 → 盤整 → 下降（趨勢反轉）
                        elif prev_trend == 'up' and new_trend == 'down':
                            all_high_points = trend_before_consolidation_high_points + consolidation_high_points
                            if all_high_points:
                                max_high = max(all_high_points, key=lambda x: x[1])
                                wave_marked.append(('high', max_high[0], max_high[1]))
                                print(f"       🔺 標記新下降起始高點: {max_high[0].strftime('%Y-%m-%d')} ({max_high[1]:.2f})")
                                print(f"          (合併 {len(trend_before_consolidation_high_points)}個上升波段點 + {len(consolidation_high_points)}個盤整點)")
                        
                        # 清空盤整記錄
                        consolidation_high_points = []
                        consolidation_low_points = []
                        trend_before_consolidation_high_points = []
                        trend_before_consolidation_low_points = []
                    
                    # 記錄趨勢變化和標記的波段點
                    trend_change_info['wave_marked'] = wave_marked
                    trend_history.append(trend_change_info)
                    wave_points_identified.extend(wave_marked)
                    
                    # 進入新趨勢
                    if new_trend == 'up' and current_trend != 'up':
                        uptrend_high_points = []
                        if row.get('turning_high_point') == 'O':
                            uptrend_high_points.append((date, row['High'], i))
                    
                    if new_trend == 'down' and current_trend != 'down':
                        downtrend_low_points = []
                        if row.get('turning_low_point') == 'O':
                            downtrend_low_points.append((date, row['Low'], i))
                    
                    if new_trend == 'consolidation' and current_trend != 'consolidation':
                        prev_trend = current_trend
                        consolidation_high_points = []
                        consolidation_low_points = []
                        if row.get('turning_high_point') == 'O':
                            consolidation_high_points.append((date, row['High'], i))
                        if row.get('turning_low_point') == 'O':
                            consolidation_low_points.append((date, row['Low'], i))
                    
                    current_trend = new_trend
        
        # 處理結尾
        print(f"\n2.3 處理數據結尾")
        print(f"    最終趨勢: {current_trend}")
        
        if current_trend == 'up' and uptrend_high_points:
            max_high = max(uptrend_high_points, key=lambda x: x[1])
            wave_points_identified.append(('high', max_high[0], max_high[1]))
            print(f"    🔺 標記最終波段高點: {max_high[0].strftime('%Y-%m-%d')} ({max_high[1]:.2f})")
        
        if current_trend == 'down' and downtrend_low_points:
            min_low = min(downtrend_low_points, key=lambda x: x[1])
            wave_points_identified.append(('low', min_low[0], min_low[1]))
            print(f"    🔻 標記最終波段低點: {min_low[0].strftime('%Y-%m-%d')} ({min_low[1]:.2f})")
        
        # 步驟3：總結手動識別結果
        print(f"\n{'='*80}")
        print(f"📋 步驟3：手動識別結果總結")
        print(f"{'='*80}")
        
        wave_high_points = [wp for wp in wave_points_identified if wp[0] == 'high']
        wave_low_points = [wp for wp in wave_points_identified if wp[0] == 'low']
        
        print(f"\n總共識別 {len(wave_points_identified)} 個波段點：")
        print(f"  • 波段高點：{len(wave_high_points)} 個")
        print(f"  • 波段低點：{len(wave_low_points)} 個")
        
        print(f"\n波段高點列表：")
        for i, (_, date, price) in enumerate(wave_high_points):
            print(f"  {i+1:2d}. {date.strftime('%Y-%m-%d')}: {price:7.2f}")
        
        print(f"\n波段低點列表：")
        for i, (_, date, price) in enumerate(wave_low_points):
            print(f"  {i+1:2d}. {date.strftime('%Y-%m-%d')}: {price:7.2f}")
        
        # 步驟4：趨勢變化時間軸
        print(f"\n{'='*80}")
        print(f"📈 步驟4：趨勢變化時間軸")
        print(f"{'='*80}")
        
        for i, change in enumerate(trend_history):
            print(f"\n{i+1}. {change['date']}: [{change['from']} → {change['to']}]")
            print(f"   高點: {change['high1']:.2f} → {change['high2']:.2f}")
            print(f"   低點: {change['low1']:.2f} → {change['low2']:.2f}")
            if change.get('wave_marked'):
                print(f"   標記波段點:")
                for point_type, point_date, point_price in change['wave_marked']:
                    symbol = "🔺" if point_type == 'high' else "🔻"
                    print(f"     {symbol} {point_type}: {point_date.strftime('%Y-%m-%d')} ({point_price:.2f})")
        
        # 步驟5：與原始算法比較
        print(f"\n{'='*80}")
        print(f"🔄 步驟5：與原始算法結果比較")
        print(f"{'='*80}")
        
        try:
            from src.baseRule.wave_point_identification import identify_wave_points
            
            original_result = identify_wave_points(recent_df)
            
            # 🔧 修正：使用 date 欄位進行合併
            recent_df_for_merge = recent_df.reset_index()
            recent_df_for_merge['date_merge'] = recent_df_for_merge[index_col_name].dt.strftime('%Y-%m-%d')
            
            merged_result = pd.merge(
                recent_df_for_merge,
                original_result,
                left_on='date_merge',
                right_on='date',
                how='left',
                suffixes=('', '_wave')
            ).set_index(index_col_name)
            
            recent_df = merged_result
            
            orig_wave_highs = original_result[original_result['wave_high_point'] == 'O']
            orig_wave_lows = original_result[original_result['wave_low_point'] == 'O']
            
            print(f"\n原始算法結果：")
            print(f"  • 波段高點：{len(orig_wave_highs)} 個")
            print(f"  • 波段低點：{len(orig_wave_lows)} 個")
            
            # 比較結果
            manual_high_dates = set([wp[1].strftime('%Y-%m-%d') for wp in wave_high_points])
            original_high_dates = set(orig_wave_highs['date'].tolist())
            
            manual_low_dates = set([wp[1].strftime('%Y-%m-%d') for wp in wave_low_points])
            original_low_dates = set(orig_wave_lows['date'].tolist())
            
            missing_highs = manual_high_dates - original_high_dates
            extra_highs = original_high_dates - manual_high_dates
            
            missing_lows = manual_low_dates - original_low_dates
            extra_lows = original_low_dates - manual_low_dates
            
            if missing_highs:
                print(f"\n⚠️ 原始算法遺漏的波段高點：{missing_highs}")
            if extra_highs:
                print(f"\n⚠️ 原始算法多出的波段高點：{extra_highs}")
            if missing_lows:
                print(f"\n⚠️ 原始算法遺漏的波段低點：{missing_lows}")
            if extra_lows:
                print(f"\n⚠️ 原始算法多出的波段低點：{extra_lows}")
            
            if not any([missing_highs, extra_highs, missing_lows, extra_lows]):
                print(f"\n✅ 手動執行結果與原始算法完全一致！")
            
        except Exception as e:
            print(f"\n❌ 無法載入原始算法進行比較：{e}")
            import traceback
            traceback.print_exc()
        
        # 創建診斷圖表
        create_wave_debug_chart(stock_id, recent_df, trend_history, wave_points_identified)
        
        return True
        
    except Exception as e:
        print(f"❌ 診斷過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


def _enforce_wave_alternation(points):
    ordered = sorted(points, key=lambda x: x[1])
    filtered = []
    for kind, date, price in ordered:
        if not filtered:
            filtered.append((kind, date, price))
            continue
        last_kind, last_date, last_price = filtered[-1]
        if kind == last_kind:
            if kind == 'high':
                if price >= last_price:
                    filtered[-1] = (kind, date, price)
            else:
                if price <= last_price:
                    filtered[-1] = (kind, date, price)
            continue
        filtered.append((kind, date, price))
    return filtered

def create_wave_debug_chart(stock_id, recent_df, trend_history, wave_points_identified):
    """
    創建波段診斷圖表
    """
    try:
        chosen_font = _ensure_wave_plot_fonts()
        plt.figure(figsize=(20, 12))
        if chosen_font not in plt.rcParams.get('font.sans-serif', []):
            plt.rcParams['font.sans-serif'] = [chosen_font]
        
        # === 主圖：K線 + 轉折點 + 波段點 ===
        plt.subplot(2, 1, 1)
        dates = recent_df.index
        
        # 繪製K棒
        for i, date in enumerate(dates):
            row = recent_df.loc[date]
            open_price = row['Open']
            high_price = row['High']
            low_price = row['Low']
            close_price = row['Close']
            
            is_up = close_price >= open_price
            
            # 上下影線
            plt.plot([date, date], [low_price, high_price], 
                    color='black', linewidth=0.6, alpha=0.6)
            
            # K棒實體
            body_height = abs(close_price - open_price)
            body_bottom = min(open_price, close_price)
            bar_width = pd.Timedelta(days=0.6)
            
            if is_up:
                rect = plt.Rectangle((date - bar_width/2, body_bottom), 
                                   bar_width, body_height, 
                                   facecolor='white', edgecolor='red', 
                                   linewidth=1, alpha=0.8)
            else:
                rect = plt.Rectangle((date - bar_width/2, body_bottom), 
                                   bar_width, body_height, 
                                   facecolor='green', edgecolor='green', 
                                   linewidth=1, alpha=0.8)
            
            plt.gca().add_patch(rect)
        
        # 繪製MA5
        plt.plot(dates, recent_df['ma5'], 
                color='blue', linewidth=1.5, linestyle='-', 
                alpha=0.7, label='5MA', zorder=5)
        
        # 標記轉折高點（小紅三角）
        turning_highs = recent_df[recent_df['turning_high_point'] == 'O']
        if len(turning_highs) > 0:
            plt.scatter(turning_highs.index, turning_highs['High'],
                       facecolors='none', edgecolors='red', marker='^', s=90,
                       linewidths=1.2, label='轉折高點', zorder=10)

        # 標記轉折低點（小綠三角）
        turning_lows = recent_df[recent_df['turning_low_point'] == 'O']
        if len(turning_lows) > 0:
            plt.scatter(turning_lows.index, turning_lows['Low'],
                       facecolors='none', edgecolors='green', marker='v', s=90,
                       linewidths=1.2, label='轉折低點', zorder=10)

        # 依序連接轉折高低點，呈現波段折線
        turning_sequence = []
        for date, row in recent_df.iterrows():
            if row.get('turning_high_point') == 'O':
                turning_sequence.append(('high', date, row['High']))
            if row.get('turning_low_point') == 'O':
                turning_sequence.append(('low', date, row['Low']))
        if len(turning_sequence) > 1:
            for prev, curr in zip(turning_sequence[:-1], turning_sequence[1:]):
                if prev[0] == curr[0]:
                    continue
                prev_type, prev_date, prev_price = prev
                curr_type, curr_date, curr_price = curr
                segment_dates = [prev_date, curr_date]
                segment_prices = [prev_price, curr_price]
                if prev_type == 'high' and curr_type == 'low':
                    color = 'red'
                elif prev_type == 'low' and curr_type == 'high':
                    color = 'green'
                else:
                    color = 'gray'
                plt.plot(segment_dates, segment_prices,
                        color=color, linestyle=(0, (4, 2)), linewidth=0.9,
                        alpha=0.6, zorder=9, label='_nolegend_')

        # 整理波段高低點（含原始演算法結果）
        wave_points_for_plot: list[tuple[str, pd.Timestamp, float]] = []
        if 'wave_high_point' in recent_df.columns or 'wave_low_point' in recent_df.columns:
            for date, row in recent_df.iterrows():
                date_ts = pd.to_datetime(date) if not isinstance(date, pd.Timestamp) else date
                if row.get('wave_high_point') == 'O':
                    wave_points_for_plot.append(('high', date_ts, float(recent_df.loc[date, 'High'])))
                if row.get('wave_low_point') == 'O':
                    wave_points_for_plot.append(('low', date_ts, float(recent_df.loc[date, 'Low'])))

        if not wave_points_for_plot and wave_points_identified:
            for kind, date, price in wave_points_identified:
                date_ts = pd.to_datetime(date) if not isinstance(date, pd.Timestamp) else date
                wave_points_for_plot.append((kind, date_ts, float(price)))

        wave_points_for_plot.sort(key=lambda x: x[1])
        wave_points_for_plot = _enforce_wave_alternation(wave_points_for_plot)

        wave_high_points = [wp for wp in wave_points_for_plot if wp[0] == 'high']
        if wave_high_points:
            wave_high_dates = [wp[1] for wp in wave_high_points]
            wave_high_prices = [wp[2] for wp in wave_high_points]
            plt.scatter(wave_high_dates, wave_high_prices,
                       color='darkred', marker='*', s=400,
                       label='波段高點', edgecolor='white', linewidth=2, zorder=20)

        wave_low_points = [wp for wp in wave_points_for_plot if wp[0] == 'low']
        if wave_low_points:
            wave_low_dates = [wp[1] for wp in wave_low_points]
            wave_low_prices = [wp[2] for wp in wave_low_points]
            plt.scatter(wave_low_dates, wave_low_prices,
                       color='darkgreen', marker='*', s=400,
                       label='波段低點', edgecolor='white', linewidth=2, zorder=20)

        if len(wave_points_for_plot) > 1:
            wave_line_dates = [wp[1] for wp in wave_points_for_plot]
            wave_line_prices = [wp[2] for wp in wave_points_for_plot]
            plt.plot(wave_line_dates, wave_line_prices,
                    color='darkred', linestyle='-', linewidth=1.3,
                    alpha=0.8, zorder=19, label='波段折線')
        
        plt.title(f'{stock_id} 波段高低點識別診斷圖', fontsize=16, fontweight='bold')
        plt.ylabel('價格', fontsize=12)
        plt.legend(fontsize=10, loc='upper left')
        plt.grid(True, alpha=0.3)
        
        # === 趨勢變化時間軸 ===
        plt.subplot(2, 1, 2)
        
        # 創建趨勢映射
        trend_map = {'up': 1, 'consolidation': 0, 'down': -1, None: 0}
        trend_values = []
        trend_dates = []
        
        current_trend_value = 0
        for date in dates:
            date_str = date.strftime('%Y-%m-%d')
            
            # 檢查是否有趨勢變化
            for change in trend_history:
                if change['date'] == date_str:
                    current_trend_value = trend_map.get(change['to'], 0)
                    break
            
            trend_dates.append(date)
            trend_values.append(current_trend_value)
        
        # 繪製趨勢線
        plt.plot(trend_dates, trend_values, 
                color='purple', linewidth=2, label='趨勢狀態')
        plt.fill_between(trend_dates, 0, trend_values, 
                        alpha=0.3, color='purple')
        
        # 標記趨勢變化點
        for change in trend_history:
            change_date = pd.to_datetime(change['date'])
            if change_date in trend_dates:
                trend_value = trend_map.get(change['to'], 0)
                plt.axvline(x=change_date, color='red', 
                           linestyle='--', alpha=0.5)
                plt.text(change_date, trend_value, 
                        f"{change['from'] or 'None'}→{change['to']}", 
                        rotation=90, fontsize=8, 
                        verticalalignment='bottom')
        
        plt.title('趨勢變化時間軸 (1=上升, 0=盤整, -1=下降)', fontsize=14)
        plt.ylabel('趨勢', fontsize=12)
        plt.xlabel('日期', fontsize=12)
        plt.yticks([-1, 0, 1], ['下降', '盤整', '上升'])
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存圖表
        output_dir = 'output/debug_charts'
        os.makedirs(output_dir, exist_ok=True)
        chart_path = f'{output_dir}/{stock_id}_wave_point_debug.png'
        
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        print(f"\n✅ 診斷圖表已保存至: {chart_path}")
        plt.show()
        
    except Exception as e:
        print(f"❌ 創建診斷圖表時發生錯誤: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主程式"""
    print("波段高低點算法執行過程診斷程式")
    print("=" * 60)
    print("逐步追蹤 wave_point_identification.py 的執行邏輯")
    
    stock_id = input("\n請輸入股票代碼 (預設2330): ").strip() or '2330'
    
    try:
        days_input = input("請輸入分析天數 (預設120天): ").strip()
        days = int(days_input) if days_input else 120
    except ValueError:
        days = 120
    
    print(f"\n開始診斷 {stock_id} 的波段高低點識別算法...")
    
    success = debug_wave_point_execution(stock_id, days)
    
    if success:
        print(f"\n🎉 診斷完成！請檢查控制台輸出和生成的圖表。")
    else:
        print(f"\n❌ 診斷失敗！")


if __name__ == "__main__":
    main()


