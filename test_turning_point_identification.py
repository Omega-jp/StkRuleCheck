#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轉折點識別測試程式
專門用來驗證 turning_point_identification.py 的結果
"""

import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


def test_turning_point_identification(stock_id='2330', days=180):
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
        
        # 創建視覺化圖表
        create_turning_point_chart(stock_id, recent_df, turning_points_df, days)
        
        return True
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


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
        
        # 標記所有轉折高點
        high_point_dates = []
        high_point_prices = []
        high_point_info = []
        
        for _, row in turning_points_df.iterrows():
            if row['turning_high_point'] == 'O':
                date_str = row['date']
                matching_dates = recent_df[recent_df.index.strftime('%Y-%m-%d') == date_str]
                if not matching_dates.empty:
                    date_obj = matching_dates.index[0]
                    high_price = matching_dates.iloc[0]['High']
                    high_point_dates.append(date_obj)
                    high_point_prices.append(high_price)
                    high_point_info.append(f"{date_str}\n{high_price:.2f}")
        
        # 標記所有轉折低點
        low_point_dates = []
        low_point_prices = []
        low_point_info = []
        
        for _, row in turning_points_df.iterrows():
            if row['turning_low_point'] == 'O':
                date_str = row['date']
                matching_dates = recent_df[recent_df.index.strftime('%Y-%m-%d') == date_str]
                if not matching_dates.empty:
                    date_obj = matching_dates.index[0]
                    low_price = matching_dates.iloc[0]['Low']
                    low_point_dates.append(date_obj)
                    low_point_prices.append(low_price)
                    low_point_info.append(f"{date_str}\n{low_price:.2f}")
        
        # 繪製轉折高點標記
        if high_point_dates:
            adjusted_high_prices = [price * 1.03 for price in high_point_prices]
            plt.scatter(high_point_dates, adjusted_high_prices, 
                       color='darkred', marker='^', s=80, 
                       label=f'轉折高點 ({len(high_point_dates)}個)', 
                       zorder=15, edgecolor='white', linewidth=2)
            
            # 添加數值標籤
            for i, (date, price, info) in enumerate(zip(high_point_dates, adjusted_high_prices, high_point_info)):
                plt.annotate(f'{i+1}', xy=(date, price), xytext=(0, 15), 
                           textcoords='offset points', ha='center', va='bottom',
                           fontsize=8, color='darkred', weight='bold')
        
        # 繪製轉折低點標記
        if low_point_dates:
            adjusted_low_prices = [price * 0.97 for price in low_point_prices]
            plt.scatter(low_point_dates, adjusted_low_prices, 
                       color='darkblue', marker='v', s=80, 
                       label=f'轉折低點 ({len(low_point_dates)}個)', 
                       zorder=15, edgecolor='white', linewidth=2)
            
            # 添加數值標籤
            for i, (date, price, info) in enumerate(zip(low_point_dates, adjusted_low_prices, low_point_info)):
                plt.annotate(f'{i+1}', xy=(date, price), xytext=(0, -15), 
                           textcoords='offset points', ha='center', va='top',
                           fontsize=8, color='darkblue', weight='bold')
        
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
        
        print(f"\n開始測試轉折點識別：{stock_id}，分析最近 {days} 天...")
        
        success = test_turning_point_identification(stock_id, days)
        
        if success:
            print(f"\n🎉 {stock_id} 轉折點識別測試完成！")
        else:
            print(f"\n❌ {stock_id} 測試失敗！")
        
        continue_test = input("\n是否測試其他股票？(y/n): ").strip().lower()
        if continue_test != 'y':
            break

if __name__ == "__main__":
    main()