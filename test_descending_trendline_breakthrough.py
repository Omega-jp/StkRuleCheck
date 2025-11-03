#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收盤站上下降趨勢線買入規則測試程式（更新版 - 配合規格書版本）
- 修正中文字體問題
- 使用新的 API: check_breakthrough_descending_trendline
- 使用新的趨勢線識別: identify_descending_trendlines
"""

import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
from matplotlib import font_manager
import matplotlib.font_manager as fm

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


_configured_font_family = None
_registered_local_fonts = False


def _register_local_fonts():
    """Register bundled font files (if any) with matplotlib's font manager."""
    global _registered_local_fonts
    if _registered_local_fonts:
        return

    local_font_paths = [
        os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'NotoSansCJKtc-Regular.otf'),
        os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'NotoSansCJKsc-Regular.otf'),
    ]

    for font_path in local_font_paths:
        if os.path.isfile(font_path):
            try:
                font_manager.fontManager.addfont(font_path)
                print(f"✅ 成功載入本地字體: {font_path}")
            except Exception as e:
                print(f"⚠️  載入本地字體失敗 {font_path}: {e}")

    _registered_local_fonts = True


def _font_is_available(font_family: str) -> bool:
    """Return True if matplotlib can locate the requested font family."""
    try:
        prop = font_manager.FontProperties(family=font_family)
        font_manager.findfont(prop, fallback_to_default=False)
        return True
    except (ValueError, RuntimeError):
        return False


def _ensure_plot_fonts():
    """Pick a font family that exists on this machine so Unicode text renders cleanly."""
    global _configured_font_family
    if _configured_font_family:
        return _configured_font_family

    _register_local_fonts()

    preferred_order = [
        'Microsoft JhengHei',
        'Microsoft YaHei',
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
    ]

    for family in preferred_order:
        if _font_is_available(family):
            plt.rcParams['font.sans-serif'] = [family]
            plt.rcParams['axes.unicode_minus'] = False
            _configured_font_family = family
            print(f"✅ 使用字體: {family}")
            return _configured_font_family
    
    print("⚠️  未找到任何中文字體，使用系統預設字體")
    plt.rcParams['axes.unicode_minus'] = False
    _configured_font_family = 'default'
    return _configured_font_family


def setup_chinese_font():
    """設置中文字體（自動尋找可用字體）"""
    try:
        chinese_fonts = [
            'Microsoft JhengHei',
            'Microsoft YaHei',
            'SimHei',
            'Arial Unicode MS',
            'PingFang TC',
            'Noto Sans CJK TC',
            'Noto Sans CJK SC',
            'WenQuanYi Zen Hei',
        ]
        
        available_fonts = set([f.name for f in fm.fontManager.ttflist])
        
        selected_font = None
        for font in chinese_fonts:
            if font in available_fonts:
                selected_font = font
                print(f"✅ 使用字體: {font}")
                break
        
        if selected_font:
            plt.rcParams['font.sans-serif'] = [selected_font]
            plt.rcParams['axes.unicode_minus'] = False
        else:
            print("⚠️  未找到中文字體，使用預設字體")
            plt.rcParams['axes.unicode_minus'] = False
        
    except Exception as e:
        print(f"⚠️  字體設置失敗: {e}")
        plt.rcParams['axes.unicode_minus'] = False


def find_all_descending_trendlines(df, wave_points_df):
    """
    找出所有有效的下降趨勢線（使用新的 API）
    """
    from src.buyRule.long_term_descending_trendline import identify_descending_trendlines
    
    # 使用新的 API
    trendlines = identify_descending_trendlines(
        df,
        wave_points_df,
        lookback_days=180,
        recent_end_days=20,
        tolerance_pct=0.1
    )
    
    return trendlines


