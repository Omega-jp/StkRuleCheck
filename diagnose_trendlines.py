#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單的趨勢線診斷腳本 - 檢查為什麼沒有顯示趨勢線
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def diagnose_trendlines(stock_id='00631l', days=360):
    """診斷趨勢線識別"""
    print(f"\n{'='*70}")
    print(f"診斷股票 {stock_id} 的趨勢線識別")
    print(f"{'='*70}\n")
    
    try:
        from src.validate_buy_rule import load_stock_data
        from src.baseRule.turning_point_identification import identify_turning_points
        from src.buyRule.long_term_descending_trendline import identify_long_term_descending_trendlines
        
        # 載入數據
        print("1. 載入股票數據...")
        df = load_stock_data(stock_id, 'D')
        if df is None:
            print(f"❌ 無法載入股票 {stock_id} 的數據")
            return
        print(f"✅ 成功載入，共 {len(df)} 筆記錄")
        
        # 計算MA5
        if 'ma5' not in df.columns:
            df['ma5'] = df['Close'].rolling(window=5, min_periods=1).mean()
        
        # 取最近數據
        recent_df = df.tail(days)
        print(f"✅ 取最近 {len(recent_df)} 天數據")
        print(f"   日期範圍: {recent_df.index[0].strftime('%Y-%m-%d')} 到 {recent_df.index[-1].strftime('%Y-%m-%d')}")
        
        # 識別轉折點
        print("\n2. 識別轉折點...")
        turning_points_df = identify_turning_points(recent_df)
        
        high_points = turning_points_df[turning_points_df['turning_high_point'] == 'O']
        low_points = turning_points_df[turning_points_df['turning_low_point'] == 'O']
        
        print(f"✅ 轉折高點: {len(high_points)} 個")
        print(f"✅ 轉折低點: {len(low_points)} 個")
        
        if len(high_points) < 2:
            print(f"\n❌ 轉折高點太少（< 2個），無法形成趨勢線")
            print(f"   建議：增加天數參數（目前 {days} 天）")
            return
        
        # 顯示前5個轉折高點
        print("\n   前5個轉折高點:")
        for i, (_, row) in enumerate(high_points.head(5).iterrows()):
            date_str = row['date']
            print(f"   {i+1}. {date_str}")
        
        # 識別趨勢線
        print("\n3. 識別下降趨勢線...")
        trendlines = identify_long_term_descending_trendlines(
            recent_df, 
            turning_points_df,
            min_days_long_term=180,
            min_points_short_term=3
        )
        
        long_term_count = len(trendlines['long_term_lines'])
        short_term_count = len(trendlines['short_term_lines'])
        total_count = len(trendlines['all_lines'])
        
        print(f"✅ 長期趨勢線: {long_term_count} 條")
        print(f"✅ 短期趨勢線: {short_term_count} 條")
        print(f"✅ 總計: {total_count} 條")
        
        if total_count == 0:
            print(f"\n❌ 沒有找到任何下降趨勢線！")
            print(f"\n可能原因：")
            print(f"1. 股票沒有形成明顯的下降趨勢")
            print(f"2. 轉折高點之間沒有形成下降關係")
            print(f"3. 時間跨度不足（長期線需要 >= 180 天）")
            print(f"\n建議：")
            print(f"- 增加天數參數（試試 500-720 天）")
            print(f"- 測試其他股票（如 00631L）")
            return
        
        # 顯示趨勢線詳細資訊
        print(f"\n4. 趨勢線詳細資訊：")
        for i, line in enumerate(trendlines['all_lines'][:5]):
            line_type = "長期" if line['type'] == 'long_term_two_point' else "短期"
            print(f"\n   趨勢線 {i+1} ({line_type}):")
            print(f"   - 時間跨度: {line['days_span']} 天")
            print(f"   - 開始: {line['start_date'].strftime('%Y-%m-%d')}")
            print(f"   - 結束: {line['end_date'].strftime('%Y-%m-%d')}")
            print(f"   - 斜率: {line['slope']:.6f}")
            print(f"   - R²: {line['r_squared']:.4f}")
            print(f"   - 連接點數: {len(line['points'])}")
        
        # 檢查買入信號
        print(f"\n5. 檢查買入信號...")
        from src.buyRule.breakthrough_descending_trendline import check_descending_trendline
        
        buy_signals = check_descending_trendline(
            recent_df,
            turning_points_df=turning_points_df,
            wave_points_df=wave_points_df,
        )
        signals = buy_signals[
            buy_signals['descending_trendline_breakthrough_check'] == 'O'
        ]
        print(f"✅ 買入信號: {len(signals)} 個")
        
        if len(signals) > 0:
            print(f"\n   買入信號詳情:")
            for i, (_, row) in enumerate(signals.iterrows()):
                print(f"   {i+1}. {row['date']} - 強度: {row['signal_strength']}/5")
        
        # 結論
        print(f"\n{'='*70}")
        print(f"診斷結果總結：")
        print(f"{'='*70}")
        if total_count > 0:
            print(f"✅ 成功識別 {total_count} 條下降趨勢線")
            print(f"✅ 可以使用修正版測試程式繪製圖表")
            if len(signals) == 0:
                print(f"ℹ️  沒有買入信號（股價未突破趨勢線）")
                print(f"   - 原版測試程式不會繪製趨勢線")
                print(f"   - 請使用修正版測試程式")
        else:
            print(f"❌ 未找到下降趨勢線")
            print(f"   建議測試其他股票或增加天數")
        
    except Exception as e:
        print(f"\n❌ 診斷過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    
    stock_id = sys.argv[1] if len(sys.argv) > 1 else '00631l'
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 360
    
    diagnose_trendlines(stock_id, days)
