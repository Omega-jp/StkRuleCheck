#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化的單股壓力線突破測試程式 - 標記所有轉折高點和轉折低點，只畫被突破的壓力線
"""

import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


def find_breakthrough_resistance_lines(high_point_dates, high_point_prices, resistance_results, recent_df):
    """
    找出所有被突破的壓力線 - 基於實際算法邏輯（最近兩個轉折高點）
    """
    breakthrough_lines = []
    
    # 獲取所有突破日期和詳細資訊
    breakthrough_info = []
    for _, row in resistance_results.iterrows():
        if row['resistance_line_breakthrough_check'] == 'O':
            date_str = row['date']
            matching_dates = recent_df[recent_df.index.strftime('%Y-%m-%d') == date_str]
            if not matching_dates.empty:
                breakthrough_date = matching_dates.index[0]
                breakthrough_close = matching_dates.iloc[0]['Close']
                breakthrough_info.append({
                    'date': breakthrough_date,
                    'close': breakthrough_close
                })
    
    if not breakthrough_info or len(high_point_dates) < 2:
        return breakthrough_lines
    
    # 按時間順序排序突破點
    breakthrough_info.sort(key=lambda x: x['date'])
    
    # 對每個突破點，找出該時點的"當前最新壓力線"
    for breakthrough in breakthrough_info:
        breakthrough_date = breakthrough['date']
        breakthrough_close = breakthrough['close']
        
        # 找出突破日期之前的所有轉折高點
        available_high_points = []
        for i, high_date in enumerate(high_point_dates):
            if high_date < breakthrough_date:
                available_high_points.append({
                    'date': high_date,
                    'price': high_point_prices[i]
                })
        
        # 需要至少2個轉折高點才能形成壓力線
        if len(available_high_points) >= 2:
            # 取最近的兩個轉折高點（這就是突破當時的"當前最新壓力線"）
            point1 = available_high_points[-2]  # 倒數第二個
            point2 = available_high_points[-1]  # 最後一個
            
            # 計算突破點處的壓力線價格
            days_diff = (point2['date'] - point1['date']).days
            extend_days = (breakthrough_date - point2['date']).days
            
            if days_diff > 0 and extend_days >= 0:
                slope = (point2['price'] - point1['price']) / days_diff
                resistance_price = point2['price'] + slope * extend_days
                
                # 計算突破幅度
                if resistance_price > 0:
                    breakthrough_ratio = (breakthrough_close / resistance_price - 1) * 100
                    
                    # 確認確實是突破（收盤價高於壓力線）
                    if breakthrough_close > resistance_price:
                        line_info = {
                            'point1_date': point1['date'],
                            'point1_price': point1['price'],
                            'point2_date': point2['date'],
                            'point2_price': point2['price'],
                            'breakthrough_date': breakthrough_date,
                            'breakthrough_price': breakthrough_close,
                            'resistance_price': resistance_price,
                            'breakthrough_ratio': breakthrough_ratio
                        }
                        
                        breakthrough_lines.append(line_info)
    
    # 按突破日期排序
    breakthrough_lines.sort(key=lambda x: x['breakthrough_date'])
    
    return breakthrough_lines


def simple_resistance_test(stock_id='2330', days=180):
    """
    簡化的壓力線測試 - 只顯示最新一條壓力線
    """
    print(f"\n{'='*60}")
    print(f"簡化測試：{stock_id} 單一壓力線突破分析")
    print(f"{'='*60}")
    
    try:
        # 導入必要模塊
        from src.validate_buy_rule import load_stock_data
        from src.buyRule.breakthrough_resistance_line import check_resistance_line_breakthrough
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
        
        # 執行突破分析
        print("🚀 執行壓力線突破分析...")
        resistance_results = check_resistance_line_breakthrough(recent_df, turning_points_df)
        
        # 創建簡化圖表
        print("🎨 創建簡化圖表...")
        create_simple_chart(stock_id, recent_df, turning_points_df, resistance_results, days)
        
        return True
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_simple_chart(stock_id, recent_df, turning_points_df, resistance_results, days):
    """
    創建簡化的圖表 - 標記所有轉折高點和轉折低點，只畫被突破的壓力線
    """
    try:
        # 設置中文字體
        plt.figure(figsize=(16, 10))
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 主圖：K線圖
        plt.subplot(2, 1, 1)
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
            # 將標記放在最高價的上方（上方2%的位置）
            adjusted_high_prices = [price * 1.02 for price in high_point_prices]
            plt.scatter(high_point_dates, adjusted_high_prices, 
                       color='darkred', marker='^', s=40, 
                       label=f'轉折高點 ({len(high_point_dates)}個)', 
                       zorder=15, edgecolor='white', linewidth=1)
            print(f"   找到 {len(high_point_dates)} 個轉折高點")
        
        # 標記轉折低點（在最低價下方）
        if low_point_dates:
            # 將標記放在最低價的下方（下方2%的位置）
            adjusted_low_prices = [price * 0.98 for price in low_point_prices]
            plt.scatter(low_point_dates, adjusted_low_prices, 
                       color='darkblue', marker='v', s=40, 
                       label=f'轉折低點 ({len(low_point_dates)}個)', 
                       zorder=15, edgecolor='white', linewidth=1)
            print(f"   找到 {len(low_point_dates)} 個轉折低點")
        
        # 繪製所有被突破的壓力線
        print("   分析並繪製被突破的壓力線...")
        breakthrough_resistance_lines = find_breakthrough_resistance_lines(
            high_point_dates, high_point_prices, resistance_results, recent_df
        )
        
        if breakthrough_resistance_lines:
            colors = ['orange', 'purple', 'brown', 'darkred', 'navy', 'darkgreen']
            
            for i, line_info in enumerate(breakthrough_resistance_lines):
                color = colors[i % len(colors)]  # 循環使用顏色
                
                point1_date = line_info['point1_date']
                point1_price = line_info['point1_price']
                point2_date = line_info['point2_date']
                point2_price = line_info['point2_price']
                breakthrough_date = line_info['breakthrough_date']
                
                # 繪製壓力線基準段（實線，更細）
                plt.plot([point1_date, point2_date], 
                        [point1_price, point2_price], 
                        color=color, linewidth=2, linestyle='-', 
                        label=f'被突破壓力線{i+1}', zorder=8, alpha=0.9)
                
                # 延伸到突破點（虛線，更細）
                if breakthrough_date > point2_date:
                    days_diff = (point2_date - point1_date).days
                    extend_days = (breakthrough_date - point2_date).days
                    
                    if days_diff > 0:
                        slope = (point2_price - point1_price) / days_diff
                        extended_price = point2_price + slope * extend_days
                        
                        plt.plot([point2_date, breakthrough_date], 
                                [point2_price, extended_price], 
                                color=color, linewidth=1.5, linestyle='--', 
                                alpha=0.7, zorder=8)
                
                print(f"     被突破壓力線{i+1}: {point1_date.strftime('%Y-%m-%d')} ({point1_price:.2f}) → {point2_date.strftime('%Y-%m-%d')} ({point2_price:.2f})")
                print(f"       突破日期: {breakthrough_date.strftime('%Y-%m-%d')}")
            
            print(f"   共找到 {len(breakthrough_resistance_lines)} 條被突破的壓力線")
        else:
            print("   未找到被突破的壓力線")
        
        # 繪製5日移動平均線
        print("   繪製5日移動平均線...")
        if 'ma5' in recent_df.columns:
            plt.plot(dates, recent_df['ma5'], 
                    color='blue', linewidth=1.5, linestyle='-', 
                    alpha=0.8, label='5MA', zorder=5)
            print("   已添加5日移動平均線")
        
        # 標記突破信號（在K棒最低價下方，避免與轉折低點重疊）
        print("   標記突破信號...")
        breakthrough_count = 0
        for _, row in resistance_results.iterrows():
            if row['resistance_line_breakthrough_check'] == 'O':
                date_str = row['date']
                matching_dates = recent_df[recent_df.index.strftime('%Y-%m-%d') == date_str]
                if not matching_dates.empty:
                    breakthrough_date = matching_dates.index[0]
                    # 將突破信號標記在該K棒最低價的下方（下方4%的位置，避免與轉折低點重疊）
                    breakthrough_low = matching_dates.iloc[0]['Low']
                    breakthrough_mark_price = breakthrough_low * 0.96
                    
                    plt.scatter([breakthrough_date], [breakthrough_mark_price],
                               color='lime', marker='o', s=35, 
                               edgecolor='darkgreen', linewidth=1.5, 
                               label='突破信號' if breakthrough_count == 0 else '', zorder=16)
                    breakthrough_count += 1
        
        print(f"   找到 {breakthrough_count} 個突破信號")
        
        # 圖表設置
        plt.title(f'{stock_id} 壓力線突破分析（最近{days}天）', 
                 fontsize=16, fontweight='bold')
        plt.ylabel('價格', fontsize=12)
        plt.legend(fontsize=10, loc='upper left', bbox_to_anchor=(0, 1))
        plt.grid(True, alpha=0.3)
        
        # 調整Y軸範圍，確保所有標記都能顯示
        y_min = recent_df['Low'].min() * 0.94  # 預留更多空間給下方標記
        y_max = recent_df['High'].max() * 1.04  # 預留更多空間給上方標記
        plt.ylim(y_min, y_max)
        
        # 成交量圖
        plt.subplot(2, 1, 2)
        volume_colors = ['red' if closes.iloc[i] >= opens.iloc[i] else 'green' 
                        for i in range(len(dates))]
        
        plt.bar(dates, recent_df['Volume'], alpha=0.7, 
               color=volume_colors, width=0.8)
        
        plt.title('成交量', fontsize=14)
        plt.ylabel('成交量', fontsize=11)
        plt.xlabel('日期', fontsize=11)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # 保存圖表
        output_dir = 'output/test_charts'
        os.makedirs(output_dir, exist_ok=True)
        chart_path = f'{output_dir}/{stock_id}_resistance_with_turning_points.png'
        
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        print(f"✅ 圖表已保存至: {chart_path}")
        plt.show()
        
        # 輸出統計資訊
        print(f"\n📊 統計資訊：")
        print(f"   轉折高點數量: {len(high_point_dates)}")
        print(f"   轉折低點數量: {len(low_point_dates)}")
        print(f"   突破信號數量: {breakthrough_count}")
        
        # 顯示轉折點詳細資訊
        if high_point_dates:
            print(f"\n🔺 轉折高點詳細資訊：")
            for i, (date, price) in enumerate(zip(high_point_dates, high_point_prices)):
                print(f"   {i+1}. {date.strftime('%Y-%m-%d')}: {price:.2f}")
        
        if low_point_dates:
            print(f"\n🔻 轉折低點詳細資訊：")
            for i, (date, price) in enumerate(zip(low_point_dates, low_point_prices)):
                print(f"   {i+1}. {date.strftime('%Y-%m-%d')}: {price:.2f}")
        
        # 顯示被突破壓力線詳細資訊
        if breakthrough_resistance_lines:
            print(f"\n📈 被突破的壓力線詳細資訊：")
            for i, line_info in enumerate(breakthrough_resistance_lines):
                print(f"   {i+1}. 壓力線: {line_info['point1_date'].strftime('%Y-%m-%d')} → {line_info['point2_date'].strftime('%Y-%m-%d')}")
                print(f"      突破日期: {line_info['breakthrough_date'].strftime('%Y-%m-%d')}")
                print(f"      壓力線價格: {line_info['resistance_price']:.2f}")
                print(f"      突破收盤價: {line_info['breakthrough_price']:.2f}")
                print(f"      突破幅度: {line_info['breakthrough_ratio']:.2f}%")
                print()
        
    except Exception as e:
        print(f"❌ 創建圖表時發生錯誤: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主程式"""
    print("修正版壓力線測試程式 - 標記所有轉折點，只畫被突破的壓力線")
    print("=" * 65)
    
    while True:
        stock_id = input("\n請輸入股票代碼 (預設2330，輸入'quit'退出): ").strip()
        
        if stock_id.lower() == 'quit':
            print("程式結束")
            break
        
        if not stock_id:
            stock_id = '2330'
        
        try:
            days_input = input("請輸入顯示天數 (預設180天): ").strip()
            days = int(days_input) if days_input else 180
        except ValueError:
            days = 180
        
        print(f"\n開始測試：{stock_id}，顯示最近 {days} 天...")
        
        success = simple_resistance_test(stock_id, days)
        
        if success:
            print(f"\n🎉 {stock_id} 測試完成！")
        else:
            print(f"\n❌ {stock_id} 測試失敗！")
        
        continue_test = input("\n是否測試其他股票？(y/n): ").strip().lower()
        if continue_test != 'y':
            break

if __name__ == "__main__":
    main()