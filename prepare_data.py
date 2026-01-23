#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料準備程序：股票規則檢查系統 - 子程序 1
負責：
1. kbar_collector.py - 收集K線數據
2. append_indicator.py - 添加技術指標
3. check_missing_timestamps.py - 檢查資料品質 (選用)
"""

import argparse
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
        print("✓ K線數據收集完成")
        return True
    except Exception as e:
        print(f"✗ K線數據收集失敗: {e}")
        return False

def run_append_indicator():
    """步驟2: 添加技術指標"""
    print_step(2, "添加技術指標")
    try:
        from src.data_initial.append_indicator import append_indicators_to_csv
        append_indicators_to_csv()
        print("✓ 技術指標添加完成")
        return True
    except Exception as e:
        print(f"✗ 技術指標添加失敗: {e}")
        return False

def run_check_missing_timestamps(baseline_stock):
    """步驟3: 檢查資料品質"""
    print_step(3, "檢查資料品質 (缺少時間戳)")
    try:
        from check_missing_timestamps import check_all
        print(f"使用基準股票: {baseline_stock}")
        check_all(
            data_dir='Data/kbar',
            suffix='D',  # 預設檢查日線
            baseline=baseline_stock,
            limit=10
        )
        print("✓ 資料品質檢查完成")
        return True
    except Exception as e:
        print(f"✗ 資料品質檢查失敗: {e}")
        return False

def parse_args():
    parser = argparse.ArgumentParser(description="資料準備程序：股票規則檢查系統 - 子程序 1")
    parser.add_argument('--check-missing', action='store_true', help='啟用資料品質檢查 (檢查缺少的時間戳)')
    parser.add_argument('--baseline', type=str, default='00631L', help='資料品質檢查的基準股票代碼 (預設: 00631L)')
    return parser.parse_args()

def main():
    """主函數"""
    args = parse_args()
    
    print("\n" + "="*80)
    print("股票規則檢查系統 - 資料準備程序 (prepare_data)")
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.check_missing:
        print(f"已啟用資料品質檢查 (基準: {args.baseline})")
    print("="*80)
    
    start_time = time.time()
    
    # 確保必要的目錄存在
    os.makedirs('Data/kbar', exist_ok=True)
    
    # 定義執行步驟
    steps = [
        ("收集K線數據", run_kbar_collector),
        ("添加技術指標", run_append_indicator)
    ]
    
    # 若有啟用檢查，加入步驟清單
    if args.check_missing:
        steps.append(("檢查資料品質", lambda: run_check_missing_timestamps(args.baseline)))
    
    success_steps = 0
    for step_name, step_func in steps:
        if step_func():
            success_steps += 1
        else:
            print(f"\n⚠️  步驟 '{step_name}' 執行失敗，但繼續執行後續步驟...")
    
    # 執行結果總結
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "="*80)
    print("資料準備 - 執行結果總結")
    print(f"總執行時間: {duration:.2f} 秒")
    print(f"成功步驟: {success_steps}/{len(steps)}")
    
    if success_steps == len(steps):
        print("🎉 資料準備完成！")
        print("\n輸出文件位置:")
        print("- K線數據: Data/kbar/")
    else:
        print("⚠️  部分步驟執行失敗，請檢查錯誤信息")
    
    print(f"結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

if __name__ == "__main__":
    main()
