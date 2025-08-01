import pandas as pd
import os
import importlib.util
from src.validate_buy_rule import load_stock_data

def get_buy_rules():
    rules = []
    buy_rule_dir = 'src/buyRule'
    for filename in os.listdir(buy_rule_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            rule_name = filename[:-3]
            rules.append(rule_name)
    return rules

def get_latest_result(df, rule_name, stock_id):
    module_path = f'src.buyRule.{rule_name}'
    module = importlib.import_module(module_path)
    check_func = getattr(module, f'check_{rule_name.replace("breakthrough_", "")}', None)
    if check_func is None:
        return 'Error: Function not found'
    rule_df = check_func(df) if 'four_seas_dragon' not in rule_name else check_func(df, [5,10,20,60], stock_id)
    if rule_df.empty:
        return 'No data'
    latest = rule_df.iloc[-1]
    check_col = next((col for col in rule_df.columns if 'check' in col), None)
    return latest[check_col] if check_col else 'No check column'

def main():
    stock_list_file = 'config/stklist.cfg'
    stock_ids = []
    with open(stock_list_file, 'r', encoding='utf-8') as f:
        next(f)  # 跳過標頭行
        for line in f:
            parts = line.strip().split(',')
            if parts:
                stock_id = parts[0].strip()
                if stock_id:
                    stock_ids.append(stock_id)
    
    rules = get_buy_rules()
    summary_data = []
    for stock_id in stock_ids:
        df = load_stock_data(stock_id, 'D')
        if df is None:
            continue
        row = {'StockID': stock_id}
        for rule in rules:
            result = get_latest_result(df, rule, stock_id)
            row[rule] = result
        summary_data.append(row)
    
    summary_df = pd.DataFrame(summary_data)
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'buy_rules_summary.csv')
    summary_df.to_csv(output_path, index=False)
    print(f'Summary CSV saved to {output_path}')

if __name__ == '__main__':
    main()