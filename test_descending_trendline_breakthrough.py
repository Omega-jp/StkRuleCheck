#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收盤站上下降趨勢線買入規則測試程式 - 標記所有轉折點，只畫被突破的下降趨勢線
"""

import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


def find_breakthrough_descending_lines(high_point_dates, high_point_prices, buy_signals, recent_df):
    """
    找出所有被突破的下降趨勢線 - 基於買入規則的實際算法邏輯
    """
    breakthrough_lines = []
    
    # 獲取所有買入信號和詳細資訊
    buy_info = []
    for _, row in buy_signals.iterrows():
        if row['breakthrough_descending_trendline_buy'] == 'O':
            date_str = row['date']
            matching_dates = recent_df[recent_df.index.strftime('%Y-%m-%d') == date_str]
            if not matching_dates.empty:
                buy_date = matching_dates.index[0]
                buy_close = matching_dates.iloc[0]['Close']
                buy_info.append({
                    'date': buy_date,
                    'close': buy_close,
                    'signal_strength': row['signal_strength'],
                    'breakthrough_type': row['breakthrough_type'],
                    'days_span': row['days_span'],
                    'breakthrough_percentage': row['breakthrough_percentage'],
                    'volume_ratio': row['volume_ratio']
                })
    
    if not buy_info or len(high_point_dates) < 2:
        return breakthrough_lines
    
    # 按時間順序排序買入點
    buy_info.sort(key=lambda x: x['date'])
    
    # 對每個買入點，找出該時點的下降趨勢線
    for buy_signal in buy_info:
        buy_date = buy_signal['date']
        buy_close = buy_signal['close']
        breakthrough_type = buy_signal['breakthrough_type']
        
        # 找出買入日期之前的所有轉折高點
        available_high_points = []
        for i, high_date in enumerate(high_point_dates):
            if high_date < buy_date:
                available_high_points.append({
                    'date': high_date,
                    'price': high_point_prices[i]
                })
        
        if len(available_high_points) < 2:
            continue
        
        # 根據突破類型確定趨勢線
        latest_high_point = available_high_points[-1]

        if breakthrough_type == 'long_term_two_point':
            # 僅繪製與最近一個轉折高點相關的長期趨勢線
            found_line = False
            for i in range(len(available_high_points) - 1):
                point1 = available_high_points[i]
                point2 = latest_high_point

                if point1['date'] == point2['date']:
                    continue

                days_span = (point2['date'] - point1['date']).days
                if days_span >= 180 and point2['price'] < point1['price']:
                    line_info = create_line_info(point1, point2, buy_signal, buy_date, buy_close)
                    if line_info:
                        breakthrough_lines.append(line_info)
                        found_line = True
                        break

            if not found_line:
                continue

        else:  # short_term_multi_point
            if len(available_high_points) >= 2:
                point1 = available_high_points[-2]
                point2 = latest_high_point

                days_span = (point2['date'] - point1['date']).days
                if days_span < 180 and point2['price'] < point1['price']:
                    line_info = create_line_info(point1, point2, buy_signal, buy_date, buy_close)
                    if line_info:
                        breakthrough_lines.append(line_info)
    
    # 按買入日期排序，去除重複
    if breakthrough_lines:
        latest_line_high_date = max(line['point2_date'] for line in breakthrough_lines)
        lines_with_latest_high = [line for line in breakthrough_lines if line['point2_date'] == latest_line_high_date]
        if lines_with_latest_high:
            breakthrough_lines = lines_with_latest_high

    breakthrough_lines.sort(key=lambda x: x['breakthrough_date'])
    
    # 去除重複的趨勢線（相同的兩個點）
    unique_lines = []
    seen_lines = set()
    for line in breakthrough_lines:
        line_key = (line['point1_date'], line['point2_date'], line['breakthrough_date'])
        if line_key not in seen_lines:
            unique_lines.append(line)
            seen_lines.add(line_key)
    
    return unique_lines


def create_line_info(point1, point2, buy_signal, buy_date, buy_close):
    """
    創建趨勢線資訊
    """
    # 計算買入點處的趨勢線價格
    days_diff = (point2['date'] - point1['date']).days
    extend_days = (buy_date - point2['date']).days
    
    if days_diff > 0 and extend_days >= 0:
        slope = (point2['price'] - point1['price']) / days_diff
        trendline_price = point2['price'] + slope * extend_days
        
        # 計算突破幅度
        if trendline_price > 0:
            breakthrough_ratio = (buy_close / trendline_price - 1) * 100
            
            # 確認確實是突破（收盤價高於趨勢線）
            if buy_close > trendline_price:
                return {
                    'point1_date': point1['date'],
                    'point1_price': point1['price'],
                    'point2_date': point2['date'],
                    'point2_price': point2['price'],
                    'breakthrough_date': buy_date,
                    'breakthrough_price': buy_close,
                    'trendline_price': trendline_price,
                    'breakthrough_ratio': breakthrough_ratio,
                    'signal_strength': buy_signal['signal_strength'],
                    'breakthrough_type': buy_signal['breakthrough_type'],
                    'days_span': buy_signal['days_span'],
                    'volume_ratio': buy_signal['volume_ratio'],
                    'slope': slope
                }
    
    return None


def descending_trendline_test(stock_id='2330', days=360):
    """
    下降趨勢線突破測試
    """
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
        
        # 取最近的數據（需要更多數據來識別長期趨勢線）
        recent_df = df.tail(days)
        print(f"📊 分析最近 {len(recent_df)} 天的數據")
        
        # 識別轉折點
        print("🔍 執行轉折點識別...")
        turning_points_df = identify_turning_points(recent_df)
        
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
        
        # 創建圖表
        print("🎨 創建分析圖表...")
        create_descending_trendline_chart(stock_id, recent_df, turning_points_df, buy_signals, days)
        
        # 輸出買入信號統計
        print_buy_signal_stats(buy_signals)
        
        return True
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_descending_trendline_chart(stock_id, recent_df, turning_points_df, buy_signals, days):
    """
    創建下降趨勢線突破分析圖表
    """
    try:
        # 設置中文字體
        plt.figure(figsize=(18, 12))
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 主圖：K線圖
        plt.subplot(3, 1, (1, 2))  # 佔上面2/3的空間
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
            
            if is_up:  # 上漲K棒（紅色空心）
                rect = plt.Rectangle((date - bar_width/2, body_bottom), 
                                   bar_width, body_height, 
                                   facecolor='white', edgecolor='red', 
                                   linewidth=1.2, alpha=0.9)
            else:  # 下跌K棒（綠色實心）
                rect = plt.Rectangle((date - bar_width/2, body_bottom), 
                                   bar_width, body_height, 
                                   facecolor='green', edgecolor='green', 
                                   linewidth=1.2, alpha=0.9)
            
            plt.gca().add_patch(rect)
        
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
        
        # 標記轉折高點（在最高價上方）
        if high_point_dates:
            adjusted_high_prices = [price * 1.02 for price in high_point_prices]
            plt.scatter(high_point_dates, adjusted_high_prices, 
                       color='darkred', marker='^', s=50, 
                       label=f'轉折高點 ({len(high_point_dates)}個)', 
                       zorder=15, edgecolor='white', linewidth=1)
            print(f"   找到 {len(high_point_dates)} 個轉折高點")
        
        # 標記轉折低點（在最低價下方）
        if low_point_dates:
            adjusted_low_prices = [price * 0.98 for price in low_point_prices]
            plt.scatter(low_point_dates, adjusted_low_prices, 
                       color='darkblue', marker='v', s=50, 
                       label=f'轉折低點 ({len(low_point_dates)}個)', 
                       zorder=15, edgecolor='white', linewidth=1)
            print(f"   找到 {len(low_point_dates)} 個轉折低點")
        
        # 繪製所有被突破的下降趨勢線
        print("   分析並繪製被突破的下降趨勢線...")
        breakthrough_lines = find_breakthrough_descending_lines(
            high_point_dates, high_point_prices, buy_signals, recent_df
        )
        
        if breakthrough_lines:
            colors = ['orange', 'purple', 'brown', 'darkred', 'navy', 'darkgreen', 'maroon', 'teal']
            
            for i, line_info in enumerate(breakthrough_lines):
                color = colors[i % len(colors)]
                
                point1_date = line_info['point1_date']
                point1_price = line_info['point1_price']
                point2_date = line_info['point2_date']
                point2_price = line_info['point2_price']
                breakthrough_date = line_info['breakthrough_date']
                signal_strength = line_info['signal_strength']
                breakthrough_type = line_info['breakthrough_type']
                
                # 趨勢線標籤
                line_type_str = "長期" if breakthrough_type == 'long_term_two_point' else "短期"
                line_label = f'{line_type_str}下降線{i+1} (強度:{signal_strength})'
                
                # 繪製下降趨勢線基準段（實線）
                plt.plot([point1_date, point2_date], 
                        [point1_price, point2_price], 
                        color=color, linewidth=2.5, linestyle='-', 
                        label=line_label, zorder=10, alpha=0.9)
                
                # 延伸到突破點（虛線）
                if breakthrough_date > point2_date:
                    days_diff = (point2_date - point1_date).days
                    extend_days = (breakthrough_date - point2_date).days
                    
                    if days_diff > 0:
                        slope = (point2_price - point1_price) / days_diff
                        extended_price = point2_price + slope * extend_days
                        
                        plt.plot([point2_date, breakthrough_date], 
                                [point2_price, extended_price], 
                                color=color, linewidth=2, linestyle='--', 
                                alpha=0.8, zorder=10)
                
                print(f"     {line_type_str}下降趨勢線{i+1}: {point1_date.strftime('%Y-%m-%d')} ({point1_price:.2f}) → {point2_date.strftime('%Y-%m-%d')} ({point2_price:.2f})")
                print(f"       突破日期: {breakthrough_date.strftime('%Y-%m-%d')} | 信號強度: {signal_strength}/5")
                print(f"       時間跨度: {line_info['days_span']}天 | 突破幅度: {line_info['breakthrough_ratio']:.2f}%")
            
            print(f"   共找到 {len(breakthrough_lines)} 條被突破的下降趨勢線")
        else:
            print("   未找到被突破的下降趨勢線")
        
        # 繪製5日移動平均線
        print("   繪製5日移動平均線...")
        if 'ma5' in recent_df.columns:
            plt.plot(dates, recent_df['ma5'], 
                    color='blue', linewidth=1.5, linestyle='-', 
                    alpha=0.8, label='5MA', zorder=5)
        
        # 標記買入信號（不同信號強度用不同大小）
        print("   標記買入信號...")
        buy_signal_count = 0
        signal_colors = {1: 'yellow', 2: 'orange', 3: 'gold', 4: 'lime', 5: 'red'}
        signal_sizes = {1: 30, 2: 40, 3: 50, 4: 60, 5: 80}
        
        for _, row in buy_signals.iterrows():
            if row['breakthrough_descending_trendline_buy'] == 'O':
                date_str = row['date']
                matching_dates = recent_df[recent_df.index.strftime('%Y-%m-%d') == date_str]
                if not matching_dates.empty:
                    buy_date = matching_dates.index[0]
                    buy_low = matching_dates.iloc[0]['Low']
                    buy_mark_price = buy_low * 0.95
                    
                    strength = int(row['signal_strength'])
                    color = signal_colors.get(strength, 'lime')
                    size = signal_sizes.get(strength, 50)
                    
                    plt.scatter([buy_date], [buy_mark_price],
                               color=color, marker='P', s=size, 
                               edgecolor='darkgreen', linewidth=2, 
                               label=f'買入信號強度{strength}' if buy_signal_count == 0 else '', zorder=20)
                    buy_signal_count += 1
        
        print(f"   找到 {buy_signal_count} 個買入信號")
        
        # 圖表設置
        plt.title(f'{stock_id} 收盤站上下降趨勢線買入分析（最近{days}天）', 
                 fontsize=16, fontweight='bold')
        plt.ylabel('價格', fontsize=12)
        plt.legend(fontsize=9, loc='upper left', bbox_to_anchor=(0, 1))
        plt.grid(True, alpha=0.3)
        
        # 調整Y軸範圍
        y_min = recent_df['Low'].min() * 0.93
        y_max = recent_df['High'].max() * 1.05
        plt.ylim(y_min, y_max)
        
        # 成交量圖
        plt.subplot(3, 1, 3)
        volume_colors = ['red' if closes.iloc[i] >= opens.iloc[i] else 'green' 
                        for i in range(len(dates))]
        
        bars = plt.bar(dates, recent_df['Volume'], alpha=0.7, 
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
                    
                    # 在成交量柱上方標記
                    plt.scatter([buy_date], [buy_volume * 1.1],
                               color='gold', marker='P', s=40, 
                               edgecolor='red', linewidth=1, zorder=10)
                    
                    # 添加成交量比率文字
                    plt.text(buy_date, buy_volume * 1.2, f'{volume_ratio:.1f}x',
                            ha='center', va='bottom', fontsize=8, 
                            bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.7))
        
        plt.title('成交量 (標記買入信號對應的放量)', fontsize=12)
        plt.ylabel('成交量', fontsize=10)
        plt.xlabel('日期', fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # 保存圖表
        output_dir = 'output/test_charts'
        os.makedirs(output_dir, exist_ok=True)
        chart_path = f'{output_dir}/{stock_id}_descending_trendline_buy.png'
        
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        print(f"✅ 圖表已保存至: {chart_path}")
        plt.show()
        
        # 輸出統計資訊
        print(f"\n📊 統計資訊：")
        print(f"   轉折高點數量: {len(high_point_dates)}")
        print(f"   轉折低點數量: {len(low_point_dates)}")
        print(f"   買入信號數量: {buy_signal_count}")
        print(f"   被突破下降趨勢線數量: {len(breakthrough_lines) if breakthrough_lines else 0}")
        
        # 顯示被突破下降趨勢線詳細資訊
        if breakthrough_lines:
            print(f"\n📈 被突破的下降趨勢線詳細資訊：")
            for i, line_info in enumerate(breakthrough_lines):
                line_type = "長期" if line_info['breakthrough_type'] == 'long_term_two_point' else "短期"
                print(f"   {i+1}. {line_type}下降趨勢線:")
                print(f"      連接點: {line_info['point1_date'].strftime('%Y-%m-%d')} ({line_info['point1_price']:.2f}) → {line_info['point2_date'].strftime('%Y-%m-%d')} ({line_info['point2_price']:.2f})")
                print(f"      突破日期: {line_info['breakthrough_date'].strftime('%Y-%m-%d')}")
                print(f"      趨勢線價格: {line_info['trendline_price']:.2f}")
                print(f"      突破收盤價: {line_info['breakthrough_price']:.2f}")
                print(f"      突破幅度: {line_info['breakthrough_ratio']:.2f}%")
                print(f"      信號強度: {line_info['signal_strength']}/5")
                print(f"      時間跨度: {line_info['days_span']}天")
                print(f"      成交量比率: {line_info['volume_ratio']:.2f}x")
                print()
        
    except Exception as e:
        print(f"❌ 創建圖表時發生錯誤: {e}")
        import traceback
        traceback.print_exc()


def print_buy_signal_stats(buy_signals):
    """
    輸出買入信號統計資訊
    """
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


def main():
    """主程式"""
    print("收盤站上下降趨勢線買入規則測試程式")
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
