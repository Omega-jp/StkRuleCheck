import os
from src.data_initial.kbar_downloader import get_stock_kbars, process_kbars

def collect_and_save_kbars():
    """
    根據 'config/StkList.cfg' 清單收集日K和周K資料，並存成 .csv 檔。
    """
    stk_list_path = 'config/StkList.cfg'
    data_output_dir = 'Data/kbar'

    # 確保輸出目錄存在
    os.makedirs(data_output_dir, exist_ok=True)

    stock_ids = []
    try:
        with open(stk_list_path, 'r', encoding='utf-8') as f:
            for line in f:
                stock_id = line.strip()
                if stock_id:
                    stock_ids.append(stock_id)
    except FileNotFoundError:
        print(f"錯誤：找不到股票清單文件 '{stk_list_path}'。")
        return
    except Exception as e:
        print(f"讀取股票清單文件時發生錯誤：{e}")
        return

    if not stock_ids:
        print("股票清單為空，沒有股票需要收集。")
        return

    for stock_id in stock_ids:
        print(f"正在收集股票 {stock_id} 的K線數據...")
        df = get_stock_kbars(stock_id)
        if df is not None:
            # 保存原始K線數據
            raw_file = os.path.join(data_output_dir, f"{stock_id}_Raw.csv")
            df.index.name = 'ts' # 確保索引名稱為 'ts'
            df.to_csv(raw_file)
            print(f"原始K線數據已保存到：{raw_file}")

            daily_k, weekly_k = process_kbars(df)

            if daily_k is not None:
                daily_k.index.name = 'ts'
                daily_file = os.path.join(data_output_dir, f"{stock_id}_D.csv")
                daily_k.to_csv(daily_file)
                print(f"日K線數據已保存到：{daily_file}")
            else:
                print(f"無法生成股票 {stock_id} 的日K線數據。")

            if weekly_k is not None:
                weekly_k.index.name = 'ts'
                weekly_file = os.path.join(data_output_dir, f"{stock_id}_W.csv")
                weekly_k.to_csv(weekly_file)
                print(f"週K線數據已保存到：{weekly_file}")
            else:
                print(f"無法生成股票 {stock_id} 的週K線數據。")
        else:
            print(f"無法獲取股票 {stock_id} 的K線數據。")
        print("-" * 30) # 分隔線

if __name__ == "__main__":
    collect_and_save_kbars()