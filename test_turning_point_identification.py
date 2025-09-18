#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轉折點識別測試程式
專門用來驗證 turning_point_identification.py 的結果
包含24-25區間震蕩問題的詳細診斷功能
"""

import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


def test_turning_point_identification(stock_id='2330', days=180, include_detailed_debug=False):
    """
    測試轉折點識別功能
    """
    print(f"\n{'='*70}")
    print(f"轉折點識別測試：{stock_id}")
    print(f"{'='*70}")
    
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
        print(f"   數據範圍：{recent_df.index[0].strftime('%Y-%m-%d')} 到 {recent_df.index[-1].strftime('%Y-%m-%d')}")
        
        # 執行轉折點識別
        print("\n🔍 執行轉折點識別...")
        turning_points_df = identify_turning_points(recent_df)
        
        # 詳細分析結果
        print(f"\n📋 轉折點識別結果分析：")
        print(f"   turning_points_df 總行數：{len(turning_points_df)}")
        print(f"   turning_points_df 欄位：{list(turning_points_df.columns)}")
        
        # 統計轉折點數量
        high_points = turning_points_df[turning_points_df['turning_high_point'] == 'O']
        low_points = turning_points_df[turning_points_df['turning_low_point'] == 'O']
        
        print(f"\n📊 統計結果：")
        print(f"   轉折高點數量：{len(high_points)}")
        print(f"   轉折低點數量：{len(low_points)}")
        
        # 顯示所有轉折高點
        if len(high_points) > 0:
            print(f"\n🔺 轉折高點詳細列表：")
            for i, (_, row) in enumerate(high_points.iterrows()):
                date_str = row['date']
                # 找出該日期在原始數據中的對應行
                matching_data = recent_df[recent_df.index.strftime('%Y-%m-%d') == date_str]
                if not matching_data.empty:
                    high_price = matching_data.iloc[0]['High']
                    close_price = matching_data.iloc[0]['Close']
                    print(f"   {i+1:2d}. {date_str} - 最高價：{high_price:7.2f}, 收盤價：{close_price:7.2f}")
                else:
                    print(f"   {i+1:2d}. {date_str} - ⚠️ 在recent_df中找不到對應數據")
        else:
            print(f"\n🔺 未找到轉折高點")
        
        # 顯示所有轉折低點
        if len(low_points) > 0:
            print(f"\n🔻 轉折低點詳細列表：")
            for i, (_, row) in enumerate(low_points.iterrows()):
                date_str = row['date']
                # 找出該日期在原始數據中的對應行
                matching_data = recent_df[recent_df.index.strftime('%Y-%m-%d') == date_str]
                if not matching_data.empty:
                    low_price = matching_data.iloc[0]['Low']
                    close_price = matching_data.iloc[0]['Close']
                    print(f"   {i+1:2d}. {date_str} - 最低價：{low_price:7.2f}, 收盤價：{close_price:7.2f}")
                else:
                    print(f"   {i+1:2d}. {date_str} - ⚠️ 在recent_df中找不到對應數據")
        else:
            print(f"\n🔻 未找到轉折低點")
        
        # 檢查日期匹配問題
        print(f"\n🔍 日期匹配檢查：")
        recent_df_dates = set(recent_df.index.strftime('%Y-%m-%d'))
        turning_point_dates = set(turning_points_df['date'])
        
        missing_in_recent = turning_point_dates - recent_df_dates
        if missing_in_recent:
            print(f"   ⚠️ 以下轉折點日期在recent_df中找不到：{missing_in_recent}")
        else:
            print(f"   ✅ 所有轉折點日期都在recent_df中存在")
        
        # 顯示turning_points_df的前10行和後10行
        print(f"\n📄 turning_points_df 前10行：")
        print(turning_points_df.head(10).to_string())
        
        if len(turning_points_df) > 10:
            print(f"\n📄 turning_points_df 後10行：")
            print(turning_points_df.tail(10).to_string())
        
        # 如果用戶要求詳細診斷，執行24-25區間分析
        if include_detailed_debug:
            debug_24_25_period_detailed(recent_df)
        
        # 創建視覺化圖表
        create_turning_point_chart(stock_id, recent_df, turning_points_df, days)
        
        return True
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


def debug_24_25_period_detailed(df):
    """
    詳細診斷24-25區間的穿越事件和轉折點識別邏輯
    """
    print(f"\n{'='*60}")
    print("24-25區間詳細診斷分析")
    print(f"{'='*60}")
    
    # 手動模擬穿越檢測邏輯
    print("逐日分析MA5穿越事件...")
    
    # 分析最近50天的數據，重點關注震蕩區間
    focus_df = df.tail(50)
    
    last_cross_up_idx = None
    last_cross_down_idx = None
    cross_events = []
    
    for i, (idx, row) in enumerate(focus_df.iterrows()):
        date = idx.strftime('%Y-%m-%d')
        
        if i < 1:  # 需要前一天數據
            continue
            
        prev_row = focus_df.iloc[i - 1]
        
        current_close = row['Close']
        current_ma5 = row['ma5']
        prev_close = prev_row['Close']
        prev_ma5 = prev_row['ma5']
        
        # 檢測穿越事件（使用修正後的無門檻邏輯）
        cross_up = (
            (current_close > current_ma5) and
            (prev_close <= prev_ma5) and
            (last_cross_down_idx is None or i - last_cross_down_idx >= 1)
        )
        
        cross_down = (
            (current_close < current_ma5) and
            (prev_close >= prev_ma5) and
            (last_cross_up_idx is None or i - last_cross_up_idx >= 1)
        )
        
        # 記錄穿越事件
        if cross_up:
            last_cross_up_idx = i
            cross_events.append({
                'date': date,
                'type': 'up',
                'close': current_close,
                'ma5': current_ma5,
                'prev_close': prev_close,
                'prev_ma5': prev_ma5,
                'idx': i
            })
            print(f"  向上穿越: {date} | 收盤:{current_close:.2f} > MA5:{current_ma5:.2f} | 前日收盤:{prev_close:.2f} <= 前日MA5:{prev_ma5:.2f}")
        
        if cross_down:
            last_cross_down_idx = i
            cross_events.append({
                'date': date,
                'type': 'down',
                'close': current_close,
                'ma5': current_ma5,
                'prev_close': prev_close,
                'prev_ma5': prev_ma5,
                'idx': i
            })
            print(f"  向下穿越: {date} | 收盤:{current_close:.2f} < MA5:{current_ma5:.2f} | 前日收盤:{prev_close:.2f} >= 前日MA5:{prev_ma5:.2f}")
    
    print(f"\n總共偵測到 {len(cross_events)} 個穿越事件")
    
    # 分析穿越事件之間的區間和轉折點
    print(f"\n穿越事件間的轉折點分析：")
    for i in range(len(cross_events) - 1):
        current_event = cross_events[i]
        next_event = cross_events[i + 1]
        
        if current_event['type'] == 'down' and next_event['type'] == 'up':
            # 向下穿越 -> 向上穿越：應該標記轉折低點
            start_idx = current_event['idx']
            end_idx = next_event['idx']
            period_data = focus_df.iloc[start_idx:end_idx+1]
            
            if len(period_data) >= 1:
                min_low_idx = period_data['Low'].idxmin()
                min_low_date = min_low_idx.strftime('%Y-%m-%d')
                min_low_price = period_data.loc[min_low_idx, 'Low']
                
                print(f"  轉折低點: {current_event['date']} -> {next_event['date']}")
                print(f"    區間長度: {len(period_data)} 天")
                print(f"    最低點: {min_low_date} (價格: {min_low_price:.2f})")
        
        elif current_event['type'] == 'up' and next_event['type'] == 'down':
            # 向上穿越 -> 向下穿越：應該標記轉折高點
            start_idx = current_event['idx']
            end_idx = next_event['idx']
            period_data = focus_df.iloc[start_idx:end_idx+1]
            
            if len(period_data) >= 1:
                max_high_idx = period_data['High'].idxmax()
                max_high_date = max_high_idx.strftime('%Y-%m-%d')
                max_high_price = period_data.loc[max_high_idx, 'High']
                
                print(f"  轉折高點: {current_event['date']} -> {next_event['date']}")
                print(f"    區間長度: {len(period_data)} 天")
                print(f"    最高點: {max_high_date} (價格: {max_high_price:.2f})")


def create_turning_point_chart(stock_id, recent_df, turning_points_df, days):
    """
    創建轉折點視覺化圖表
    """
    try:
        # 設置中文字體
        plt.figure(figsize=(18, 12))
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 主圖：K線圖 + 轉折點
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
        
        # 繪製5日移動平均線
        if 'ma5' in recent_df.columns:
            plt.plot(dates, recent_df['ma5'], 
                    color='blue', linewidth=2, linestyle='-', 
                    alpha=0.8, label='5MA', zorder=5)
        
        # 標記所有轉折點（統一按時間順序編號）
        print("   統一標記所有轉折點...")
        
        # 收集所有轉折點
        all_turning_points = []
        
        # 收集轉折高點
        for _, row in turning_points_df.iterrows():
            if row['turning_high_point'] == 'O':
                date_str = row['date']
                matching_dates = recent_df[recent_df.index.strftime('%Y-%m-%d') == date_str]
                if not matching_dates.empty:
                    date_obj = matching_dates.index[0]
                    high_price = matching_dates.iloc[0]['High']
                    all_turning_points.append({
                        'date': date_obj,
                        'price': high_price,
                        'type': 'high',
                        'marker_price': high_price * 1.03,
                        'marker': '^',
                        'color': 'darkred'
                    })
        
        # 收集轉折低點
        for _, row in turning_points_df.iterrows():
            if row['turning_low_point'] == 'O':
                date_str = row['date']
                matching_dates = recent_df[recent_df.index.strftime('%Y-%m-%d') == date_str]
                if not matching_dates.empty:
                    date_obj = matching_dates.index[0]
                    low_price = matching_dates.iloc[0]['Low']
                    all_turning_points.append({
                        'date': date_obj,
                        'price': low_price,
                        'type': 'low',
                        'marker_price': low_price * 0.97,
                        'marker': 'v',
                        'color': 'darkblue'
                    })
        
        # 按時間排序
        all_turning_points.sort(key=lambda x: x['date'])
        
        # 分別繪製高點和低點的散點圖（用於圖例）
        high_points = [tp for tp in all_turning_points if tp['type'] == 'high']
        low_points = [tp for tp in all_turning_points if tp['type'] == 'low']
        
        if high_points:
            high_dates = [tp['date'] for tp in high_points]
            high_marker_prices = [tp['marker_price'] for tp in high_points]
            plt.scatter(high_dates, high_marker_prices, 
                       color='darkred', marker='^', s=80, 
                       label=f'轉折高點 ({len(high_points)}個)', 
                       zorder=15, edgecolor='white', linewidth=2)
        
        if low_points:
            low_dates = [tp['date'] for tp in low_points]
            low_marker_prices = [tp['marker_price'] for tp in low_points]
            plt.scatter(low_dates, low_marker_prices, 
                       color='darkblue', marker='v', s=80, 
                       label=f'轉折低點 ({len(low_points)}個)', 
                       zorder=15, edgecolor='white', linewidth=2)
        
        # 統一編號標記（按時間順序）
        for i, tp in enumerate(all_turning_points):
            plt.annotate(f'{i+1}', 
                       xy=(tp['date'], tp['marker_price']), 
                       xytext=(0, 15 if tp['type'] == 'high' else -15), 
                       textcoords='offset points', 
                       ha='center', 
                       va='bottom' if tp['type'] == 'high' else 'top',
                       fontsize=9, 
                       color=tp['color'], 
                       weight='bold',
                       bbox=dict(boxstyle='round,pad=0.2', 
                                facecolor='white', 
                                edgecolor=tp['color'], 
                                alpha=0.8))
        
        # 圖表設置
        plt.title(f'{stock_id} 轉折點識別測試（最近{days}天）', 
                 fontsize=18, fontweight='bold')
        plt.ylabel('價格', fontsize=14)
        plt.legend(fontsize=12, loc='upper left')
        plt.grid(True, alpha=0.3)
        
        # 調整Y軸範圍
        y_min = recent_df['Low'].min() * 0.95
        y_max = recent_df['High'].max() * 1.05
        plt.ylim(y_min, y_max)
        
        # 成交量圖
        plt.subplot(2, 1, 2)
        volume_colors = ['red' if closes.iloc[i] >= opens.iloc[i] else 'green' 
                        for i in range(len(dates))]
        
        plt.bar(dates, recent_df['Volume'], alpha=0.7, 
               color=volume_colors, width=0.8)
        
        plt.title('成交量', fontsize=16)
        plt.ylabel('成交量', fontsize=12)
        plt.xlabel('日期', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # 保存圖表
        output_dir = 'output/test_charts'
        os.makedirs(output_dir, exist_ok=True)
        chart_path = f'{output_dir}/{stock_id}_turning_point_test.png'
        
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        print(f"✅ 轉折點測試圖表已保存至: {chart_path}")
        plt.show()
        
    except Exception as e:
        print(f"❌ 創建圖表時發生錯誤: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主程式"""
    print("轉折點識別測試程式")
    print("=" * 50)
    print("此程式專門用來驗證 turning_point_identification.py 的結果")
    print("會詳細列出所有轉折高點和轉折低點的資訊")
    print("並包含24-25區間震蕩問題的詳細診斷功能")
    
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
        
        # 詢問是否要執行詳細診斷
        detailed_debug = input("是否要執行24-25區間詳細診斷？(y/n，預設n): ").strip().lower()
        
        print(f"\n開始測試轉折點識別：{stock_id}，分析最近 {days} 天...")
        
        success = test_turning_point_identification(stock_id, days, 
                                                  include_detailed_debug=(detailed_debug == 'y'))
        
        if success:
            print(f"\n🎉 {stock_id} 轉折點識別測試完成！")
        else:
            print(f"\n❌ {stock_id} 測試失敗！")
        
        continue_test = input("\n是否測試其他股票？(y/n): ").strip().lower()
        if continue_test != 'y':
            break

if __name__ == "__main__":
    main()