def draw_trendline(ax, line_info, df, color, label_prefix):
    """
    繪製單條趨勢線
    """
    line_type = line_info['type']
    
    if line_type == 'horizontal_resistance':
        # 繪製水平壓力線
        y_value = line_info['resistance_price']
        start_date = df.index[0]
        end_date = df.index[-1]
        
        ax.axhline(y=y_value, color=color, linewidth=2.5, linestyle='--', 
                   alpha=0.8, zorder=10, label=f'{label_prefix}水平壓力線')
        
        # 標記價格
        mid_date = df.index[len(df)//2]
        ax.text(mid_date, y_value * 1.01, f'壓力線 {y_value:.2f}',
               fontsize=9, color=color, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                        edgecolor=color, alpha=0.8))
    
    else:
        # 繪製斜向趨勢線
        start_idx = line_info['start_idx']
        end_idx = line_info['end_idx']
        slope = line_info['slope']
        intercept = line_info['intercept']
        
        start_date = df.index[start_idx]
        end_date = df.index[end_idx]
        
        last_idx = len(df) - 1
        last_date = df.index[last_idx]
        
        start_price = intercept + slope * start_idx
        end_price = intercept + slope * end_idx
        last_price = intercept + slope * last_idx
        
        # 繪製基準段（實線）
        ax.plot([start_date, end_date], 
                [start_price, end_price], 
                color=color, linewidth=2.5, linestyle='-', 
                alpha=0.9, zorder=10)
        
        # 延伸到最後（虛線）
        if last_idx > end_idx:
            ax.plot([end_date, last_date], 
                    [end_price, last_price], 
                    color=color, linewidth=2, linestyle='--', 
                    alpha=0.7, zorder=10)
        
        # 標記起點和終點
        points = line_info.get('points', [])
        if len(points) >= 2:
            point1 = points[0]
            point2 = points[-1]
            
            ax.scatter([point1['date'], point2['date']], 
                      [point1['price'], point2['price']], 
                      color=color, marker='o', s=100, 
                      edgecolor='white', linewidth=2, zorder=15)
        
        # 添加標籤
        days_span = line_info.get('days_span', 0)
        label = f"{label_prefix}斜向線 ({days_span}天)"
        
        mid_idx = (start_idx + end_idx) // 2
        mid_date = df.index[mid_idx]
        mid_price = intercept + slope * mid_idx
        
        ax.text(mid_date, mid_price * 1.02, label,
               fontsize=9, color=color, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                        edgecolor=color, alpha=0.8))


