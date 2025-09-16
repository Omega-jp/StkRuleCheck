#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轉折點算法執行過程診斷程式
逐步追蹤 turning_point_identification.py 的執行邏輯
"""

import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


def debug_turning_point_execution(stock_id='2330', days=60):
    """
    逐步追蹤轉折點識別算法的執行過程
    """
    print(f"\n{'='*80}")
    print(f"轉折點算法執行過程診斷：{stock_id}")
    print(f"{'='*80}")
    
    try:
        # 導入必要模塊
        from src.validate_buy_rule import load_stock_data
        
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
        
        # 手動執行轉折點識別算法的每個步驟
        print(f"\n🔍 開始手動執行轉折點識別算法...")
        
        # 步驟1：計算收盤價與MA5的關係
        print(f"\n1️⃣ 步驟1：計算收盤價與MA5的關係")
        recent_df['close_above_ma5'] = recent_df['Close'] > recent_df['ma5']
        recent_df['prev_close_above_ma5'] = recent_df['close_above_ma5'].shift(1)
        
        # 顯示最近10天的關係
        print(f"   最近10天的收盤價vs MA5關係：")
        last_10 = recent_df.tail(10)
        for i, (date, row) in enumerate(last_10.iterrows()):
            above_current = "✓" if row['close_above_ma5'] else "✗"
            above_prev = "✓" if pd.notna(row['prev_close_above_ma5']) and row['prev_close_above_ma5'] else "✗"
            print(f"   {i+1:2d}. {date.strftime('%Y-%m-%d')}: C={row['Close']:6.2f}, MA5={row['ma5']:6.2f}, "
                  f"當前={above_current}, 前日={above_prev}")
        
        # 步驟2：識別穿越點
        print(f"\n2️⃣ 步驟2：識別MA5穿越點")
        
        # 處理NaN值問題：填充第一行的prev_close_above_ma5
        recent_df['prev_close_above_ma5'] = recent_df['prev_close_above_ma5'].fillna(recent_df['close_above_ma5'])
        
        # 確保都是布林值
        recent_df['close_above_ma5'] = recent_df['close_above_ma5'].astype(bool)
        recent_df['prev_close_above_ma5'] = recent_df['prev_close_above_ma5'].astype(bool)
        
        recent_df['cross_up'] = (~recent_df['prev_close_above_ma5']) & recent_df['close_above_ma5']
        recent_df['cross_down'] = recent_df['prev_close_above_ma5'] & (~recent_df['close_above_ma5'])
        
        cross_up_dates = recent_df[recent_df['cross_up']].index
        cross_down_dates = recent_df[recent_df['cross_down']].index
        
        print(f"   向上穿越MA5的日期 ({len(cross_up_dates)}個)：")
        for i, date in enumerate(cross_up_dates):
            row = recent_df.loc[date]
            print(f"     {i+1}. {date.strftime('%Y-%m-%d')}: C={row['Close']:6.2f}, MA5={row['ma5']:6.2f}")
        
        print(f"   向下穿越MA5的日期 ({len(cross_down_dates)}個)：")
        for i, date in enumerate(cross_down_dates):
            row = recent_df.loc[date]
            print(f"     {i+1}. {date.strftime('%Y-%m-%d')}: C={row['Close']:6.2f}, MA5={row['ma5']:6.2f}")
        
        # 步驟3：建立穿越事件時間軸
        print(f"\n3️⃣ 步驟3：建立穿越事件時間軸")
        cross_events = []
        
        for date in cross_up_dates:
            cross_events.append((date, 'up'))
        for date in cross_down_dates:
            cross_events.append((date, 'down'))
        
        cross_events.sort(key=lambda x: x[0])
        
        print(f"   時間軸上的穿越事件 ({len(cross_events)}個)：")
        for i, (date, direction) in enumerate(cross_events):
            arrow = "📈" if direction == 'up' else "📉"
            print(f"     {i+1}. {date.strftime('%Y-%m-%d')} - {arrow} {direction}")
        
        # 步驟4：根據穿越事件尋找轉折點
        print(f"\n4️⃣ 步驟4：根據穿越事件尋找轉折點")
        
        identified_turning_points = []
        
        for i, (cross_date, cross_type) in enumerate(cross_events):
            print(f"\n   處理穿越事件 {i+1}: {cross_date.strftime('%Y-%m-%d')} ({cross_type})")
            
            # 確定搜尋區間
            if i == 0:
                # 第一個穿越事件，從數據開始到穿越點
                start_date = recent_df.index[0]
            else:
                # 從上一個穿越事件到當前穿越事件
                start_date = cross_events[i-1][0]
            
            end_date = cross_date
            
            print(f"     搜尋區間：{start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
            
            # 獲取區間數據
            if start_date <= end_date:
                period_data = recent_df.loc[start_date:end_date]
                print(f"     區間數據筆數：{len(period_data)}")
                
                if cross_type == 'up':
                    # 向上穿越時，找該區間的最低點
                    if len(period_data) > 0:
                        min_idx = period_data['Low'].idxmin()
                        min_value = period_data['Low'].min()
                        min_date_str = min_idx.strftime('%Y-%m-%d')
                        
                        print(f"     🔻 找到轉折低點：{min_date_str} (價格: {min_value:.2f})")
                        identified_turning_points.append((min_idx, 'low', min_value))
                        
                        # 顯示該區間的所有低點以供比較
                        print(f"     該區間所有日期的低點：")
                        for j, (period_date, period_row) in enumerate(period_data.iterrows()):
                            mark = " <<<< 最低點" if period_date == min_idx else ""
                            print(f"       {period_date.strftime('%Y-%m-%d')}: {period_row['Low']:6.2f}{mark}")
                
                elif cross_type == 'down':
                    # 向下穿越時，找該區間的最高點
                    if len(period_data) > 0:
                        max_idx = period_data['High'].idxmax()
                        max_value = period_data['High'].max()
                        max_date_str = max_idx.strftime('%Y-%m-%d')
                        
                        print(f"     🔺 找到轉折高點：{max_date_str} (價格: {max_value:.2f})")
                        identified_turning_points.append((max_idx, 'high', max_value))
                        
                        # 顯示該區間的所有高點以供比較
                        print(f"     該區間所有日期的高點：")
                        for j, (period_date, period_row) in enumerate(period_data.iterrows()):
                            mark = " <<<< 最高點" if period_date == max_idx else ""
                            print(f"       {period_date.strftime('%Y-%m-%d')}: {period_row['High']:6.2f}{mark}")
            else:
                print(f"     ⚠️ 無效區間：起始日期晚於結束日期")
        
        # 步驟5：總結手動識別的結果
        print(f"\n5️⃣ 步驟5：手動識別結果總結")
        print(f"   總共識別到 {len(identified_turning_points)} 個轉折點：")
        
        high_points = [tp for tp in identified_turning_points if tp[1] == 'high']
        low_points = [tp for tp in identified_turning_points if tp[1] == 'low']
        
        print(f"   轉折高點 ({len(high_points)}個)：")
        for i, (date, _, price) in enumerate(high_points):
            print(f"     {i+1}. {date.strftime('%Y-%m-%d')}: {price:.2f}")
        
        print(f"   轉折低點 ({len(low_points)}個)：")
        for i, (date, _, price) in enumerate(low_points):
            print(f"     {i+1}. {date.strftime('%Y-%m-%d')}: {price:.2f}")
        
        # 🔍 新增：檢查轉折點交錯邏輯
        print(f"\n📊 轉折點交錯檢查：")
        
        # 合併所有轉折點並按時間排序
        all_turning_points = []
        for date, point_type, price in identified_turning_points:
            all_turning_points.append((date, point_type, price))
        
        all_turning_points.sort(key=lambda x: x[0])
        
        print(f"   按時間順序的轉折點：")
        for i, (date, point_type, price) in enumerate(all_turning_points):
            symbol = "🔺" if point_type == 'high' else "🔻"
            print(f"     {i+1}. {date.strftime('%Y-%m-%d')} {symbol} {point_type} ({price:.2f})")
        
        # 檢查是否有連續相同類型的轉折點
        consecutive_issues = []
        for i in range(1, len(all_turning_points)):
            prev_type = all_turning_points[i-1][1]
            curr_type = all_turning_points[i][1]
            if prev_type == curr_type:
                consecutive_issues.append({
                    'index': i,
                    'prev': all_turning_points[i-1],
                    'curr': all_turning_points[i]
                })
        
        if consecutive_issues:
            print(f"\n⚠️ 發現 {len(consecutive_issues)} 個連續相同類型轉折點問題：")
            for issue in consecutive_issues:
                prev_date, prev_type, prev_price = issue['prev']
                curr_date, curr_type, curr_price = issue['curr']
                print(f"     連續 {prev_type}: {prev_date.strftime('%Y-%m-%d')} → {curr_date.strftime('%Y-%m-%d')}")
                
                # 分析這兩個轉折點之間的穿越事件
                between_events = [event for event in cross_events 
                                if prev_date < event[0] <= curr_date]
                print(f"       中間的穿越事件 ({len(between_events)}個): ", end="")
                if between_events:
                    event_summary = [f"{e[0].strftime('%m-%d')}({e[1]})" for e in between_events]
                    print(" → ".join(event_summary))
                else:
                    print("無")
        else:
            print(f"   ✅ 所有轉折點都正確交錯")
        
        # 檢查穿越事件與轉折點的對應關係
        print(f"\n🔄 穿越事件與轉折點對應關係檢查：")
        for i, (cross_date, cross_type) in enumerate(cross_events):
            print(f"   {i+1:2d}. {cross_date.strftime('%Y-%m-%d')} ({cross_type}):", end=" ")
            
            # 找出這個穿越事件應該對應的轉折點
            expected_type = 'low' if cross_type == 'up' else 'high'
            
            # 查找在這個穿越事件之後是否有對應的轉折點被標記
            found_corresponding = False
            for tp_date, tp_type, tp_price in identified_turning_points:
                # 轉折點應該在穿越事件的區間內
                if i == 0:
                    start_range = recent_df.index[0]
                else:
                    start_range = cross_events[i-1][0]
                
                if start_range <= tp_date <= cross_date and tp_type == expected_type:
                    print(f"✅ 對應 {tp_date.strftime('%Y-%m-%d')} {expected_type}")
                    found_corresponding = True
                    break
            
            if not found_corresponding:
                print(f"❌ 缺少對應的轉折{expected_type}點")
                
                # 詳細分析這個區間
                if i == 0:
                    period_start = recent_df.index[0]
                else:
                    period_start = cross_events[i-1][0]
                
                period_end = cross_date
                period_data = recent_df.loc[period_start:period_end]
                
                if expected_type == 'low':
                    actual_min_idx = period_data['Low'].idxmin()
                    actual_min_price = period_data['Low'].min()
                    print(f"       應該標記: {actual_min_idx.strftime('%Y-%m-%d')} 低點 ({actual_min_price:.2f})")
                else:
                    actual_max_idx = period_data['High'].idxmax()
                    actual_max_price = period_data['High'].max()
                    print(f"       應該標記: {actual_max_idx.strftime('%Y-%m-%d')} 高點 ({actual_max_price:.2f})")
        
        # 步驟6：與原始算法結果比較
        print(f"\n6️⃣ 步驟6：與原始算法結果比較")
        try:
            from src.baseRule.turning_point_identification import identify_turning_points
            original_result = identify_turning_points(recent_df)
            
            orig_high_points = original_result[original_result['turning_high_point'] == 'O']
            orig_low_points = original_result[original_result['turning_low_point'] == 'O']
            
            print(f"   原始算法結果：")
            print(f"     轉折高點：{len(orig_high_points)} 個")
            print(f"     轉折低點：{len(orig_low_points)} 個")
            
            print(f"   原始算法的轉折低點：")
            for i, (_, row) in enumerate(orig_low_points.iterrows()):
                print(f"     {i+1}. {row['date']}")
            
            # 檢查是否有遺漏
            manual_low_dates = set([tp[0].strftime('%Y-%m-%d') for tp in low_points])
            original_low_dates = set(orig_low_points['date'].tolist())
            
            missing_in_original = manual_low_dates - original_low_dates
            extra_in_original = original_low_dates - manual_low_dates
            
            if missing_in_original:
                print(f"   ⚠️ 原始算法遺漏的轉折低點：{missing_in_original}")
            if extra_in_original:
                print(f"   ⚠️ 原始算法多出的轉折低點：{extra_in_original}")
            
            if not missing_in_original and not extra_in_original:
                print(f"   ✅ 手動執行結果與原始算法一致")
            
        except Exception as e:
            print(f"   ❌ 無法載入原始算法進行比較：{e}")
        
        # 創建診斷圖表
        create_debug_chart(stock_id, recent_df, cross_events, identified_turning_points)
        
        return True
        
    except Exception as e:
        print(f"❌ 診斷過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_debug_chart(stock_id, recent_df, cross_events, identified_turning_points):
    """
    創建診斷圖表
    """
    try:
        plt.figure(figsize=(20, 14))
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 主圖：K線圖 + MA5 + 穿越點 + 轉折點
        plt.subplot(3, 1, 1)
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
        
        # 繪製MA5
        plt.plot(dates, recent_df['ma5'], 
                color='blue', linewidth=2, linestyle='-', 
                alpha=0.8, label='5MA', zorder=5)
        
        # 標記穿越點
        for date, direction in cross_events:
            if direction == 'up':
                plt.scatter([date], [recent_df.loc[date, 'Close'] * 0.98], 
                           color='lime', marker='^', s=100, 
                           label='向上穿越' if date == cross_events[0][0] or cross_events[0][1] != 'up' else '', 
                           zorder=10)
            else:
                plt.scatter([date], [recent_df.loc[date, 'Close'] * 1.02], 
                           color='red', marker='v', s=100, 
                           label='向下穿越' if date == cross_events[0][0] or cross_events[0][1] != 'down' else '', 
                           zorder=10)
        
        # 標記轉折點
        for date, point_type, price in identified_turning_points:
            if point_type == 'high':
                plt.scatter([date], [price * 1.03], 
                           color='darkred', marker='^', s=120, 
                           label='轉折高點' if identified_turning_points[0][1] != 'high' or date == identified_turning_points[0][0] else '', 
                           edgecolor='white', linewidth=2, zorder=15)
            else:
                plt.scatter([date], [price * 0.97], 
                           color='darkblue', marker='v', s=120, 
                           label='轉折低點' if identified_turning_points[0][1] != 'low' or date == identified_turning_points[0][0] else '', 
                           edgecolor='white', linewidth=2, zorder=15)
        
        plt.title(f'{stock_id} 轉折點算法執行過程診斷', fontsize=16, fontweight='bold')
        plt.ylabel('價格', fontsize=12)
        plt.legend(fontsize=10, loc='upper left')
        plt.grid(True, alpha=0.3)
        
        # 子圖2：收盤價與MA5關係
        plt.subplot(3, 1, 2)
        plt.plot(dates, recent_df['Close'], label='收盤價', color='black', linewidth=1)
        plt.plot(dates, recent_df['ma5'], label='MA5', color='blue', linewidth=2)
        
        # 標記穿越點
        for date, direction in cross_events:
            color = 'lime' if direction == 'up' else 'red'
            marker = '^' if direction == 'up' else 'v'
            plt.scatter([date], [recent_df.loc[date, 'Close']], 
                       color=color, marker=marker, s=80, zorder=10)
        
        plt.title('收盤價 vs MA5 關係圖', fontsize=14)
        plt.ylabel('價格', fontsize=12)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        
        # 子圖3：穿越信號
        plt.subplot(3, 1, 3)
        above_ma5 = recent_df['close_above_ma5'].astype(int)
        plt.plot(dates, above_ma5, label='收盤價高於MA5', color='purple', linewidth=2)
        plt.fill_between(dates, 0, above_ma5, alpha=0.3, color='purple')
        
        # 標記穿越點
        for date, direction in cross_events:
            plt.axvline(x=date, color='red' if direction == 'down' else 'lime', 
                       linestyle='--', alpha=0.7)
        
        plt.title('收盤價相對於MA5位置 (1=上方, 0=下方)', fontsize=14)
        plt.ylabel('位置', fontsize=12)
        plt.xlabel('日期', fontsize=12)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # 保存圖表
        output_dir = 'output/debug_charts'
        os.makedirs(output_dir, exist_ok=True)
        chart_path = f'{output_dir}/{stock_id}_turning_point_debug.png'
        
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        print(f"\n✅ 診斷圖表已保存至: {chart_path}")
        plt.show()
        
    except Exception as e:
        print(f"❌ 創建診斷圖表時發生錯誤: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主程式"""
    print("轉折點算法執行過程診斷程式")
    print("=" * 60)
    print("逐步追蹤 turning_point_identification.py 的執行邏輯")
    
    stock_id = input("\n請輸入股票代碼 (預設2330): ").strip() or '2330'
    
    try:
        days_input = input("請輸入分析天數 (預設60天): ").strip()
        days = int(days_input) if days_input else 60
    except ValueError:
        days = 60
    
    print(f"\n開始診斷 {stock_id} 的轉折點識別算法...")
    
    success = debug_turning_point_execution(stock_id, days)
    
    if success:
        print(f"\n🎉 診斷完成！請檢查控制台輸出找出問題所在。")
    else:
        print(f"\n❌ 診斷失敗！")

if __name__ == "__main__":
    main()