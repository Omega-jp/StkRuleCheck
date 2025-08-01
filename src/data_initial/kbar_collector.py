import os
from datetime import datetime, timedelta
import pandas as pd
from src.data_initial.kbar_downloader import get_stock_kbars, process_kbars

def collect_and_save_kbars():
    """
    根據 'config/StkList.cfg' 清單收集日K和周K資料，並存成 .csv 檔。
    如果檔案已存在：
    1. 檢查最後更新日期，如果不是最新的，則補充數據到今天
    2. 如果數據早於下載總天數(200天)，則重新下載
    """
    stk_list_path = 'config/StkList.cfg'
    data_output_dir = 'Data/kbar'
    DOWNLOAD_DAYS = 200  # 下載天數

    # 確保輸出目錄存在
    os.makedirs(data_output_dir, exist_ok=True)

    stock_ids = []
    try:
        with open(stk_list_path, 'r', encoding='utf-8') as f:
            next(f)  # 跳過標頭行
            for line in f:
                parts = line.strip().split(',')
                if parts:
                    stock_id = parts[0].strip()
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
        print(f"處理股票 {stock_id} 的K線數據...")
        daily_file = os.path.join(data_output_dir, f"{stock_id}_D.csv")
        weekly_file = os.path.join(data_output_dir, f"{stock_id}_W.csv")
        raw_file = os.path.join(data_output_dir, f"{stock_id}_Raw.csv")
        
        start_date = None
        end_date = datetime.now()
        need_download = True

        if os.path.exists(daily_file):
            try:
                # 讀取現有數據的最後日期
                existing_data = pd.read_csv(daily_file, index_col='ts', parse_dates=True)
                last_date = existing_data.index.max()
                
                # 檢查數據是否需要更新
                days_diff = (end_date - last_date).days
                
                # 檢查數據是否需要更新
                if last_date.date() >= end_date.date():  # 數據是最新的
                    print(f"股票 {stock_id} 的數據已是最新")
                    need_download = False
                else:
                    need_download = True
                    if days_diff > DOWNLOAD_DAYS:  # 數據太舊
                        print(f"股票 {stock_id} 的數據已過期，需要重新下載")
                        start_date = None  # 重新下載全部數據
                    else:  # 需要補充數據
                        print(f"股票 {stock_id} 的數據需要更新，從 {last_date.date() + timedelta(days=1)} 更新到今天")
                        start_date = last_date + timedelta(days=1)  # 從最後一天的下一天開始更新
            except Exception as e:
                print(f"讀取現有數據時發生錯誤：{e}，將重新下載")
                start_date = None

        if need_download:
            df = get_stock_kbars(stock_id, start_date=start_date, end_date=end_date)
            if df is not None:
                if start_date is not None:  # 如果是更新數據
                    # 合併新舊數據
                    try:
                        old_data = pd.read_csv(raw_file, index_col='ts', parse_dates=True)
                        df = pd.concat([old_data[old_data.index < start_date], df])
                    except Exception as e:
                        print(f"合併數據時發生錯誤：{e}，將使用新下載的數據")

                # 保存原始K線數據
                df.index.name = 'ts'
                df.to_csv(raw_file)
                print(f"原始K線數據已保存到：{raw_file}")

                daily_k, weekly_k = process_kbars(df)

                if daily_k is not None:
                    daily_k.index.name = 'ts'
                    daily_k.to_csv(daily_file)
                    print(f"日K線數據已保存到：{daily_file}")
                else:
                    print(f"無法生成股票 {stock_id} 的日K線數據。")

                if weekly_k is not None:
                    weekly_k.index.name = 'ts'
                    weekly_k.to_csv(weekly_file)
                    print(f"週K線數據已保存到：{weekly_file}")
                else:
                    print(f"無法生成股票 {stock_id} 的週K線數據。")
            else:
                print(f"無法獲取股票 {stock_id} 的K線數據。")
        print("-" * 30)  # 分隔線

if __name__ == "__main__":
    collect_and_save_kbars()