#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收盤站上下降趨勢線買入規則測試程式（修正版）
- 修正中文字體問題
- 顯示所有有效的下降趨勢線（不只是被突破的）
"""

import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


def setup_chinese_font():
    """設置中文字體（自動尋找可用字體）"""
    try:
        # 嘗試常見的中文字體
        chinese_fonts = [
            'Microsoft JhengHei',  # 微軟正黑體
            'Microsoft YaHei',     # 微軟雅黑
            'SimHei',              # 黑體
            'Arial Unicode MS',    # Arial Unicode
            'Noto Sans CJK TC',    # Noto Sans 繁體中文
            'Noto Sans CJK SC',    # Noto Sans 簡體中文
            'DejaVu Sans',         # 後備字體
        ]
        
        # 獲取系統所有可用字體
        available_fonts = set([f.name for f in fm.fontManager.ttflist])
        
        # 找到第一個可用的中文字體
        selected_font = None
        for font in chinese_fonts:
            if font in available_fonts:
                selected_font = font
                print(f"✅ 使用字體: {font}")
                break
        
        if selected_font:
            plt.rcParams['font.sans-serif'] = [selected_font]
        else:
            print("⚠️  未找到中文字體，使用預設字體")
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
        
        plt.rcParams['axes.unicode_minus'] = False
        
    except Exception as e:
        print(f"⚠️  字體設置失敗: {e}")
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False


def find_all_descending_trendlines(df, turning_points_df):
    """
    找出所有有效的下降趨勢線（不限於被突破的）
    """
    from src.buyRule.long_term_descending_trendline import identify_long_term_descending_trendlines
    
    # 識別所有下降趨勢線
    trendlines = identify_long_term_descending_trendlines(
        df,
        turning_points_df,
        min_days_long_term=180,
        min_points_short_term=3
    )
    
    return trendlines


def draw_trendline(ax, line_info, df, color, label_prefix):
    """
    繪製單條趨勢線
    """
    start_idx = line_info['start_idx']
    end_idx = line_info['end_idx']
    slope = line_info['equation']['slope']
    intercept = line_info['equation']['intercept']
    
    # 取得起點和終點的日期
    start_date = df.index[start_idx]
    end_date = df.index[end_idx]
    
    # 延伸到最後一天
    last_idx = len(df) - 1
    last_date = df.index[last_idx]
    
    # 計算各點的價格
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
    points = line_info['points']
    if len(points) >= 2:
        point1 = points[0]
        point2 = points[-1]
        
        # 標記連接點
        ax.scatter([point1['date'], point2['date']], 
                  [point1['price'], point2['price']], 
                  color=color, marker='o', s=100, 
                  edgecolor='white', linewidth=2, zorder=15)
    
    # 添加標籤
    days_span = line_info['days_span']
    line_type = "長期" if line_info['type'] == 'long_term_two_point' else "短期"
    label = f"{label_prefix}{line_type} ({days_span}天)"
    
    # 在趨勢線中點添加文字標籤
    mid_idx = (start_idx + end_idx) // 2
    mid_date = df.index[mid_idx]
    mid_price = intercept + slope * mid_idx
    
    ax.text(mid_date, mid_price * 1.02, label,
           fontsize=9, color=color, fontweight='bold',
           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                    edgecolor=color, alpha=0.8))


def create_descending_trendline_chart(stock_id, recent_df, turning_points_df, 
                                      buy_signals, trendlines, days):
    """
    創建下降趨勢線突破分析圖表（顯示所有趨勢線）
    """
    try:
        # 設置中文字體
        setup_chinese_font()
        
        plt.figure(figsize=(20, 14))
        
        # 主圖：K線圖
        ax1 = plt.subplot(3, 1, (1, 2))
        dates = recent_df.index
        opens = recent_df['Open']
        highs = recent_df['High']
        lows = recent_df['Low']
        closes = recent_df['Close']
        
        # 繪製K棒
        print("   繪製K棒...")
        for i, date in enumerate(dates):
            open_price = opens.iloc[i]
            high_price = highs.iloc[i]
            low_price = lows.iloc[i]
            close_price = closes.iloc[i]
            
            is_up = close_price >= open_price
            
            # 繪製上下影線
            plt.plot([date, date], [low_price, high_price], 
                    color='black', linewidth=0.8, alpha=0.8)
            
            # 繪製實體K棒
            body_height = abs(close_price - open_price)
            body_bottom = min(open_price, close_price)
            bar_width = pd.Timedelta(days=0.6)
            
            if is_up:
                rect = plt.Rectangle((date - bar_width/2, body_bottom), 
                                   bar_width, body_height, 
                                   facecolor='white', edgecolor='red', 
                                   linewidth=1.2, alpha=0.9)
            else:
                rect = plt.Rectangle((date - bar_width/2, body_bottom), 
                                   bar_width, body_height, 
                                   facecolor='green', edgecolor='green', 
                                   linewidth=1.2, alpha=0.9)
            
            plt.gca().add_patch(rect)
        
        # 繪製5日移動平均線
        print("   繪製5日移動平均線...")
        if 'ma5' in recent_df.columns:
            plt.plot(dates, recent_df['ma5'], 
                    color='blue', linewidth=1.5, linestyle='-', 
                    alpha=0.8, label='5MA', zorder=5)
        
        # 找出所有轉折高點
        print("   識別轉折高點...")
        high_point_dates = []
        high_point_prices = []
        for _, row in turning_points_df.iterrows():
            if row['turning_high_point'] == 'O':
                date_str = row['date']
                matching_dates = recent_df[recent_df.index.strftime('%Y-%m-%d') == date_str]
                if not matching_dates.empty:
                    high_point_dates.append(matching_dates.index[0])
                    high_point_prices.append(matching_dates.iloc[0]['High'])
        
        # 找出所有轉折低點
        print("   識別轉折低點...")
        low_point_dates = []
        low_point_prices = []
        for _, row in turning_points_df.iterrows():
            if row['turning_low_point'] == 'O':
                date_str = row['date']
                matching_dates = recent_df[recent_df.index.strftime('%Y-%m-%d') == date_str]
                if not matching_dates.empty:
                    low_point_dates.append(matching_dates.index[0])
                    low_point_prices.append(matching_dates.iloc[0]['Low'])
        
        # 標記轉折高點
        if high_point_dates:
            adjusted_high_prices = [price * 1.02 for price in high_point_prices]
            plt.scatter(high_point_dates, adjusted_high_prices, 
                       color='darkred', marker='^', s=50, 
                       label=f'轉折高點 ({len(high_point_dates)}個)', 
                       zorder=15, edgecolor='white', linewidth=1)
            print(f"   找到 {len(high_point_dates)} 個轉折高點")
        
        # 標記轉折低點
        if low_point_dates:
            adjusted_low_prices = [price * 0.98 for price in low_point_prices]
            plt.scatter(low_point_dates, adjusted_low_prices, 
                       color='darkblue', marker='v', s=50, 
                       label=f'轉折低點 ({len(low_point_dates)}個)', 
                       zorder=15, edgecolor='white', linewidth=1)
            print(f"   找到 {len(low_point_dates)} 個轉折低點")
        
        # 繪製所有長期下降趨勢線
        print("   繪製下降趨勢線...")
        long_term_lines = trendlines.get('long_term_lines', [])
        short_term_lines = trendlines.get('short_term_lines', [])
        
        colors_long = ['orange', 'purple', 'brown', 'darkred', 'navy']
        colors_short = ['cyan', 'magenta', 'lime', 'pink']
        
        # 繪製長期趨勢線
        for i, line in enumerate(long_term_lines[:5]):  # 最多顯示5條
            color = colors_long[i % len(colors_long)]
            draw_trendline(ax1, line, recent_df, color, f"趨勢線{i+1}-")
        
        # 繪製短期趨勢線
        for i, line in enumerate(short_term_lines[:3]):  # 最多顯示3條
            color = colors_short[i % len(colors_short)]
            draw_trendline(ax1, line, recent_df, color, f"短線{i+1}-")
        
        print(f"   長期趨勢線: {len(long_term_lines)} 條")
        print(f"   短期趨勢線: {len(short_term_lines)} 條")
        
        # 標記買入信號
        print("   標記買入信號...")
        buy_signal_count = 0
        signal_colors = {1: 'yellow', 2: 'orange', 3: 'gold', 4: 'lime', 5: 'red'}
        signal_sizes = {1: 100, 2: 150, 3: 200, 4: 250, 5: 300}
        
        for _, row in buy_signals.iterrows():
            if row['breakthrough_descending_trendline_buy'] == 'O':
                date_str = row['date']
                matching_dates = recent_df[recent_df.index.strftime('%Y-%m-%d') == date_str]
                if not matching_dates.empty:
                    buy_date = matching_dates.index[0]
                    buy_low = matching_dates.iloc[0]['Low']
                    buy_mark_price = buy_low * 0.97
                    
                    strength = int(row['signal_strength'])
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
        
        # 調整Y軸範圍
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
            if row['breakthrough_descending_trendline_buy'] == 'O':
                date_str = row['date']
                matching_dates = recent_df[recent_df.index.strftime('%Y-%m-%d') == date_str]
                if not matching_dates.empty:
                    buy_date = matching_dates.index[0]
                    buy_volume = matching_dates.iloc[0]['Volume']
                    volume_ratio = row['volume_ratio']
                    
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
    signals = buy_signals[buy_signals['breakthrough_descending_trendline_buy'] == 'O']
    
    if len(signals) == 0:
        print(f"\n📊 買入信號統計：無買入信號")
        return
    
    print(f"\n📊 買入信號統計：")
    print(f"   總信號數量: {len(signals)}")
    print(f"   平均信號強度: {signals['signal_strength'].mean():.2f}/5")
    
    # 按類型統計
    long_term_count = len(signals[signals['breakthrough_type'] == 'long_term_two_point'])
    short_term_count = len(signals[signals['breakthrough_type'] == 'short_term_multi_point'])
    print(f"   長期趨勢線突破: {long_term_count} 個")
    print(f"   短期趨勢線突破: {short_term_count} 個")
    
    # 信號強度分布
    strength_dist = signals['signal_strength'].value_counts().sort_index()
    print(f"   信號強度分布:")
    for strength, count in strength_dist.items():
        print(f"     {strength}分: {count} 個")
    
    # 其他統計
    print(f"   平均時間跨度: {signals['days_span'].mean():.0f} 天")
    print(f"   平均突破幅度: {signals['breakthrough_percentage'].mean():.2f}%")
    print(f"   平均成交量比率: {signals['volume_ratio'].mean():.2f}x")
    
    # 最佳信號
    best_signal = signals.loc[signals['signal_strength'].idxmax()]
    print(f"\n🏆 最強信號 ({best_signal['signal_strength']}/5):")
    print(f"   日期: {best_signal['date']}")
    print(f"   類型: {'長期' if best_signal['breakthrough_type'] == 'long_term_two_point' else '短期'}趨勢線")
    print(f"   時間跨度: {best_signal['days_span']} 天")
    print(f"   突破幅度: {best_signal['breakthrough_percentage']:.2f}%")
    print(f"   成交量比率: {best_signal['volume_ratio']:.2f}x")


def descending_trendline_test(stock_id='2330', days=360):
    """下降趨勢線突破測試"""
    print(f"\n{'='*70}")
    print(f"下降趨勢線突破買入規則測試：{stock_id}")
    print(f"{'='*70}")
    
    try:
        # 導入必要模塊
        from src.validate_buy_rule import load_stock_data
        from src.buyRule.breakthrough_descending_trendline import (
            check_breakthrough_descending_trendline_buy_rule,
        )
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
        
        # 識別轉折點
        print("🔍 執行轉折點識別...")
        turning_points_df = identify_turning_points(recent_df)
        
        # 找出所有下降趨勢線
        print("🔍 識別所有下降趨勢線...")
        trendlines = find_all_descending_trendlines(recent_df, turning_points_df)
        
        # 執行下降趨勢線突破買入規則分析
        print("🚀 執行下降趨勢線突破買入分析...")
        buy_signals = check_breakthrough_descending_trendline_buy_rule(
            recent_df, turning_points_df,
            min_days_long_term=180,
            min_points_short_term=3,
            volume_confirmation=True,
            volume_multiplier=1.2,
            min_breakthrough_percentage=0.5
        )
        
        # 創建圖表（顯示所有趨勢線）
        print("🎨 創建分析圖表...")
        create_descending_trendline_chart(
            stock_id, recent_df, turning_points_df, 
            buy_signals, trendlines, days
        )
        
        # 輸出買入信號統計
        print_buy_signal_stats(buy_signals)
        
        # 輸出趨勢線統計
        print(f"\n📈 趨勢線統計：")
        print(f"   長期趨勢線: {len(trendlines['long_term_lines'])} 條")
        print(f"   短期趨勢線: {len(trendlines['short_term_lines'])} 條")
        print(f"   總計: {len(trendlines['all_lines'])} 條")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主程式"""
    print("收盤站上下降趨勢線買入規則測試程式（修正版）")
    print("=" * 70)
    print("改進：")
    print("  ✓ 自動偵測並使用可用的中文字體")
    print("  ✓ 顯示所有有效的下降趨勢線（不只是被突破的）")
    print("  ✓ 改善視覺化效果")
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