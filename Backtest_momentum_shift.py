#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Momentum Shift 勝率回測整合腳本
流程：下載 10 年資料 -> 計算指標 -> 產生信號 -> 執行回測 -> 輸出報表
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# 加入 src 路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data_initial.twse_downloader import TWSEDownloader
from src.buyRule.momentum_shift import compute_momentum_shift
from src.analysis.win_rate_calculator import WinRateCalculator

import glob

def run_win_rate_analysis(stock_id, years=10, force_download=False):
    output_dir = 'Data/backtest_data'
    stock_dir = os.path.join(output_dir, stock_id)
    
    # 檢查是否有現存的年度資料檔
    existing_files = glob.glob(os.path.join(stock_dir, "*.csv"))
    
    # 1. 取得資料
    if not existing_files or force_download:
        downloader = TWSEDownloader(output_dir=output_dir)
        df_raw = downloader.download_history(stock_id, years=years)
    else:
        print(f"📖 讀取現有資料目錄: {stock_dir}")
        df_list = []
        for f in existing_files:
            try:
                df_part = pd.read_csv(f, index_col='ts', parse_dates=True)
                df_list.append(df_part)
            except Exception as e:
                print(f"⚠️ 讀取檔案 {f} 失敗: {e}")
        
        if df_list:
            df_raw = pd.concat(df_list).sort_index()
        else:
            df_raw = pd.DataFrame()
    
    if df_raw is None or df_raw.empty:
        print(f"❌ 無法取得 {stock_id} 的回測資料")
        return

    print(f"🛠️ 正在準備指標與信號: {stock_id}")
    
    # 2. 計算基礎指標 (MA5, MA10)
    df_calc = df_raw.copy().sort_index()
    df_calc.index = pd.to_datetime(df_calc.index) # 確保索引是日期類型
    df_calc['ma5'] = df_calc['Close'].rolling(window=5).mean()
    df_calc['ma10'] = df_calc['Close'].rolling(window=10).mean()
    
    # 3. 計算 Momentum Shift 信號
    # 註：compute_momentum_shift 會自動處理轉折點
    df_signals = compute_momentum_shift(df_calc)
    
    if df_signals.empty:
        print("❌ 訊號計算失敗")
        return

    # 4. 執行回測
    print(f"📉 執行回測引擎...")
    calculator = WinRateCalculator()
    trades = calculator.backtest(stock_id, df_signals)
    
    # 5. 輸出結果
    if not trades:
        print(f"ℹ️ 在 {years} 年內未發現任何 Momentum Shift 買進訊號")
        return

    # 存檔明細
    analysis_out_dir = 'output/analysis'
    os.makedirs(analysis_out_dir, exist_ok=True)
    
    df_trades = pd.DataFrame(trades)
    
    # 計算單筆盈虧 (加權盈虧)
    def calc_profit_pct(t):
        if t['sell_half_price'] and not np.isnan(t['sell_half_price']):
            realized = (t['sell_half_price'] * 0.5) + (t['exit_price'] * 0.5)
        else:
            realized = t['exit_price']
        return (realized - t['entry_price']) / t['entry_price']

    df_trades['profit_pct'] = df_trades.apply(calc_profit_pct, axis=1)
    df_trades['result'] = df_trades['profit_pct'].apply(lambda x: 'Win' if x > 0 else 'Loss')
    
    trades_file = os.path.join(analysis_out_dir, f"{stock_id}_momentum_shift_trades.csv")
    df_trades.to_csv(trades_file, index=False)
    print(f"✅ 交易明細已存至: {trades_file}")

    # 輸出統計摘要
    summary = calculator.calculate_summary(trades)
    if summary:
        print("\n" + "="*40)
        print(f"📊 {stock_id} Momentum Shift 回測摘要 ({years}年)")
        print("-" * 40)
        print(f"總交易次數: {summary['total_trades']}")
        print(f"勝場 / 敗場: {summary['wins']} / {summary['losses']}")
        print(f"勝率: {summary['win_rate']:.2%}")
        print(f"平均獲利: {summary['avg_profit']:.2%}")
        print(f"平均虧損: {summary['avg_loss']:.2%}")
        print(f"最高獲利: {summary['max_profit']:.2%}")
        print(f"最高虧損: {summary['max_loss']:.2%}")
        print(f"複利總報酬: {summary['total_return']:.2%}")
        print("="*40 + "\n")

        # 存檔彙總
        summary['stock_id'] = stock_id
        summary['test_period'] = f"{df_raw.index.min()} to {df_raw.index.max()}"
        df_summary = pd.DataFrame([summary])
        summary_file = os.path.join(analysis_out_dir, "momentum_shift_summary_batch.csv")
        
        if os.path.exists(summary_file):
            df_existing = pd.read_csv(summary_file)
            df_final = pd.concat([df_existing[df_existing['stock_id'] != stock_id], df_summary])
        else:
            df_final = df_summary
            
        df_final.to_csv(summary_file, index=False)
        print(f"📊 彙總統計已更新: {summary_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Momentum Shift 勝率回測整合腳本')
    parser.add_argument('stock_id', nargs='?', help='股票代碼 (例如: 2330)')
    parser.add_argument('--years', type=int, default=3, help='回測年數 (預設: 3，10年需較長時間抓取)')
    args = parser.parse_args()
    
    if args.stock_id:
        run_win_rate_analysis(args.stock_id, args.years)
    else:
        print("💡 未指定股票代碼，執行預設測試：2330 (3年)")
        run_win_rate_analysis('2330', 3)
