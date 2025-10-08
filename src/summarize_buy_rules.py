import pandas as pd
import os
import importlib.util
from src.validate_buy_rule import load_stock_data

def get_buy_rules():
    rules = []
    buy_rule_dir = 'src/buyRule'
    
    exclude_modules = {'long_term_descending_trendline'}
    for filename in os.listdir(buy_rule_dir):
        if not filename.endswith('.py') or filename == '__init__.py':
            continue

        rule_name = filename[:-3]
        if rule_name in exclude_modules:
            continue

        rules.append(rule_name)
    return rules

def get_latest_result(df, rule_name, stock_id):
    module_path = f'src.buyRule.{rule_name}'
    module = importlib.import_module(module_path)
    
    # 根據不同的規則名稱調用不同的函數
    if 'four_seas_dragon' in rule_name:
        check_func = getattr(module, f'check_{rule_name.replace("breakthrough_", "")}', None)
        if check_func is None:
            return 'Error: Function not found'
        rule_df = check_func(df, [5,10,20,60], stock_id)
    elif 'diamond_cross' in rule_name:
        check_func = getattr(module, f'check_{rule_name.replace("breakthrough_", "")}', None)
        if check_func is None:
            return 'Error: Function not found'
        
        # 鑽石劍需要轉折點數據
        from src.baseRule.turning_point_identification import identify_turning_points
        if 'ma5' not in df.columns:
            df['ma5'] = df['Close'].rolling(window=5, min_periods=1).mean()
        turning_points_df = identify_turning_points(df)
        rule_df = check_func(df, turning_points_df)
    elif 'resistance_line' in rule_name:
        # 處理壓力線突破規則
        check_func = getattr(module, 'check_resistance_line_breakthrough', None)
        if check_func is None:
            return 'Error: Function not found'
        
        # 壓力線突破也需要轉折點數據
        from src.baseRule.turning_point_identification import identify_turning_points
        if 'ma5' not in df.columns:
            df['ma5'] = df['Close'].rolling(window=5, min_periods=1).mean()
        turning_points_df = identify_turning_points(df)
        rule_df = check_func(df, turning_points_df)
    else:
        check_func = getattr(module, f'check_{rule_name.replace("breakthrough_", "")}', None)
        if check_func is None:
            return 'Error: Function not found'
        rule_df = check_func(df)
    
    if rule_df.empty:
        return 'No data'
    
    latest = rule_df.iloc[-1]
    check_col = next((col for col in rule_df.columns if 'check' in col), None)
    return latest[check_col] if check_col else 'No check column'

def get_rule_display_name(rule_name):
    """將規則檔案名稱轉換為更易讀的顯示名稱"""
    name_mapping = {
        'breakthrough_san_yang_kai_tai': '三陽開泰',
        'breakthrough_four_seas_dragon': '四海游龍',
        'macd_golden_cross_above_zero': 'MACD黃金交叉零軸上',
        'macd_golden_cross_above_zero_positive_histogram': 'MACD黃金交叉零軸上正柱',
        'diamond_cross': '鑽石劍',
        'breakthrough_resistance_line': '壓力線突破'
    }
    return name_mapping.get(rule_name, rule_name)

def main():
    stock_list_file = 'config/stklist.cfg'
    stock_ids = []
    stock_names = {}
    
    with open(stock_list_file, 'r', encoding='utf-8') as f:
        next(f)  # 跳過標頭行
        for line in f:
            parts = line.strip().split(',', 1)  # 只分割第一個逗號，保留中文名稱中可能的逗號
            if parts and len(parts) >= 2:
                stock_id = parts[0].strip()
                stock_name = parts[1].strip() if len(parts) > 1 else ""
                if stock_id:
                    stock_ids.append(stock_id)
                    stock_names[stock_id] = stock_name
    
    rules = get_buy_rules()
    print(f"找到的買入規則: {rules}")
    
    summary_data = []
    
    for i, stock_id in enumerate(stock_ids):
        print(f"處理股票 {i+1}/{len(stock_ids)}: {stock_id} ({stock_names.get(stock_id, '')})")
        
        df = load_stock_data(stock_id, 'D')
        if df is None:
            print(f"  無法載入 {stock_id} 的數據，跳過")
            continue
        
        row = {
            'StockID': stock_id,
            'StockName': stock_names.get(stock_id, "")
        }
        
        for rule in rules:
            try:
                result = get_latest_result(df, rule, stock_id)
                rule_display_name = get_rule_display_name(rule)
                row[rule_display_name] = result
                print(f"  {rule_display_name}: {result}")
            except Exception as e:
                print(f"  {rule} 處理錯誤: {e}")
                row[get_rule_display_name(rule)] = 'Error'
        
        summary_data.append(row)
        print(f"  {stock_id} 處理完成")
        print("-" * 50)
    
    if not summary_data:
        print("沒有成功處理任何股票數據")
        return
    
    summary_df = pd.DataFrame(summary_data)
    
    # 重新排列欄位順序，讓更重要的規則排在前面
    column_order = ['StockID', 'StockName', '壓力線突破', '三陽開泰', '四海游龍', 
                   'MACD黃金交叉零軸上', 'MACD黃金交叉零軸上正柱', '鑽石劍']
    
    # 確保所有欄位都存在，如果不存在則添加
    for col in column_order:
        if col not in summary_df.columns:
            summary_df[col] = 'Not Available'
    
    # 重新排序欄位
    other_cols = [col for col in summary_df.columns if col not in column_order]
    summary_df = summary_df[column_order + other_cols]
    
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'buy_rules_summary.csv')
    summary_df.to_csv(output_path, index=False, encoding='utf-8-sig')  # 使用 utf-8-sig 確保中文正確顯示
    
    print(f'\n匯總結果已保存至: {output_path}')
    print(f'共處理 {len(summary_data)} 支股票')
    
    # 統計各規則的觸發情況
    print("\n=== 各規則觸發統計 ===")
    for rule_col in column_order[2:]:  # 跳過 StockID 和 StockName
        if rule_col in summary_df.columns:
            triggered_count = len(summary_df[summary_df[rule_col] == 'O'])
            total_count = len(summary_df[summary_df[rule_col].notna() & (summary_df[rule_col] != 'Error') & (summary_df[rule_col] != 'Not Available')])
            print(f"{rule_col}: {triggered_count}/{total_count} ({triggered_count/max(total_count,1)*100:.1f}%)")

if __name__ == '__main__':
    main()