def create_descending_trendline_chart(stock_id, recent_df, wave_points_df, 
                                      buy_signals, trendlines, days):
    """
    創建下降趨勢線突破分析圖表
    """
    try:
        setup_chinese_font()
        _ensure_plot_fonts()
        
        plt.figure(figsize=(20, 14))
        
        # 主圖：K線圖
        ax1 = plt.subplot(3, 1, (1, 2))
        dates = recent_df.index
        opens = recent_df['Open']
        highs = recent_df['High']
        lows = recent_df['Low']
        closes = recent_df['Close']
        ma5 = closes.rolling(window=5, min_periods=1).mean()
        
        # 繪製K線
        print("   繪製K線圖...")
        for i in range(len(dates)):
            date = dates[i]
            open_price = opens.iloc[i]
            high_price = highs.iloc[i]
            low_price = lows.iloc[i]
            close_price = closes.iloc[i]
            
            color = 'red' if close_price >= open_price else 'green'
            
            plt.plot([date, date], [low_price, high_price], 
                    color=color, linewidth=1, alpha=0.8)
            
            body_height = abs(close_price - open_price)
            body_bottom = min(open_price, close_price)
            
            plt.bar(date, body_height, bottom=body_bottom, 
                   color=color, alpha=0.7, width=0.8)

        # Plot MA5 moving average line on the price chart
        plt.plot(dates, ma5, color='dodgerblue', linewidth=1.6,
                 label='MA5 (5日均線)', zorder=12)
        
        # 標記波段高點
        print("   標記波段點...")
        high_point_dates = []
        high_point_prices = []
        for _, row in wave_points_df.iterrows():
            if row.get('wave_high_point', '') == 'O':
                date_str = row['date']
                matching_dates = recent_df[recent_df.index.strftime('%Y-%m-%d') == date_str]
                if not matching_dates.empty:
                    high_point_dates.append(matching_dates.index[0])
                    high_point_prices.append(matching_dates.iloc[0]['High'])
        
        if high_point_dates:
            adjusted_high_prices = [price * 1.02 for price in high_point_prices]
            plt.scatter(high_point_dates, adjusted_high_prices, 
                       color='darkred', marker='^', s=50, 
                       label=f'波段高點 ({len(high_point_dates)}個)', 
                       zorder=15, edgecolor='white', linewidth=1)
            print(f"   找到 {len(high_point_dates)} 個波段高點")
        
        # 繪製趨勢線
        print("   繪製下降趨勢線...")
        diagonal_lines = trendlines.get('diagonal_lines', [])
        horizontal_line = trendlines.get('horizontal_line', None)
        
        colors = ['orange', 'purple', 'brown', 'darkred', 'navy', 'cyan']
        
        # 繪製斜向趨勢線
        for i, line in enumerate(diagonal_lines[:5]):
            color = colors[i % len(colors)]
            draw_trendline(ax1, line, recent_df, color, f"趨勢線{i+1}-")
        
        # 繪製水平壓力線
        if horizontal_line:
            draw_trendline(ax1, horizontal_line, recent_df, 'red', "")
        
        print(f"   斜向趨勢線: {len(diagonal_lines)} 條")
        print(f"   水平壓力線: {'1 條' if horizontal_line else '無'}")
        
        # 標記買入信號
        print("   標記買入信號...")
        buy_signal_count = 0
        signal_colors = {1: 'yellow', 2: 'orange', 3: 'gold', 4: 'lime', 5: 'red'}
        signal_sizes = {1: 100, 2: 150, 3: 200, 4: 250, 5: 300}
        
        for _, row in buy_signals.iterrows():
            if row.get('breakthrough_check', '') == 'O':
                date_str = row['date']
                matching_dates = recent_df[recent_df.index.strftime('%Y-%m-%d') == date_str]
                if not matching_dates.empty:
                    buy_date = matching_dates.index[0]
                    buy_low = matching_dates.iloc[0]['Low']
                    buy_mark_price = buy_low * 0.97
                    
                    strength = int(row.get('signal_strength', 3))
                    color = signal_colors.get(strength, 'lime')
                    size = signal_sizes.get(strength, 200)
                    
                    plt.scatter([buy_date], [buy_mark_price],
                               color=color, marker='*', s=size, 
                               edgecolor='darkgreen', linewidth=2, 
                               label=f'買入信號 強度{strength}', zorder=20)
                    buy_signal_count += 1
        
        print(f"   找到 {buy_signal_count} 個買入信號")
        
        # 圖表設置
        plt.title(f'{stock_id} 收盤站上下降趨勢線買入分析 (最近{days}天)', 
                 fontsize=18, fontweight='bold', pad=20)
        plt.ylabel('價格', fontsize=14)
        plt.legend(fontsize=10, loc='upper left')
        plt.grid(True, alpha=0.3, linestyle='--')
        
        y_min = recent_df['Low'].min() * 0.93
        y_max = recent_df['High'].max() * 1.05
        plt.ylim(y_min, y_max)
        
        # 成交量圖
        ax2 = plt.subplot(3, 1, 3)
        volume_colors = ['red' if closes.iloc[i] >= opens.iloc[i] else 'green' 
                        for i in range(len(dates))]
        
        plt.bar(dates, recent_df['Volume'], alpha=0.7, 
               color=volume_colors, width=0.8)
        
        # 標記買入信號對應的成交量
        for _, row in buy_signals.iterrows():
            if row.get('breakthrough_check', '') == 'O':
                date_str = row['date']
                matching_dates = recent_df[recent_df.index.strftime('%Y-%m-%d') == date_str]
                if not matching_dates.empty:
                    buy_date = matching_dates.index[0]
                    buy_volume = matching_dates.iloc[0]['Volume']
                    volume_ratio = row.get('volume_ratio', 1.0)
                    
                    plt.scatter([buy_date], [buy_volume * 1.1],
                               color='gold', marker='P', s=100, 
                               edgecolor='red', linewidth=2, zorder=10)
                    
                    plt.text(buy_date, buy_volume * 1.2, f'{volume_ratio:.1f}x',
                            ha='center', va='bottom', fontsize=10, 
                            bbox=dict(boxstyle='round,pad=0.2', 
                                    facecolor='yellow', alpha=0.8))
        
        plt.title('成交量 (標記買入信號對應的放量)', fontsize=14)
        plt.ylabel('成交量', fontsize=12)
        plt.xlabel('日期', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # 保存圖表
        output_dir = 'output/test_charts'
        os.makedirs(output_dir, exist_ok=True)
        chart_path = f'{output_dir}/{stock_id}_descending_trendline_buy.png'
        
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        print(f"✅ 圖表已保存至: {chart_path}")
        plt.close()
        
    except Exception as e:
        print(f"❌ 創建圖表時發生錯誤: {e}")
        import traceback
        traceback.print_exc()


def print_buy_signal_stats(buy_signals):
    """輸出買入信號統計資訊"""
    signals = buy_signals[buy_signals.get('breakthrough_check', '') == 'O']
    
    if len(signals) == 0:
        print(f"\n📊 買入信號統計：無買入信號")
        return
    
    print(f"\n📊 買入信號統計：")
    print(f"   總信號數量: {len(signals)}")
    print(f"   平均信號強度: {signals['signal_strength'].mean():.2f}/5")
    
    # 按類型統計
    horizontal_count = len(signals[signals['breakthrough_type'] == 'horizontal_resistance'])
    diagonal_count = len(signals[signals['breakthrough_type'] == 'diagonal_descending'])
    print(f"   水平壓力線突破: {horizontal_count} 個")
    print(f"   斜向趨勢線突破: {diagonal_count} 個")
    
    # 信號強度分布
    strength_dist = signals['signal_strength'].value_counts().sort_index()
    print(f"   信號強度分布:")
    for strength, count in strength_dist.items():
        print(f"     {strength}分: {count} 個")
    
    # 其他統計
    print(f"   平均突破幅度: {signals['breakthrough_pct'].mean():.2f}%")
    print(f"   平均成交量比率: {signals['volume_ratio'].mean():.2f}x")
    
    # 最佳信號
    if len(signals) > 0:
        best_signal = signals.loc[signals['signal_strength'].idxmax()]
        print(f"\n🏆 最強信號 ({best_signal['signal_strength']}/5):")
        print(f"   日期: {best_signal['date']}")
        print(f"   類型: {'水平壓力線' if best_signal['breakthrough_type'] == 'horizontal_resistance' else '斜向趨勢線'}")
        print(f"   突破幅度: {best_signal['breakthrough_pct']:.2f}%")
        print(f"   成交量比率: {best_signal['volume_ratio']:.2f}x")


def descending_trendline_test(stock_id='2330', days=360):
    """下降趨勢線突破測試"""
    print(f"\n{'='*70}")
    print(f"下降趨勢線突破買入規則測試：{stock_id}")
    print(f"{'='*70}")
    
    try:
        from src.validate_buy_rule import load_stock_data
        from src.buyRule.breakthrough_descending_trendline import check_breakthrough_descending_trendline
        from src.baseRule.waving_point_identification import identify_waving_points
        from src.baseRule.turning_point_identification import identify_turning_points
        
        # 載入數據
        print("🔄 載入股票數據...")
        df = load_stock_data(stock_id, 'D')
        if df is None:
            print(f"❌ 無法載入股票 {stock_id} 的數據")
            return False
        
        print(f"✅ 成功載入數據，共 {len(df)} 筆記錄")
        
        # 確保有ma5欄位
        if 'ma5' not in df.columns:
            df['ma5'] = df['Close'].rolling(window=5, min_periods=1).mean()
        
        # 取最近的數據
        recent_df = df.tail(days)
        print(f"📊 分析最近 {len(recent_df)} 天的數據")
        
        # 識別轉折點和波段點
        print("🔍 執行轉折點識別...")
        turning_points_df = identify_turning_points(recent_df)
        
        print("🔍 執行波段點識別...")
        wave_points_df = identify_waving_points(recent_df, turning_points_df)
        
        # 找出所有下降趨勢線
        print("🔍 識別所有下降趨勢線...")
        trendlines = find_all_descending_trendlines(recent_df, wave_points_df)
        
        # 執行下降趨勢線突破買入規則分析
        print("🚀 執行下降趨勢線突破買入分析...")
        buy_signals = check_breakthrough_descending_trendline(
            recent_df,
            trendlines,
        )
        
        # 創建圖表
        print("🎨 創建分析圖表...")
        create_descending_trendline_chart(
            stock_id, recent_df, wave_points_df, 
            buy_signals, trendlines, days
        )
        
        # 輸出買入信號統計
        print_buy_signal_stats(buy_signals)
        
        # 輸出趨勢線統計
        print(f"\n📈 趨勢線統計：")
        print(f"   斜向趨勢線: {len(trendlines.get('diagonal_lines', []))} 條")
        print(f"   水平壓力線: {'1 條' if trendlines.get('horizontal_line') else '無'}")
        print(f"   總計: {len(trendlines.get('all_lines', []))} 條")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主程式"""
    print("收盤站上下降趨勢線買入規則測試程式（規格書版本）")
    print("=" * 70)
    print("改進：")
    print("  ✓ 自動偵測並使用可用的中文字體")
    print("  ✓ 使用規格書版本的突破檢查邏輯")
    print("  ✓ 支援水平壓力線和斜向趨勢線")
    print("  ✓ 顯示所有有效的下降趨勢線")
    print("=" * 70)
    
    while True:
        stock_id = input("\n請輸入股票代碼 (預設2330，輸入'quit'退出): ").strip()
        
        if stock_id.lower() == 'quit':
            print("程式結束")
            break
        
        if not stock_id:
            stock_id = '2330'
        
        try:
            days_input = input("請輸入顯示天數 (預設360天，建議至少300天): ").strip()
            days = int(days_input) if days_input else 360
            if days < 200:
                print("⚠️  警告：天數太少可能無法識別長期趨勢線，建議至少300天")
        except ValueError:
            days = 360
        
        print(f"\n開始測試：{stock_id}，顯示最近 {days} 天...")
        
        success = descending_trendline_test(stock_id, days)
        
        if success:
            print(f"\n🎉 {stock_id} 下降趨勢線買入規則測試完成！")
        else:
            print(f"\n❌ {stock_id} 測試失敗！")
        
        continue_test = input("\n是否測試其他股票？(y/n): ").strip().lower()
        if continue_test != 'y':
            break


if __name__ == "__main__":
    main()
