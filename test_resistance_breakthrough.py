#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化的單股壓力線突破測試程式 - 標記所有轉折點、繪製被突破的壓力線與水平壓力線
"""

import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.buyRule.breakthrough_resistance_line import (
    check_resistance_line_breakthrough,
    get_resistance_line_data,
)

def find_breakthrough_resistance_lines(resistance_results, resistance_data, recent_df):
    """
    找出所有被突破的壓力線 - 直接使用後端計算的壓力線數據 (Trading Days邏輯)
    """
    breakthrough_lines = []
    
    # 建立日期索引查找表
    date_lookup = {idx.strftime('%Y-%m-%d'): idx for idx in recent_df.index}
    
    # 將 resistance_data 轉為以 date 為索引，方便查詢
    res_data_map = resistance_data.set_index('date')
    
    for _, row in resistance_results.iterrows():
        # 只處理被標記為突破的日子
        if row['resistance_line_breakthrough_check'] == 'O':
            date_str = row['date']
            
            # 確保有這天的壓力線數據
            if date_str in res_data_map.index:
                res_row = res_data_map.loc[date_str]
                
                # 確保有有效的壓力線點位 (斜率壓力線需要 point1 和 point2)
                p1_date_str = res_row.get('point1_date')
                p2_date_str = res_row.get('point2_date')
                
                if p1_date_str and p2_date_str:
                    breakthrough_date = date_lookup.get(date_str)
                    p1_date = date_lookup.get(p1_date_str)
                    p2_date = date_lookup.get(p2_date_str)
                    
                    if breakthrough_date and p1_date and p2_date:
                        resistance_price = res_row['resistance_price']
                        breakthrough_close = recent_df.loc[breakthrough_date]['Close']
                        
                        # 計算突破幅度
                        breakthrough_ratio = 0
                        if resistance_price > 0:
                            breakthrough_ratio = (breakthrough_close / resistance_price - 1) * 100
                            
                        line_info = {
                            'point1_date': p1_date,
                            'point1_price': res_row['point1_price'],
                            'point2_date': p2_date,
                            'point2_price': res_row['point2_price'],
                            'breakthrough_date': breakthrough_date,
                            'breakthrough_price': breakthrough_close,
                            'resistance_price': resistance_price,
                            'breakthrough_ratio': breakthrough_ratio
                        }
                        
                        breakthrough_lines.append(line_info)
    
    # 按突破日期排序
    breakthrough_lines.sort(key=lambda x: x['breakthrough_date'])
    
    return breakthrough_lines


def simple_resistance_test(stock_id='00631L', days=180):
    """
    簡化的壓力線測試 - 顯示被突破的壓力線與水平壓力線
    """
    print(f"\n{'='*60}")
    print(f"簡化測試：{stock_id} 單一壓力線突破分析")
    print(f"{'='*60}")
    
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
        resistance_data = get_resistance_line_data(recent_df, turning_points_df)
        
        # 創建簡化圖表
        print("🎨 創建簡化圖表...")
        create_simple_chart(
            stock_id,
            recent_df,
            turning_points_df,
            resistance_results,
            resistance_data,
            days
        )
        
        return True
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_simple_chart(stock_id, recent_df, turning_points_df, resistance_results, resistance_data, days):
    """
    創建簡化的圖表 - 標記轉折點、繪製被突破的斜率壓力線與水平壓力線
    """
    try:
        # 設置中文字體
        plt.figure(figsize=(16, 10))
        preferred_fonts = ['Microsoft JhengHei', 'Arial Unicode MS', 'SimHei']
        selected_font = None
        for font_name in preferred_fonts:
            try:
                fm.findfont(font_name, fallback_to_default=False)
                selected_font = font_name
                break
            except ValueError:
                continue
        if selected_font:
            plt.rcParams['font.sans-serif'] = [selected_font]
            print(f"   使用中文字體: {selected_font}")
        else:
            plt.rcParams['font.sans-serif'] = plt.rcParamsDefault['font.sans-serif']
            print("   使用預設字型（未找到預設的中文字體）")
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
                    color='black', linewidth=0.8, alpha=0.8, zorder=1)
            
            # 繪製實體K棒
            body_height = abs(close_price - open_price)
            body_bottom = min(open_price, close_price)
            bar_width = pd.Timedelta(days=0.6)
            
            if is_up:  # 上漲K棒（紅色空心）
                rect = plt.Rectangle((date - bar_width/2, body_bottom), 
                                   bar_width, body_height, 
                                   facecolor='white', edgecolor='red', 
                                   linewidth=1.2, alpha=1.0, zorder=2)
            else:  # 下跌K棒（綠色實心）
                rect = plt.Rectangle((date - bar_width/2, body_bottom), 
                                   bar_width, body_height, 
                                   facecolor='green', edgecolor='green', 
                                   linewidth=1.2, alpha=1.0, zorder=2)
            
            plt.gca().add_patch(rect)
        
        # 建立日期查找表（字串日期 → 實際索引）
        date_lookup = {idx.strftime('%Y-%m-%d'): idx for idx in recent_df.index}
        breakthrough_dates = []
        for _, row in resistance_results.iterrows():
            if row.get('resistance_line_breakthrough_check') == 'O':
                dt = date_lookup.get(row.get('date'))
                if dt is not None:
                    breakthrough_dates.append(dt)
        breakthrough_dates = sorted(set(breakthrough_dates))
        
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
        
        # 繪製所有被突破的斜率壓力線
        print("   分析並繪製被突破的壓力線...")
        breakthrough_resistance_lines = find_breakthrough_resistance_lines(
            resistance_results, resistance_data, recent_df
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
        
        # 繪製水平壓力線（使用最近一個轉折高點形成的水平壓力）
        # 只保留最近即將突破或已突破的水平線，避免圖表雜訊
        horizontal_lines = []
        current_price = None
        current_start = None
        current_source_date = ''
        prev_datetime = None
        
        for _, row in resistance_data.iterrows():
            date_str = row.get('date')
            horizontal_price = row.get('horizontal_resistance_price', np.nan)
            current_datetime = date_lookup.get(date_str)
            
            if current_datetime is None:
                continue
            
            if not pd.isna(horizontal_price):
                if (current_price is None) or (not np.isclose(horizontal_price, current_price, rtol=1e-05, atol=1e-05)):
                    if current_price is not None and prev_datetime is not None:
                        horizontal_lines.append({
                            'start': current_start,
                            'end': prev_datetime,
                            'price': current_price,
                            'source_date': current_source_date
                        })
                    current_price = float(horizontal_price)
                    current_start = current_datetime
                    current_source_date = row.get('last_high_point_date', '')
                prev_datetime = current_datetime
            else:
                if current_price is not None and prev_datetime is not None:
                    horizontal_lines.append({
                        'start': current_start,
                        'end': prev_datetime,
                        'price': current_price,
                        'source_date': current_source_date
                    })
                current_price = None
                current_start = None
                current_source_date = ''
                prev_datetime = None
        
        # 收尾：若最後一段仍有效，補上
        if current_price is not None and prev_datetime is not None:
            horizontal_lines.append({
                'start': current_start,
                'end': prev_datetime,
                'price': current_price,
                'source_date': current_source_date
            })
        
        if horizontal_lines:
            latest_date = recent_df.index[-1]
            latest_close = recent_df.iloc[-1]['Close']
            near_threshold = 0.01  # 1% 內視為接近突破（僅關注當日）
            
            filtered_lines = []
            for line in horizontal_lines:
                start = line['start']
                end = line['end']
                price = line['price']
                
                if start is None or end is None or pd.isna(price):
                    continue
                
                has_breakthrough_today = (
                    latest_date in breakthrough_dates and start <= latest_date <= end
                )
                near_break_today = False
                
                if (not has_breakthrough_today) and (end == latest_date) and price > 0:
                    if latest_close < price:
                        near_break_today = latest_close >= price * (1 - near_threshold)
                    else:
                        near_break_today = np.isclose(latest_close, price, rtol=0, atol=price * near_threshold)
                
                if has_breakthrough_today or near_break_today:
                    line['has_breakthrough_today'] = has_breakthrough_today
                    line['near_break_today'] = near_break_today
                    filtered_lines.append(line)
            
            if filtered_lines:
                print("   繪製符合條件的水平壓力線...")
                for idx, line in enumerate(filtered_lines):
                    start = line['start']
                    end = line['end']
                    price = line['price']
                    source = line['source_date']
                    label = '水平壓力線' if idx == 0 else ''
                    
                    plt.hlines(
                        price,
                        xmin=start,
                        xmax=end,
                        colors='darkorange',
                        linestyles=':',
                        linewidth=1.6,
                        alpha=0.75,
                        label=label,
                        zorder=7
                    )
                    
                    status = "今日已突破" if line.get('has_breakthrough_today') else "今日接近突破"
                    if source:
                        print(f"     {status}水平壓力線{idx+1}: 自 {source} 高點延伸，範圍 {start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')} @ {price:.2f}")
                    else:
                        print(f"     {status}水平壓力線{idx+1}: 範圍 {start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')} @ {price:.2f}")
            else:
                print("   未找到符合條件的水平壓力線")
        else:
            print("   未找到水平壓力線")
        
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
        stock_id = input("\n請輸入股票代碼 (預設00631L，輸入'quit'退出): ").strip()
        
        if stock_id.lower() == 'quit':
            print("程式結束")
            break
        
        if not stock_id:
            stock_id = '00631L'
        
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
