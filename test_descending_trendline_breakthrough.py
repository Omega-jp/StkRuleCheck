#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下降趨勢線突破測試程式 - 規格書版本
====================================

完整測試下降趨勢線突破檢測功能：
1. 載入股票數據
2. 識別波段高點
3. 繪製趨勢線
4. 檢測突破信號
5. 視覺化分析

作者：Claude
日期：2025-01-21
"""

import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import Rectangle

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


def setup_chinese_font():
    """設置中文字體（自動尋找可用字體）"""
    try:
        chinese_fonts = [
            'Microsoft JhengHei',
            'Microsoft YaHei',
            'SimHei',
            'Arial Unicode MS',
            'Noto Sans CJK TC',
            'Noto Sans CJK SC',
            'DejaVu Sans',
        ]
        
        available_fonts = set([f.name for f in fm.fontManager.ttflist])
        
        for font in chinese_fonts:
            if font in available_fonts:
                plt.rcParams['font.sans-serif'] = [font]
                print(f"✅ 使用字體: {font}")
                break
        else:
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
        
        plt.rcParams['axes.unicode_minus'] = False
        
    except Exception as e:
        print(f"⚠️  字體設置失敗: {e}")
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']


def test_descending_trendline_breakthrough(stock_id='2330', days=360):
    """
    測試下降趨勢線突破檢測
    
    完整流程：
    1. 載入數據並識別波段點
    2. 識別下降趨勢線
    3. 檢測突破信號
    4. 繪製分析圖表
    5. 輸出統計資訊
    """
    
    print(f"\n{'='*70}")
    print(f"下降趨勢線突破測試：{stock_id}（規格書版本）")
    print(f"{'='*70}")
    
    try:
        # 導入必要模塊
        print("📦 載入模組...")
        from src.validate_buy_rule import load_stock_data
        from src.baseRule.turning_point_identification import identify_turning_points
        from src.baseRule.waving_point_identification import identify_waving_points
        
        # 使用新版本的模組（從 src.buyRule 導入）
        from src.buyRule.long_term_descending_trendline import identify_descending_trendlines
        from src.buyRule.breakthrough_descending_trendline import check_breakthrough_descending_trendline
        
        # 載入股票數據
        print(f"🔄 載入股票數據...")
        df = load_stock_data(stock_id, 'D')
        if df is None:
            print(f"❌ 無法載入股票 {stock_id} 的數據")
            return False
        
        print(f"✅ 成功載入數據，共 {len(df)} 筆記錄")
        
        # 確保有MA5欄位
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
        
        print(f"✅ 轉折高點：{len(high_points)} 個")
        print(f"✅ 轉折低點：{len(low_points)} 個")
        
        # 步驟2：識別波段點
        print(f"\n{'='*60}")
        print("步驟2：識別波段點")
        print(f"{'='*60}")
        
        wave_points_df = identify_waving_points(recent_df, turning_points_df)
        wave_high_points = wave_points_df[wave_points_df['wave_high_point'] == 'O']
        wave_low_points = wave_points_df[wave_points_df['wave_low_point'] == 'O']
        
        print(f"✅ 波段高點：{len(wave_high_points)} 個")
        print(f"✅ 波段低點：{len(wave_low_points)} 個")
        
        if len(wave_high_points) < 2:
            print(f"\n⚠️  波段高點數量不足（< 2），無法繪製趨勢線")
            return False
        
        # 步驟3：識別下降趨勢線（使用規格書版本）
        print(f"\n{'='*60}")
        print("步驟3：識別下降趨勢線（規格書版本）")
        print(f"{'='*60}")
        
        trendlines = identify_descending_trendlines(
            recent_df,
            wave_points_df,
            lookback_days=180,
            recent_end_days=20,
            tolerance_pct=0.1
        )
        
        diagonal_lines = trendlines['diagonal_lines']
        horizontal_line = trendlines['horizontal_line']
        
        print(f"✅ 斜向下降趨勢線：{len(diagonal_lines)} 條")
        print(f"✅ 水平壓力線：{'有' if horizontal_line else '無'}")
        
        # 顯示趨勢線詳情
        if len(diagonal_lines) > 0:
            print(f"\n斜向趨勢線詳情（前5條）：")
            for i, line in enumerate(diagonal_lines[:5]):
                print(f"  {i+1}. {line['start_date'].strftime('%Y-%m-%d')} → {line['end_date'].strftime('%Y-%m-%d')}")
                print(f"     時間跨度：{line['days_span']} 天，斜率：{line['slope']:.6f}")
        
        if horizontal_line:
            print(f"\n水平壓力線詳情：")
            print(f"  價格：{horizontal_line['resistance_price']:.2f}")
            print(f"  日期：{horizontal_line['resistance_date'].strftime('%Y-%m-%d')}")
        
        # 步驟4：檢測突破信號
        print(f"\n{'='*60}")
        print("步驟4：檢測突破信號")
        print(f"{'='*60}")
        
        breakthrough_df = check_breakthrough_descending_trendline(
            recent_df,
            trendlines,
            min_breakthrough_pct=0.5,
            volume_confirmation=True,
            volume_multiplier=1.2,
            volume_window=20
        )
        
        # 篩選出突破信號
        signals = breakthrough_df[breakthrough_df['breakthrough_check'] == 'O']
        
        print(f"✅ 突破信號：{len(signals)} 個")
        
        if len(signals) > 0:
            print(f"\n突破信號詳情：")
            for i, (_, row) in enumerate(signals.iterrows()):
                print(f"  {i+1}. {row['date']} - {row['breakthrough_type']}")
                print(f"     突破幅度：{row['breakthrough_pct']:.2f}%")
                print(f"     成交量比：{row['volume_ratio']:.2f}x")
                print(f"     信號強度：{row['signal_strength']}/5")
        
        # 步驟5：創建分析圖表
        print(f"\n{'='*60}")
        print("步驟5：創建視覺化圖表")
        print(f"{'='*60}")
        
        create_analysis_chart(
            stock_id,
            recent_df,
            wave_points_df,
            trendlines,
            breakthrough_df,
            days
        )
        
        # 輸出統計摘要
        print_statistics(signals, trendlines)
        
        return True
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_analysis_chart(stock_id, df, wave_points_df, trendlines, breakthrough_df, days):
    """
    創建完整的分析圖表
    
    包含：
    1. K線圖 + 波段點標記
    2. 所有趨勢線
    3. 突破信號標記
    4. 成交量圖
    """
    
    try:
        setup_chinese_font()
        
        fig = plt.figure(figsize=(20, 12))
        
        # === 上半部：K線圖 ===
        ax1 = plt.subplot(2, 1, 1)
        
        dates = df.index
        opens = df['Open']
        highs = df['High']
        lows = df['Low']
        closes = df['Close']
        
        # 繪製K線
        colors = ['red' if closes.iloc[i] >= opens.iloc[i] else 'green' 
                  for i in range(len(dates))]
        
        for i in range(len(dates)):
            # K線實體
            body_height = abs(closes.iloc[i] - opens.iloc[i])
            body_bottom = min(opens.iloc[i], closes.iloc[i])
            
            rect = Rectangle((dates[i], body_bottom), 0.6, body_height,
                           facecolor=colors[i], edgecolor='black', linewidth=0.5, alpha=0.8)
            ax1.add_patch(rect)
            
            # 上下影線
            ax1.plot([dates[i], dates[i]], [lows.iloc[i], highs.iloc[i]], 
                    color='black', linewidth=0.5)
        
        # 標記波段高點
        wave_high_dates = []
        wave_high_prices = []
        for _, row in wave_points_df.iterrows():
            if row['wave_high_point'] == 'O':
                date_str = row['date']
                matching = df[df.index.strftime('%Y-%m-%d') == date_str]
                if not matching.empty:
                    wave_high_dates.append(matching.index[0])
                    wave_high_prices.append(matching.iloc[0]['High'] * 1.02)
        
        if wave_high_dates:
            ax1.scatter(wave_high_dates, wave_high_prices, 
                       color='darkred', marker='*', s=200, 
                       label=f'波段高點 ({len(wave_high_dates)}個)', 
                       zorder=20, edgecolor='white', linewidth=1.5)
        
        # 標記波段低點
        wave_low_dates = []
        wave_low_prices = []
        for _, row in wave_points_df.iterrows():
            if row['wave_low_point'] == 'O':
                date_str = row['date']
                matching = df[df.index.strftime('%Y-%m-%d') == date_str]
                if not matching.empty:
                    wave_low_dates.append(matching.index[0])
                    wave_low_prices.append(matching.iloc[0]['Low'] * 0.98)
        
        if wave_low_dates:
            ax1.scatter(wave_low_dates, wave_low_prices, 
                       color='darkblue', marker='*', s=200, 
                       label=f'波段低點 ({len(wave_low_dates)}個)', 
                       zorder=20, edgecolor='white', linewidth=1.5)
        
        # 繪製趨勢線
        diagonal_lines = trendlines['diagonal_lines']
        horizontal_line = trendlines['horizontal_line']
        
        colors_diagonal = ['orange', 'purple', 'brown', 'navy', 'darkgreen']
        
        for i, line in enumerate(diagonal_lines[:5]):
            color = colors_diagonal[i % len(colors_diagonal)]
            draw_trendline(ax1, line, df, color, f"趨勢線{i+1}")
        
        if horizontal_line:
            draw_horizontal_line(ax1, horizontal_line, df, 'red', "水平壓力線")
        
        # 標記突破信號
        breakthrough_dates = []
        breakthrough_prices = []
        breakthrough_strengths = []
        
        for _, row in breakthrough_df.iterrows():
            if row['breakthrough_check'] == 'O':
                date_str = row['date']
                matching = df[df.index.strftime('%Y-%m-%d') == date_str]
                if not matching.empty:
                    breakthrough_dates.append(matching.index[0])
                    breakthrough_prices.append(matching.iloc[0]['High'] * 1.05)
                    breakthrough_strengths.append(row['signal_strength'])
        
        if breakthrough_dates:
            ax1.scatter(breakthrough_dates, breakthrough_prices, 
                       color='gold', marker='P', s=300, 
                       label=f'突破信號 ({len(breakthrough_dates)}個)', 
                       zorder=25, edgecolor='red', linewidth=2)
            
            # 標記信號強度
            for date, price, strength in zip(breakthrough_dates, breakthrough_prices, breakthrough_strengths):
                ax1.text(date, price * 1.02, f'{strength}/5',
                        ha='center', va='bottom', fontsize=10,
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.8))
        
        ax1.set_title(f'{stock_id} 下降趨勢線突破分析（規格書版本）', fontsize=16, fontweight='bold')
        ax1.set_ylabel('價格', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='best', fontsize=10)
        
        # === 下半部：成交量圖 ===
        ax2 = plt.subplot(2, 1, 2)
        
        volume_colors = ['red' if closes.iloc[i] >= opens.iloc[i] else 'green' 
                        for i in range(len(dates))]
        
        ax2.bar(dates, df['Volume'], alpha=0.7, color=volume_colors, width=0.8)
        
        # 標記突破信號對應的成交量
        if breakthrough_dates:
            for date in breakthrough_dates:
                matching = df[df.index == date]
                if not matching.empty:
                    volume = matching.iloc[0]['Volume']
                    ax2.scatter([date], [volume * 1.1],
                               color='gold', marker='P', s=150, 
                               edgecolor='red', linewidth=2, zorder=10)
        
        ax2.set_title('成交量', fontsize=14)
        ax2.set_ylabel('成交量', fontsize=12)
        ax2.set_xlabel('日期', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存圖表
        output_dir = 'output/test_charts'
        os.makedirs(output_dir, exist_ok=True)
        chart_path = f'{output_dir}/{stock_id}_descending_trendline_spec.png'
        
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        print(f"✅ 圖表已保存至: {chart_path}")
        plt.close()
        
    except Exception as e:
        print(f"❌ 創建圖表時發生錯誤: {e}")
        import traceback
        traceback.print_exc()


def draw_trendline(ax, line, df, color, label):
    """繪製斜向趨勢線"""
    start_idx = line['start_idx']
    end_idx = line['end_idx']
    slope = line['slope']
    intercept = line['intercept']
    
    start_date = df.index[start_idx]
    end_date = df.index[end_idx]
    last_date = df.index[-1]
    
    start_price = intercept + slope * start_idx
    end_price = intercept + slope * end_idx
    last_price = intercept + slope * (len(df) - 1)
    
    # 實線段
    ax.plot([start_date, end_date], [start_price, end_price], 
            color=color, linewidth=2.5, linestyle='-', alpha=0.9, zorder=15)
    
    # 延伸虛線
    if len(df) - 1 > end_idx:
        ax.plot([end_date, last_date], [end_price, last_price], 
                color=color, linewidth=2, linestyle='--', alpha=0.7, zorder=15)
    
    # 標記連接點
    points = line['points']
    if len(points) >= 2:
        point_dates = [p['date'] for p in points]
        point_prices = [p['price'] for p in points]
        ax.scatter(point_dates, point_prices, 
                  color=color, marker='o', s=100, 
                  edgecolor='white', linewidth=2, zorder=18)
    
    # 添加標籤
    mid_idx = (start_idx + end_idx) // 2
    mid_date = df.index[mid_idx]
    mid_price = intercept + slope * mid_idx
    
    ax.text(mid_date, mid_price * 1.02, f"{label}({line['days_span']}天)",
           fontsize=9, color=color, fontweight='bold',
           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                    edgecolor=color, alpha=0.8))


def draw_horizontal_line(ax, line, df, color, label):
    """繪製水平壓力線"""
    start_date = df.index[0]
    end_date = df.index[-1]
    price = line['resistance_price']
    
    ax.axhline(y=price, color=color, linewidth=3, linestyle='-', 
              alpha=0.9, zorder=15, label=f'{label} ({price:.2f})')
    
    # 標記最高點位置
    resistance_date = line['resistance_date']
    ax.scatter([resistance_date], [price], 
              color=color, marker='D', s=150, 
              edgecolor='white', linewidth=2, zorder=18)


def print_statistics(signals, trendlines):
    """輸出統計摘要"""
    print(f"\n{'='*60}")
    print("統計摘要")
    print(f"{'='*60}")
    
    diagonal_count = len(trendlines['diagonal_lines'])
    has_horizontal = trendlines['horizontal_line'] is not None
    
    print(f"📊 趨勢線統計：")
    print(f"   斜向下降趨勢線：{diagonal_count} 條")
    print(f"   水平壓力線：{'有' if has_horizontal else '無'}")
    
    if len(signals) == 0:
        print(f"\n📊 突破信號統計：無突破信號")
        return
    
    print(f"\n📊 突破信號統計：")
    print(f"   總信號數：{len(signals)}")
    print(f"   平均信號強度：{signals['signal_strength'].mean():.2f}/5")
    print(f"   平均突破幅度：{signals['breakthrough_pct'].mean():.2f}%")
    print(f"   平均成交量比：{signals['volume_ratio'].mean():.2f}x")
    
    # 按類型分類
    diagonal_signals = signals[signals['breakthrough_type'] == 'diagonal_descending']
    horizontal_signals = signals[signals['breakthrough_type'] == 'horizontal_resistance']
    
    print(f"\n   突破類型分布：")
    print(f"   - 斜向趨勢線突破：{len(diagonal_signals)} 個")
    print(f"   - 水平壓力線突破：{len(horizontal_signals)} 個")
    
    # 最佳信號
    if len(signals) > 0:
        best_signal = signals.loc[signals['signal_strength'].idxmax()]
        print(f"\n🏆 最強信號：")
        print(f"   日期：{best_signal['date']}")
        print(f"   類型：{best_signal['breakthrough_type']}")
        print(f"   突破幅度：{best_signal['breakthrough_pct']:.2f}%")
        print(f"   成交量比：{best_signal['volume_ratio']:.2f}x")
        print(f"   信號強度：{best_signal['signal_strength']}/5")


def main():
    """主程式"""
    print("=" * 70)
    print("下降趨勢線突破測試程式（規格書版本）")
    print("=" * 70)
    print("改進：")
    print("  ✅ 使用波段高點（非轉折高點）")
    print("  ✅ 斜向趨勢線（180天內起點，20天內終點）")
    print("  ✅ 水平壓力線（180天最高價）")
    print("  ✅ 收盤價突破 + 0.5%幅度 + 1.2x量能")
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
        
        success = test_descending_trendline_breakthrough(stock_id, days)
        
        if success:
            print(f"\n🎉 {stock_id} 測試完成！")
        else:
            print(f"\n❌ {stock_id} 測試失敗！")
        
        continue_test = input("\n是否測試其他股票？(y/n): ").strip().lower()
        if continue_test != 'y':
            break


if __name__ == "__main__":
    main()