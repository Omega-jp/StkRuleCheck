#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
趨勢波偵測診斷程式
測試並診斷 waving_point_identification.py 的執行邏輯
"""

import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
from matplotlib.patches import FancyBboxPatch
from datetime import datetime

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


def debug_waving_point_execution(stock_id='00631L', days=120):
    """
    診斷趨勢波識別算法的執行過程
    """
    print(f"\n{'='*80}")
    print(f"趨勢波偵測診斷：{stock_id}")
    print(f"{'='*80}")
    
    try:
        # 導入必要模塊
        from src.validate_buy_rule import load_stock_data
        from src.baseRule.turning_point_identification import identify_turning_points
        
        # 導入趨勢波識別模組
        sys.path.append(os.path.dirname(__file__))
        from src.baseRule.waving_point_identification import WavingPointIdentifier
        
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
        
        # 步驟1：識別轉折點
        print(f"\n{'='*60}")
        print("步驟1：識別轉折點")
        print(f"{'='*60}")
        
        turning_points_df = identify_turning_points(recent_df)
        
        high_points = turning_points_df[turning_points_df['turning_high_point'] == 'O']
        low_points = turning_points_df[turning_points_df['turning_low_point'] == 'O']
        
        print(f"✅ 轉折高點數量：{len(high_points)}")
        print(f"✅ 轉折低點數量：{len(low_points)}")
        
        print(f"\n轉折點時間序列：")
        all_turning = []
        for _, row in high_points.iterrows():
            date = pd.to_datetime(row['date'])
            price = recent_df.loc[date, 'High']
            all_turning.append((date, 'high', price))
        
        for _, row in low_points.iterrows():
            date = pd.to_datetime(row['date'])
            price = recent_df.loc[date, 'Low']
            all_turning.append((date, 'low', price))
        
        all_turning.sort(key=lambda x: x[0])
        
        for i, (date, tp_type, price) in enumerate(all_turning):
            symbol = "🔺" if tp_type == 'high' else "🔻"
            print(f"  {i+1:2d}. {date.strftime('%Y-%m-%d')} {symbol} {tp_type:4s} (價格: {price:7.2f})")
        
        # 步驟2：識別趨勢波
        print(f"\n{'='*60}")
        print("步驟2：識別趨勢波和波段點")
        print(f"{'='*60}")
        
        identifier = WavingPointIdentifier(debug=True)
        result_df = identifier.identify_waving_points(recent_df, turning_points_df)
        
        # 步驟3：總結結果
        print(f"\n{'='*60}")
        print("步驟3：趨勢波識別結果總結")
        print(f"{'='*60}")
        
        wave_highs = result_df[result_df['wave_high_point'] == 'O']
        wave_lows = result_df[result_df['wave_low_point'] == 'O']
        
        print(f"\n📈 波段高點 ({len(wave_highs)}個)：")
        for i, (_, row) in enumerate(wave_highs.iterrows()):
            date = pd.to_datetime(row['date'])
            price = recent_df.loc[date, 'High']
            print(f"  {i+1}. {row['date']} - 價格: {price:.2f}")
        
        print(f"\n📉 波段低點 ({len(wave_lows)}個)：")
        for i, (_, row) in enumerate(wave_lows.iterrows()):
            date = pd.to_datetime(row['date'])
            price = recent_df.loc[date, 'Low']
            print(f"  {i+1}. {row['date']} - 價格: {price:.2f}")
        
        # 步驟4：趨勢分析
        print(f"\n{'='*60}")
        print("步驟4：趨勢分析")
        print(f"{'='*60}")
        
        trend_changes = result_df[result_df['trend_type'] != ''].copy()
        if len(trend_changes) > 0:
            prev_trend = None
            for _, row in trend_changes.iterrows():
                if row['trend_type'] != prev_trend:
                    trend_emoji = {
                        'up': '📈',
                        'down': '📉',
                        'consolidation': '↔️'
                    }.get(row['trend_type'], '❓')
                    
                    print(f"  {row['date']}: {trend_emoji} {row['trend_type']}")
                    prev_trend = row['trend_type']
        
        # 步驟5：檢查待確認狀態
        pending_reversals = result_df[result_df['pending_reversal'] != '']
        if len(pending_reversals) > 0:
            print(f"\n⏸️ 待確認反轉狀態：")
            for _, row in pending_reversals.iterrows():
                print(f"  {row['date']}: {row['pending_reversal']}")
        
        # 步驟6：繪製診斷圖表
        print(f"\n{'='*60}")
        print("步驟5：生成診斷圖表")
        print(f"{'='*60}")
        
        create_waving_debug_chart(stock_id, recent_df, result_df, all_turning)
        
        # 步驟7：保存結果
        output_dir = 'output/debug_charts'
        os.makedirs(output_dir, exist_ok=True)
        
        result_file = f'{output_dir}/{stock_id}_waving_result.csv'
        result_df.to_csv(result_file, index=False, encoding='utf-8-sig')
        print(f"\n✅ 結果已保存至: {result_file}")
        
        # 保存日誌
        log_file = f'{output_dir}/{stock_id}_waving_log.txt'
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(identifier.log_messages))
        print(f"✅ 執行日誌已保存至: {log_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 診斷過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


_configured_font_family = None
_registered_local_fonts = False


def _register_local_fonts():
    """註冊本地字體"""
    global _registered_local_fonts
    if _registered_local_fonts:
        return

    local_font_paths = [
        os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'NotoSansCJKtc-Regular.otf'),
    ]

    for font_path in local_font_paths:
        if os.path.isfile(font_path):
            font_manager.fontManager.addfont(font_path)

    _registered_local_fonts = True


def _font_is_available(font_family: str) -> bool:
    """檢查字體是否可用"""
    try:
        prop = font_manager.FontProperties(family=font_family)
        font_manager.findfont(prop, fallback_to_default=False)
        return True
    except (ValueError, RuntimeError):
        return False


def _ensure_plot_fonts():
    """確保繪圖字體可用"""
    global _configured_font_family
    if _configured_font_family:
        return _configured_font_family

    _register_local_fonts()

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
        if _font_is_available(family):
            plt.rcParams['font.sans-serif'] = [family]
            _configured_font_family = family
            break
    else:
        default_family = plt.rcParams.get('font.sans-serif', ['DejaVu Sans'])
        _configured_font_family = default_family[0] if default_family else 'DejaVu Sans'

    plt.rcParams['axes.unicode_minus'] = False
    return _configured_font_family


def create_waving_debug_chart(stock_id, recent_df, result_df, all_turning):
    """
    創建趨勢波診斷圖表
    """
    try:
        chosen_font = _ensure_plot_fonts()
        fig = plt.figure(figsize=(24, 16))
        if chosen_font not in plt.rcParams.get('font.sans-serif', []):
            plt.rcParams['font.sans-serif'] = [chosen_font]
        
        # 主圖：K線圖 + MA5 + 轉折點 + 波段點 + 趨勢區間
        ax1 = plt.subplot(4, 1, 1)
        dates = recent_df.index
        
        # 繪製K棒
        for i, date in enumerate(dates):
            row = recent_df.loc[date]
            open_price = row['Open']
            high_price = row['High']
            low_price = row['Low']
            close_price = row['Close']
            
            is_up = close_price >= open_price
            
            # 繪製上下影線
            plt.plot([date, date], [low_price, high_price], 
                    color='black', linewidth=1.0, alpha=0.7, zorder=2)
            
            # 繪製實體K棒
            body_height = abs(close_price - open_price)
            body_bottom = min(open_price, close_price)
            bar_width = pd.Timedelta(days=0.4)  # 減小K線寬度
            
            if is_up:
                rect = plt.Rectangle((date - bar_width/2, body_bottom), 
                                   bar_width, body_height, 
                                   facecolor='white', edgecolor='red', 
                                   linewidth=1.5, alpha=1.0, zorder=3)
            else:
                rect = plt.Rectangle((date - bar_width/2, body_bottom), 
                                   bar_width, body_height, 
                                   facecolor='#00AA00', edgecolor='#00AA00',  # 使用更鮮明的綠色
                                   linewidth=1.5, alpha=1.0, zorder=3)
            
            plt.gca().add_patch(rect)
        
        # 繪製MA5
        plt.plot(dates, recent_df['ma5'], 
                color='blue', linewidth=2, linestyle='-', 
                alpha=0.8, label='5MA', zorder=5)
        
        # 標記轉折點
        high_series = recent_df['High']
        low_series = recent_df['Low']
        chart_range = float(high_series.max() - low_series.min())
        base_offset = chart_range * 0.015 if chart_range > 0 else 0.1  # 增加偏移量
        
        turning_labeled = {'high': False, 'low': False}
        
        for date, tp_type, price in all_turning:
            color = 'darkred' if tp_type == 'high' else 'darkblue'
            marker = '^' if tp_type == 'high' else 'v'
            
            row_data = recent_df.loc[date]
            row_high = float(row_data['High'])
            row_low = float(row_data['Low'])
            
            # ✅ 修正：根據類型決定位置和標籤
            if tp_type == 'high':
                y_pos = row_high + base_offset * 2
                label_text = '轉折高點' if not turning_labeled['high'] else None
                turning_labeled['high'] = True
            else:  # tp_type == 'low'
                y_pos = row_low - base_offset * 2
                label_text = '轉折低點' if not turning_labeled['low'] else None
                turning_labeled['low'] = True
            
            plt.scatter([date], [y_pos], color=color, marker=marker, 
                       s=200, alpha=0.9, zorder=10, label=label_text,  # 增大標記尺寸
                       edgecolors='white', linewidths=2)  # 增加邊框寬度
        
        # 標記波段點
        wave_highs = result_df[result_df['wave_high_point'] == 'O']
        wave_lows = result_df[result_df['wave_low_point'] == 'O']
        
        wave_labeled = {'high': False, 'low': False}
        
        for _, row in wave_highs.iterrows():
            date = pd.to_datetime(row['date'])
            if date in recent_df.index:
                price = recent_df.loc[date, 'High']
                y_pos = price + base_offset * 4
                
                label_text = '波段高點' if not wave_labeled['high'] else None
                wave_labeled['high'] = True
                
                plt.scatter([date], [y_pos], color='red', marker='*', 
                           s=500, alpha=1.0, zorder=15, label=label_text,  # 增大波段點標記
                           edgecolors='darkred', linewidths=2.5)
        
        for _, row in wave_lows.iterrows():
            date = pd.to_datetime(row['date'])
            if date in recent_df.index:
                price = recent_df.loc[date, 'Low']
                y_pos = price - base_offset * 4
                
                label_text = '波段低點' if not wave_labeled['low'] else None
                wave_labeled['low'] = True
                
                plt.scatter([date], [y_pos], color='blue', marker='*', 
                           s=500, alpha=1.0, zorder=15, label=label_text,  # 增大波段點標記
                           edgecolors='darkblue', linewidths=2.5)
        
        # 繪製趨勢背景
        trend_colors = {
            'up': ('green', 0.1),
            'down': ('red', 0.1),
            'consolidation': ('gray', 0.05)
        }
        
        prev_date = None
        prev_trend = None
        
        for date in dates:
            date_str = date.strftime('%Y-%m-%d')
            row = result_df[result_df['date'] == date_str]
            
            if len(row) > 0:
                current_trend = row.iloc[0]['trend_type']
                
                if current_trend != '' and current_trend != prev_trend:
                    if prev_date is not None and prev_trend in trend_colors:
                        # 繪製前一個趨勢區間
                        color, alpha = trend_colors[prev_trend]
                        ax1.axvspan(prev_date, date, alpha=alpha, color=color, zorder=1)
                    
                    prev_date = date
                    prev_trend = current_trend
        
        # 繪製最後一個趨勢區間
        if prev_date is not None and prev_trend in trend_colors:
            color, alpha = trend_colors[prev_trend]
            ax1.axvspan(prev_date, dates[-1], alpha=alpha, color=color, zorder=1)
        
        plt.title(f'{stock_id} 趨勢波偵測診斷圖', fontsize=18, fontweight='bold', pad=20)
        plt.ylabel('價格', fontsize=14)
        plt.legend(fontsize=11, loc='upper left', framealpha=0.9)
        plt.grid(True, alpha=0.3, linestyle='--')
        
        # 子圖2：趨勢類型時間軸
        ax2 = plt.subplot(4, 1, 2, sharex=ax1)
        
        trend_mapping = {'up': 1, 'down': -1, 'consolidation': 0, '': np.nan}
        trend_values = []
        
        for date in dates:
            date_str = date.strftime('%Y-%m-%d')
            row = result_df[result_df['date'] == date_str]
            if len(row) > 0:
                trend = row.iloc[0]['trend_type']
                trend_values.append(trend_mapping.get(trend, np.nan))
            else:
                trend_values.append(np.nan)
        
        plt.plot(dates, trend_values, linewidth=2.5, color='purple', alpha=0.8)
        plt.fill_between(dates, trend_values, alpha=0.3, color='purple')
        plt.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        
        plt.title('趨勢類型時間軸', fontsize=14, pad=10)
        plt.ylabel('趨勢方向', fontsize=12)
        plt.yticks([-1, 0, 1], ['下降', '盤整', '上升'])
        plt.grid(True, alpha=0.3, linestyle='--')
        
        # 子圖3：轉折點序列
        ax3 = plt.subplot(4, 1, 3, sharex=ax1)
        
        high_dates = [tp[0] for tp in all_turning if tp[1] == 'high']
        high_prices = [tp[2] for tp in all_turning if tp[1] == 'high']
        low_dates = [tp[0] for tp in all_turning if tp[1] == 'low']
        low_prices = [tp[2] for tp in all_turning if tp[1] == 'low']
        
        if high_dates:
            plt.scatter(high_dates, high_prices, color='darkred', marker='^', 
                       s=150, alpha=0.9, label='轉折高點', zorder=10)
        if low_dates:
            plt.scatter(low_dates, low_prices, color='darkblue', marker='v', 
                       s=150, alpha=0.9, label='轉折低點', zorder=10)
        
        # 連接轉折點
        if len(all_turning) > 1:
            turning_dates = [tp[0] for tp in all_turning]
            turning_prices = [tp[2] for tp in all_turning]
            plt.plot(turning_dates, turning_prices, color='brown', 
                    linewidth=2, linestyle='-', alpha=0.6, zorder=5)
        
        plt.title('轉折點序列圖', fontsize=14, pad=10)
        plt.ylabel('價格', fontsize=12)
        plt.legend(fontsize=11, loc='upper left')
        plt.grid(True, alpha=0.3, linestyle='--')
        
        # 子圖4：波段點標記
        ax4 = plt.subplot(4, 1, 4, sharex=ax1)
        
        # 繪製收盤價
        plt.plot(dates, recent_df['Close'], color='black', linewidth=1.5, 
                alpha=0.7, label='收盤價')
        
        # 標記波段高點
        for _, row in wave_highs.iterrows():
            date = pd.to_datetime(row['date'])
            if date in recent_df.index:
                price = recent_df.loc[date, 'High']
                plt.scatter([date], [price], color='red', marker='*', 
                           s=500, alpha=1.0, zorder=15,
                           edgecolors='darkred', linewidths=2)
                plt.axvline(x=date, color='red', linestyle='--', 
                           linewidth=1, alpha=0.5)
        
        # 標記波段低點
        for _, row in wave_lows.iterrows():
            date = pd.to_datetime(row['date'])
            if date in recent_df.index:
                price = recent_df.loc[date, 'Low']
                plt.scatter([date], [price], color='blue', marker='*', 
                           s=500, alpha=1.0, zorder=15,
                           edgecolors='darkblue', linewidths=2)
                plt.axvline(x=date, color='blue', linestyle='--', 
                           linewidth=1, alpha=0.5)
        
        plt.title('波段點標記圖', fontsize=14, pad=10)
        plt.ylabel('價格', fontsize=12)
        plt.xlabel('日期', fontsize=12)
        plt.legend(fontsize=11, loc='upper left')
        plt.grid(True, alpha=0.3, linestyle='--')
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # 保存圖表
        output_dir = 'output/debug_charts'
        os.makedirs(output_dir, exist_ok=True)
        chart_path = f'{output_dir}/{stock_id}_waving_point_debug.png'
        
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        print(f"✅ 診斷圖表已保存至: {chart_path}")
        plt.show()
        
    except Exception as e:
        print(f"❌ 創建診斷圖表時發生錯誤: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主程式"""
    print("趨勢波偵測診斷程式")
    print("=" * 80)
    print("診斷 waving_point_identification.py 的執行邏輯")
    
    stock_id = input("\n請輸入股票代碼 (預設00631L): ").strip() or '00631L'
    
    try:
        days_input = input("請輸入分析天數 (預設120天): ").strip()
        days = int(days_input) if days_input else 120
    except ValueError:
        days = 120
    
    print(f"\n開始診斷 {stock_id} 的趨勢波識別...")
    
    success = debug_waving_point_execution(stock_id, days)
    
    if success:
        print(f"\n🎉 診斷完成！請檢查控制台輸出和生成的圖表。")
        print(f"   結果文件保存在 output/debug_charts/ 目錄")
    else:
        print(f"\n❌ 診斷失敗！")


if __name__ == "__main__":
    main()