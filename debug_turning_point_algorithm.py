#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轉折點算法診斷程式 - v2.0 (書本規格版)

配合新版 turning_point_identification.py，診斷位移規則的執行過程

功能：
1. 逐步追蹤穿越事件
2. 顯示群組內極值的位移過程
3. 驗證高低點交替原則
4. 視覺化呈現轉折點
5. 對比分析轉折點質量

版本：v2.0
更新日期：2025-10-23
"""

import pandas as pd
import numpy as np
import os
import sys
# 強制將標準輸出設為 UTF-8，解決 Windows 控制台 (CP950) 無法顯示 Emoji 的問題
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
from matplotlib.patches import Rectangle

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


def setup_chinese_font():
    """設置中文字體"""
    try:
        # Windows
        if os.name == 'nt':
            plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei']
        # macOS
        elif sys.platform == 'darwin':
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Heiti TC']
        # Linux
        else:
            plt.rcParams['font.sans-serif'] = ['Noto Sans CJK TC', 'WenQuanYi Zen Hei']
        
        plt.rcParams['axes.unicode_minus'] = False
        return True
    except Exception as e:
        print(f"⚠️ 字體設置警告: {e}")
        return False


def debug_turning_point_execution(stock_id='00631L', days=60):
    """
    診斷轉折點識別算法的執行過程
    
    詳細追蹤：
    1. 穿越事件檢測
    2. 群組劃分
    3. 極值位移過程
    4. 最終標記結果
    """
    print(f"\n{'='*80}")
    print(f"轉折點算法診斷：{stock_id} (書本規格版 v2.0)")
    print(f"{'='*80}")
    
    try:
        # 導入模塊
        from src.validate_buy_rule import load_stock_data
        from src.baseRule.turning_point_identification import (
            identify_turning_points, 
            detect_cross_events
        )

        class TurningPointTracker:
            """
            用於追蹤群組內極值位移的輔助類
            (僅用於診斷與視覺化，不影響核心算法)
            """
            def __init__(self):
                self.current_group_type = None  # 'positive' or 'negative'
                self.current_group_start_idx = -1
                self.current_extremum_idx = -1
                self.current_extremum_date = None
                self.current_extremum_value = None

            def start_positive_group(self, idx, date, high_val):
                self.current_group_type = 'positive'
                self.current_group_start_idx = idx
                self.current_extremum_idx = idx
                self.current_extremum_date = date
                self.current_extremum_value = high_val

            def start_negative_group(self, idx, date, low_val):
                self.current_group_type = 'negative'
                self.current_group_start_idx = idx
                self.current_extremum_idx = idx
                self.current_extremum_date = date
                self.current_extremum_value = low_val

            def update_extremum_in_positive_group(self, idx, date, high_val):
                if self.current_group_type == 'positive':
                    if high_val >= self.current_extremum_value:
                        self.current_extremum_idx = idx
                        self.current_extremum_date = date
                        self.current_extremum_value = high_val
            
            def update_extremum_in_negative_group(self, idx, date, low_val):
                if self.current_group_type == 'negative':
                    if low_val <= self.current_extremum_value:
                        self.current_extremum_idx = idx
                        self.current_extremum_date = date
                        self.current_extremum_value = low_val
        
        # 載入數據
        print("\n🔄 載入股票數據...")
        df = load_stock_data(stock_id, 'D')
        if df is None:
            print(f"❌ 無法載入股票 {stock_id} 的數據")
            return False
        
        # 確保有ma5欄位
        if 'ma5' not in df.columns:
            df['ma5'] = df['Close'].rolling(window=5, min_periods=1).mean()
        
        # 取最近的數據
        recent_df = df.tail(days).copy()
        print(f"✅ 成功載入數據")
        print(f"   分析範圍：{recent_df.index[0].strftime('%Y-%m-%d')} 到 {recent_df.index[-1].strftime('%Y-%m-%d')}")
        print(f"   總天數：{len(recent_df)} 天")
        
        # === 步驟1：檢測穿越事件 ===
        print(f"\n{'='*80}")
        print("📊 步驟1：檢測穿越事件")
        print(f"{'='*80}")
        
        df_with_cross = detect_cross_events(recent_df)
        
        # 找出所有穿越事件
        cross_up_dates = df_with_cross[df_with_cross['cross_up']].index
        cross_down_dates = df_with_cross[df_with_cross['cross_down']].index
        
        print(f"\n向上穿越事件 ({len(cross_up_dates)}次)：")
        for i, date in enumerate(cross_up_dates, 1):
            print(f"  {i:2d}. {date.strftime('%Y-%m-%d')} - 收盤價向上穿越MA5")
        
        print(f"\n向下穿越事件 ({len(cross_down_dates)}次)：")
        for i, date in enumerate(cross_down_dates, 1):
            print(f"  {i:2d}. {date.strftime('%Y-%m-%d')} - 收盤價向下穿越MA5")
        
        # 合併並排序所有穿越事件
        all_crosses = []
        for date in cross_up_dates:
            all_crosses.append((date, 'up'))
        for date in cross_down_dates:
            all_crosses.append((date, 'down'))
        all_crosses.sort(key=lambda x: x[0])
        
        # === 步驟2：追蹤群組與極值位移 ===
        print(f"\n{'='*80}")
        print("🔍 步驟2：追蹤群組劃分與極值位移過程")
        print(f"{'='*80}")
        
        tracker = TurningPointTracker()
        group_history = []  # 記錄每個群組的歷史
        
        current_position = None
        last_cross_idx = -1
        
        for i, (idx, row) in enumerate(df_with_cross.iterrows()):
            date = idx.strftime('%Y-%m-%d')
            close_above_ma5 = row['close_above_ma5']
            
            # 檢測穿越
            if row['cross_up']:
                print(f"\n⬆️  向上穿越 @ {date}")
                
                # 確認前一個負價群組
                if tracker.current_group_type == 'negative':
                    print(f"   └─ 確認負價群組 (起始: 索引 {tracker.current_group_start_idx})")
                    print(f"      轉折低點位置: 索引 {tracker.current_extremum_idx}, 日期 {tracker.current_extremum_date}")
                    print(f"      最低價: {tracker.current_extremum_value:.2f}")
                    
                    group_history.append({
                        'type': 'negative',
                        'start_idx': tracker.current_group_start_idx,
                        'end_idx': i,
                        'extremum_idx': tracker.current_extremum_idx,
                        'extremum_date': tracker.current_extremum_date,
                        'extremum_value': tracker.current_extremum_value,
                        'mark_type': 'low'
                    })
                
                # 開始新的正價群組
                tracker.start_positive_group(i, date, row['High'])
                print(f"   └─ 開始正價群組 @ 索引 {i}")
                last_cross_idx = i
            
            elif row['cross_down']:
                print(f"\n⬇️  向下穿越 @ {date}")
                
                # 確認前一個正價群組
                if tracker.current_group_type == 'positive':
                    print(f"   └─ 確認正價群組 (起始: 索引 {tracker.current_group_start_idx})")
                    print(f"      轉折高點位置: 索引 {tracker.current_extremum_idx}, 日期 {tracker.current_extremum_date}")
                    print(f"      最高價: {tracker.current_extremum_value:.2f}")
                    
                    group_history.append({
                        'type': 'positive',
                        'start_idx': tracker.current_group_start_idx,
                        'end_idx': i,
                        'extremum_idx': tracker.current_extremum_idx,
                        'extremum_date': tracker.current_extremum_date,
                        'extremum_value': tracker.current_extremum_value,
                        'mark_type': 'high'
                    })
                
                # 開始新的負價群組
                tracker.start_negative_group(i, date, row['Low'])
                print(f"   └─ 開始負價群組 @ 索引 {i}")
                last_cross_idx = i
            
            # 群組內更新極值（位移）
            else:
                if i >= 2:  # 需要至少2天數據
                    old_extremum_idx = tracker.current_extremum_idx
                    old_extremum_value = tracker.current_extremum_value
                    
                    if close_above_ma5 and tracker.current_group_type == 'positive':
                        tracker.update_extremum_in_positive_group(i, date, row['High'])
                        
                        # 如果發生位移，顯示
                        if tracker.current_extremum_idx != old_extremum_idx:
                            print(f"   🔄 位移！正價群組最高點更新:")
                            print(f"      從 索引{old_extremum_idx} ({old_extremum_value:.2f})")
                            print(f"      到 索引{i} {date} ({row['High']:.2f})")
                    
                    elif not close_above_ma5 and tracker.current_group_type == 'negative':
                        tracker.update_extremum_in_negative_group(i, date, row['Low'])
                        
                        # 如果發生位移，顯示
                        if tracker.current_extremum_idx != old_extremum_idx:
                            print(f"   🔄 位移！負價群組最低點更新:")
                            print(f"      從 索引{old_extremum_idx} ({old_extremum_value:.2f})")
                            print(f"      到 索引{i} {date} ({row['Low']:.2f})")
        
        # === 步驟3：執行完整算法並分析結果 ===
        print(f"\n{'='*80}")
        print("📋 步驟3：執行完整算法並分析結果")
        print(f"{'='*80}")
        
        turning_points_df = identify_turning_points(recent_df)
        
        high_points = turning_points_df[turning_points_df['turning_high_point'] == 'O']
        low_points = turning_points_df[turning_points_df['turning_low_point'] == 'O']
        
        print(f"\n✅ 轉折點識別完成")
        print(f"   轉折高點數量: {len(high_points)}")
        print(f"   轉折低點數量: {len(low_points)}")
        
        # 顯示所有轉折點
        print(f"\n🔺 轉折高點列表:")
        for i, (_, row) in enumerate(high_points.iterrows(), 1):
            date_str = row['date']
            matching_data = recent_df[recent_df.index.strftime('%Y-%m-%d') == date_str]
            if not matching_data.empty:
                high_price = matching_data.iloc[0]['High']
                close_price = matching_data.iloc[0]['Close']
                print(f"   {i:2d}. {date_str} - High: {high_price:7.2f}, Close: {close_price:7.2f}")
        
        print(f"\n🔻 轉折低點列表:")
        for i, (_, row) in enumerate(low_points.iterrows(), 1):
            date_str = row['date']
            matching_data = recent_df[recent_df.index.strftime('%Y-%m-%d') == date_str]
            if not matching_data.empty:
                low_price = matching_data.iloc[0]['Low']
                close_price = matching_data.iloc[0]['Close']
                print(f"   {i:2d}. {date_str} - Low: {low_price:7.2f}, Close: {close_price:7.2f}")
        
        # === 步驟4：驗證轉折點質量 ===
        print(f"\n{'='*80}")
        print("✓ 步驟4：驗證轉折點質量")
        print(f"{'='*80}")
        
        # 合併所有轉折點並檢查交替
        all_turning = []
        for _, row in high_points.iterrows():
            all_turning.append((row['date'], 'high'))
        for _, row in low_points.iterrows():
            all_turning.append((row['date'], 'low'))
        all_turning.sort(key=lambda x: x[0])
        
        print(f"\n按時間順序的轉折點:")
        alternating_ok = True
        for i, (date, tp_type) in enumerate(all_turning, 1):
            symbol = "🔺" if tp_type == 'high' else "🔻"
            
            # 檢查交替
            violation = ""
            if i > 1:
                if all_turning[i-2][1] == tp_type:
                    violation = " ⚠️ 違反交替原則!"
                    alternating_ok = False
            
            print(f"   {i:2d}. {symbol} {date} ({tp_type}){violation}")
        
        if alternating_ok:
            print(f"\n✅ 高低點交替檢查: 通過")
        else:
            print(f"\n❌ 高低點交替檢查: 失敗")
        
        # === 步驟5：視覺化 ===
        print(f"\n{'='*80}")
        print("📊 步驟5：生成診斷圖表")
        print(f"{'='*80}")
        
        create_diagnostic_chart(recent_df, turning_points_df, stock_id)
        
        return True
        
    except Exception as e:
        print(f"❌ 診斷過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_diagnostic_chart(df, turning_points_df, stock_id):
    """
    創建診斷圖表
    
    包含：
    1. K線圖 + MA5
    2. 轉折點標記
    3. 正價/負價群組背景色
    4. 穿越事件標記
    """
    try:
        setup_chinese_font()
        
        # 調整圖表尺寸符合規格書建議 (18, 8)，但因為我們有兩個子圖，稍微增高
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 12), 
                                        gridspec_kw={'height_ratios': [3, 1]})
        
        dates = df.index
        
        # === 上圖：K線 + MA5 + 轉折點 ===
        
        # 繪製K線 (使用 Z-Order 方法 A)
        for i, (date, row) in enumerate(df.iterrows()):
            is_up = row['Close'] >= row['Open']
            
            # K線參數
            bar_width = pd.Timedelta(hours=16)
            date_center = date + bar_width / 2
            
            # 1. 繪製影線 (Z-Order=1) - 黑色，一次畫完 Low 到 High
            ax1.plot([date_center, date_center], [row['Low'], row['High']], 
                    color='black', linewidth=0.8, alpha=1.0, zorder=1)
            
            # 2. 繪製實體 (Z-Order=2) - 必須覆蓋影線 (alpha=1.0)
            body_bottom = min(row['Close'], row['Open'])
            body_height = abs(row['Close'] - row['Open'])
            
            if body_height == 0:  # 十字線處理
                # 即使是十字線，也畫一個極扁的長方形，或者直接畫橫線
                line_color = 'red' if is_up else 'green'
                ax1.plot([date, date + bar_width], [row['Close'], row['Close']],
                        color=line_color, linewidth=1.5, zorder=3)
            else:
                if is_up:
                    # 上漲: 紅框白底
                    ax1.add_patch(Rectangle((date, body_bottom), 
                                           bar_width, body_height,
                                           facecolor='white', 
                                           edgecolor='red', 
                                           linewidth=1.2,
                                           alpha=1.0, 
                                           zorder=2))
                else:
                    # 下跌: 綠框綠底
                    ax1.add_patch(Rectangle((date, body_bottom), 
                                           bar_width, body_height,
                                           facecolor='green', 
                                           edgecolor='green', 
                                           linewidth=1.0, 
                                           alpha=1.0, 
                                           zorder=2))
        
        # 繪製MA5 (Z-Order=5)
        ax1.plot(dates, df['ma5'], label='MA5', color='blue', linewidth=1.5, alpha=0.8, zorder=5)
        
        # 標記轉折高點
        high_points = turning_points_df[turning_points_df['turning_high_point'] == 'O']
        for idx, row in high_points.iterrows():
            date_obj = pd.to_datetime(row['date'])
            if date_obj in df.index:
                price = df.loc[date_obj, 'High']
                offset = (df['High'].max() - df['Low'].min()) * 0.015
                ax1.scatter(date_obj + pd.Timedelta(hours=8), price + offset, 
                           color='darkred', s=60, marker='v', 
                           edgecolors='red', linewidths=0.5,
                           zorder=15, label='轉折高點' if idx == high_points.index[0] else '')
        
        # 標記轉折低點
        low_points = turning_points_df[turning_points_df['turning_low_point'] == 'O']
        for idx, row in low_points.iterrows():
            date_obj = pd.to_datetime(row['date'])
            if date_obj in df.index:
                price = df.loc[date_obj, 'Low']
                offset = (df['High'].max() - df['Low'].min()) * 0.015
                ax1.scatter(date_obj + pd.Timedelta(hours=8), price - offset, 
                           color='darkgreen', s=60, marker='^', 
                           edgecolors='green', linewidths=0.5,
                           zorder=15, label='轉折低點' if idx == low_points.index[0] else '')
        
        ax1.set_title(f'{stock_id} 轉折點診斷圖 (符合規格書標準)', fontsize=16, fontweight='bold')
        ax1.set_ylabel('價格', fontsize=12)
        ax1.legend(loc='upper left', fontsize=10)
        ax1.grid(True, color='gray', alpha=0.3)
        
        # === 下圖：收盤價與MA5的相對位置 ===
        
        close_above_ma5 = (df['Close'] > df['ma5']).astype(int)
        
        ax2.fill_between(dates, 0, close_above_ma5, 
                        where=(close_above_ma5 == 1), 
                        alpha=0.3, color='red', label='正價群組(收盤>MA5)')
        
        ax2.fill_between(dates, 0, close_above_ma5, 
                        where=(close_above_ma5 == 0), 
                        alpha=0.3, color='green', label='負價群組(收盤<MA5)')
        
        ax2.set_title('收盤價與MA5相對位置', fontsize=14)
        ax2.set_ylabel('位置', fontsize=12)
        ax2.set_xlabel('日期', fontsize=12)
        ax2.set_ylim(-0.1, 1.1)
        ax2.legend(fontsize=10)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存圖表
        output_dir = 'output/debug_charts'
        os.makedirs(output_dir, exist_ok=True)
        chart_path = f'{output_dir}/{stock_id}_turning_point_debug_v2.png'
        
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        print(f"\n✅ 診斷圖表已保存至: {chart_path}")
        plt.close()
        
    except Exception as e:
        print(f"❌ 創建診斷圖表時發生錯誤: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主程式"""
    print("="*80)
    print("轉折點算法診斷程式 v2.0 (書本規格版)")
    print("="*80)
    print("診斷功能：")
    print("  1. 追蹤穿越事件")
    print("  2. 顯示群組劃分")
    print("  3. 監控極值位移過程")
    print("  4. 驗證高低點交替")
    print("  5. 生成視覺化圖表")
    print("="*80)
    
    stock_id = input("\n請輸入股票代碼 (預設00631L): ").strip() or '00631L'
    
    try:
        days_input = input("請輸入分析天數 (預設60天): ").strip()
        days = int(days_input) if days_input else 60
    except ValueError:
        days = 60
    
    print(f"\n開始診斷 {stock_id} 的轉折點識別算法...")
    
    success = debug_turning_point_execution(stock_id, days)
    
    if success:
        print(f"\n{'='*80}")
        print("🎉 診斷完成！")
        print("="*80)
        print("\n請查看：")
        print("  1. 控制台輸出 - 詳細的執行過程")
        print("  2. output/debug_charts/ - 視覺化診斷圖表")
    else:
        print(f"\n❌ 診斷失敗！")


if __name__ == "__main__":
    main()