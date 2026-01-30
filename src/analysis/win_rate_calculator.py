#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
勝率分析核心引擎 v1.0
功能：模擬交易流程，計算勝率、盈虧比等指標。
支持核心邏輯：INITIAL (破 Level 出) -> TRENDING (破 5MA 賣半, 破 10MA 清倉)
"""

import pandas as pd
import numpy as np

class WinRateCalculator:
    def __init__(self, initial_capital=1.0):
        self.initial_capital = initial_capital

    def backtest(self, stock_id, df):
        """
        執行回測
        df 必須包含: Open, High, Low, Close, ma5, ma10, ms_level, ms_buy_signal
        """
        trades = []
        in_position = False
        current_trade = None
        
        # 遍歷每一天
        for i in range(len(df)):
            row = df.iloc[i]
            date = df.index[i]
            
            # --- 1. 出場邏輯 (若目前持有部位) ---
            if in_position:
                self._process_exit(row, date, current_trade, df, i)
                if current_trade['units'] == 0:
                    trades.append(current_trade)
                    in_position = False
                    current_trade = None
                    continue # 當天已清倉，不考慮當天進場
            
            # --- 2. 進場邏輯 (若目前無部位) ---
            if not in_position:
                if row['ms_buy_signal'] == 'O':
                    # 檢查次日是否有資料進場
                    if i + 1 < len(df):
                        next_row = df.iloc[i+1]
                        next_date = df.index[i+1]
                        
                        current_trade = {
                            'stock_id': stock_id,
                            'entry_date': next_date,
                            'entry_price': next_row['Open'],
                            'status': 'INITIAL',
                            'units': 1.0,
                            'sell_half_date': None,
                            'sell_half_price': None,
                            'exit_date': None,
                            'exit_price': None,
                            'standing_on_ma5_date': None
                        }
                        in_position = True
        
        return trades

    def _process_exit(self, row, date, trade, df, idx):
        """處理部位狀態與出場判斷"""
        
        # A. 狀態轉場：INITIAL -> TRENDING
        if trade['status'] == 'INITIAL':
            if row['Close'] >= row['ma5']:
                trade['status'] = 'TRENDING'
                trade['standing_on_ma5_date'] = date
        
        # B. 出場判斷
        # 若在次一交易日開盤賣出，我們會記錄觸發日，但在計算時以觸發日次日的開盤價計算
        # 為了簡化邏輯，此處實作：若當日「收盤」符合條件，則「次日開盤」賣出。
        
        # 1. INITIAL 階段：破 ms_level 則全賣
        if trade['status'] == 'INITIAL':
            if not np.isnan(row['ms_level']) and row['Close'] < row['ms_level']:
                self._execute_sell(trade, df, idx, amount='ALL')
                return

        # 2. TRENDING 階段：
        if trade['status'] == 'TRENDING':
            # 破 5MA 賣一半 (僅限尚未賣過一半時)
            if trade['sell_half_date'] is None:
                if row['Close'] < row['ma5']:
                    # 檢查是否同時破 10MA，若同時破則直接全賣
                    if row['Close'] < row['ma10']:
                        self._execute_sell(trade, df, idx, amount='ALL')
                    else:
                        self._execute_sell(trade, df, idx, amount='HALF')
                    return
            
            # 破 10MA 全賣
            if row['Close'] < row['ma10']:
                self._execute_sell(trade, df, idx, amount='ALL')

    def _execute_sell(self, trade, df, trigger_idx, amount='ALL'):
        """執行賣出模擬 (次日開盤價)"""
        # 取得賣出價格 (次日 Open)
        sell_idx = trigger_idx + 1
        if sell_idx >= len(df):
            # 若已經是最後一天，以最後一天 Close 結算
            sell_price = df.iloc[trigger_idx]['Close']
            sell_date = df.index[trigger_idx]
        else:
            sell_price = df.iloc[sell_idx]['Open']
            sell_date = df.index[sell_idx]

        if amount == 'HALF':
            trade['sell_half_date'] = sell_date
            trade['sell_half_price'] = sell_price
            trade['units'] = 0.5
        else:
            trade['exit_date'] = sell_date
            trade['exit_price'] = sell_price
            trade['units'] = 0
            
    def calculate_summary(self, trades):
        """統計勝率資訊"""
        if not trades:
            return None
            
        results = []
        for t in trades:
            # 計算總賣出額
            # 若只成交一半 (沒賣全)，這筆交易不算完整 (但在回測中應該都會全賣)
            if t['exit_price'] is None: continue 
            
            if t['sell_half_price']:
                realized_sell_total = (t['sell_half_price'] * 0.5) + (t['exit_price'] * 0.5)
            else:
                realized_sell_total = t['exit_price']
            
            profit_pct = (realized_sell_total - t['entry_price']) / t['entry_price']
            results.append(profit_pct)
        
        if not results: return None
        
        results_np = np.array(results)
        wins = results_np[results_np > 0]
        losses = results_np[results_np <= 0]
        
        summary = {
            'total_trades': len(results),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': len(wins) / len(results) if len(results) > 0 else 0,
            'avg_profit': wins.mean() if len(wins) > 0 else 0,
            'avg_loss': losses.mean() if len(losses) > 0 else 0,
            'max_profit': results_np.max(),
            'max_loss': results_np.min(),
            'total_return': (1 + results_np).prod() - 1 # 累計複利報酬
        }
        return summary
