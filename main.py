#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主程序：股票規則檢查系統
串接四個子程序：
1. kbar_collector.py - 收集K線數據
2. append_indicator.py - 添加技術指標
3. validate_buy_rule.py - 驗證買入規則
4. summarize_buy_rules.py - 總結買入規則
"""

import os
import sys
import time
from datetime import datetime

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def print_step(step_num, description):
    """打印步驟信息"""
    print(f"\n{'='*60}")
    print(f"步驟 {step_num}: {description}")
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

def run_kbar_collector():
    """步驟1: 收集K線數據"""
    print_step(1, "收集K線數據")
    try:
        from src.data_initial.kbar_collector import collect_and_save_kbars
        collect_and_save_kbars()
        print("[v] K線數據收集完成")
        return True
    except Exception as e:
        print(f"[x] K線數據收集失敗: {e}")
        return False

def run_append_indicator():
    """步驟2: 添加技術指標"""
    print_step(2, "添加技術指標")
    try:
        from src.data_initial.append_indicator import append_indicators_to_csv
        append_indicators_to_csv()
        print("[v] 技術指標添加完成")
        return True
    except Exception as e:
        print(f"[x] 技術指標添加失敗: {e}")
        return False

def run_validate_buy_rule():
    """步驟3: 驗證買入規則"""
    print_step(3, "驗證買入規則")
    try:
        from src.validate_buy_rule import get_stock_list, validate_buy_rule
        
        # 獲取股票列表
        stock_ids = get_stock_list()
        if not stock_ids:
            print("未找到任何股票代碼，請檢查 config/stklist.cfg 文件。")
            return False
        
        print(f"找到 {len(stock_ids)} 支股票，開始驗證買入規則...")
        
        # 逐一驗證每支股票
        success_count = 0
        for i, stock_id in enumerate(stock_ids, 1):
            try:
                print(f"\n處理進度: {i}/{len(stock_ids)} - {stock_id}")
                validate_buy_rule(stock_id)
                success_count += 1
            except Exception as e:
                print(f"處理股票 {stock_id} 時發生錯誤: {e}")
        
        print(f"\n[v] 買入規則驗證完成，成功處理 {success_count}/{len(stock_ids)} 支股票")
        return True
    except Exception as e:
        print(f"[x] 買入規則驗證失敗: {e}")
        return False

def run_summarize_buy_rules():
    """步驟4: 總結買入規則"""
    print_step(4, "總結買入規則")
    try:
        from src.summarize_buy_rules import main as summarize_main
        summarize_main()
        print("[v] 買入規則總結完成")
        return True
    except Exception as e:
        print(f"[x] 買入規則總結失敗: {e}")
        return False

def main():
    """主函數"""
    print("\n" + "="*80)
    print("股票規則檢查系統 - 完整流程執行")
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    start_time = time.time()
    
    # 確保必要的目錄存在
    os.makedirs('Data/kbar', exist_ok=True)
    os.makedirs('output/chart', exist_ok=True)
    os.makedirs('output/buy_rules', exist_ok=True)
    
    # 執行步驟
    steps = [
        ("收集K線數據", run_kbar_collector),
        ("添加技術指標", run_append_indicator),
        ("驗證買入規則", run_validate_buy_rule),
        ("總結買入規則", run_summarize_buy_rules)
    ]
    
    success_steps = 0
    for step_name, step_func in steps:
        if step_func():
            success_steps += 1
        else:
            print(f"\n[!]  步驟 '{step_name}' 執行失敗，但繼續執行後續步驟...")
    
    # 執行結果總結
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "="*80)
    print("執行結果總結")
    print(f"總執行時間: {duration:.2f} 秒")
    print(f"成功步驟: {success_steps}/{len(steps)}")
    
    if success_steps == len(steps):
        print("[v] 所有步驟執行成功！")
        print("\n輸出文件位置:")
        print("- K線數據: Data/kbar/")
        print("- 規則驗證結果: output/buy_rules/")
        print("- K線圖表: output/chart/")
        print("- 規則總結: output/buy_rules_summary.csv")
    else:
        print("[!]  部分步驟執行失敗，請檢查錯誤信息")
    
    print(f"結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

if __name__ == "__main__":
    main()