import os
import json
from datetime import datetime, timedelta
import pandas as pd
from src.data_initial.kbar_downloader import get_stock_kbars, process_kbars

MARKET_CLOSE_HOUR = 13
MARKET_CLOSE_MINUTE = 30
CLOSING_BAR_TOLERANCE_MINUTES = 5
FETCH_LOG_FILENAME = "_fetch_log.json"
FETCH_COOLDOWN_MINUTES = 1


def has_latest_closing_bar(raw_file_path, trading_date, expected_close_time):
    """
    Check whether the raw kbar file already contains the final bar for the given trading date.
    A small tolerance is allowed to account for market quirks (e.g., last trade a few minutes early).
    """
    if not os.path.exists(raw_file_path):
        return False

    try:
        raw_data = pd.read_csv(raw_file_path, index_col='ts', parse_dates=True)
    except Exception as e:
        print(f"讀取 raw 原始資料失敗：{e}")
        return False

    day_mask = raw_data.index.date == trading_date
    if not day_mask.any():
        return False

    last_timestamp = raw_data.index[day_mask].max()
    expected_close_dt = datetime.combine(trading_date, expected_close_time)
    tolerance = timedelta(minutes=CLOSING_BAR_TOLERANCE_MINUTES)
    return last_timestamp >= (expected_close_dt - tolerance)


def load_fetch_log(log_path):
    """Load the last-fetch timestamps persisted on disk."""
    if not os.path.exists(log_path):
        return {}

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            raw_entries = json.load(f)
    except Exception as e:
        print(f"讀取抓取紀錄失敗：{e}，將忽略紀錄檔")
        return {}

    entries = {}
    for stock_id, ts in raw_entries.items():
        if not isinstance(ts, str):
            continue
        try:
            entries[stock_id] = datetime.fromisoformat(ts)
        except ValueError:
            continue
    return entries


def save_fetch_log(log_path, entries):
    """Persist the last-fetch timestamps for each stock."""
    try:
        serializable = {stock_id: ts.isoformat() for stock_id, ts in entries.items()}
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"寫入抓取紀錄失敗：{e}")

def collect_and_save_kbars():
    """
    根據 'config/StkList.cfg' 清單收集日K和周K資料，並存成 .csv 檔。
    如果檔案已存在：
    1. 檢查最後更新日期，如果不是最新的，則補充數據到今天
    2. 如果數據早於下載總天數(540天)，則重新下載
    """
    stk_list_path = 'config/StkList.cfg'
    data_output_dir = 'Data/kbar'
    DOWNLOAD_DAYS = 540  # 下載天數

    # 確保輸出目錄存在
    os.makedirs(data_output_dir, exist_ok=True)
    fetch_log_path = os.path.join(data_output_dir, FETCH_LOG_FILENAME)
    fetch_log = load_fetch_log(fetch_log_path)
    fetch_cooldown = timedelta(minutes=FETCH_COOLDOWN_MINUTES)

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
        market_close_dt = end_date.replace(hour=MARKET_CLOSE_HOUR,
                                           minute=MARKET_CLOSE_MINUTE,
                                           second=0,
                                           microsecond=0)
        before_close = end_date <= market_close_dt
        today = end_date.date()
        need_download = True
        last_fetch_time = fetch_log.get(stock_id)
        if before_close and last_fetch_time and (end_date - last_fetch_time) < fetch_cooldown:
            print(f"股票 {stock_id} 於 {last_fetch_time.strftime('%H:%M:%S')} 已抓取，間隔未滿 1 分鐘，暫不重複請求")
            continue

        if os.path.exists(daily_file):
            try:
                # 讀取現有數據的最後日期
                existing_data = pd.read_csv(daily_file, index_col='ts', parse_dates=True)
                last_date = existing_data.index.max()
                
                if pd.isna(last_date):
                    need_download = True
                else:
                    last_date_date = last_date.date()
                    days_diff = (today - last_date_date).days

                    if days_diff < 0:
                        print(f"股票 {stock_id} 的數據已是最新")
                        need_download = False
                    elif before_close:
                        need_download = True
                        if last_date_date == today:
                            print(f"盤中時間，強制更新股票 {stock_id} 今日 K 棒數據")
                            start_date = last_date
                        else:
                            if days_diff > DOWNLOAD_DAYS:
                                print(f"股票 {stock_id} 的數據已過期，需要重新下載")
                                start_date = None
                            else:
                                print(f"股票 {stock_id} 的數據需要更新，從 {last_date.date() + timedelta(days=1)} 更新到今天")
                                start_date = last_date + timedelta(days=1)
                    else:
                        if last_date_date < today:
                            need_download = True
                            if days_diff > DOWNLOAD_DAYS:
                                print(f"股票 {stock_id} 的數據已過期，需要重新下載")
                                start_date = None
                            else:
                                print(f"股票 {stock_id} 的數據需要更新，從 {last_date.date() + timedelta(days=1)} 更新到今天")
                                start_date = last_date + timedelta(days=1)
                        else:
                            if has_latest_closing_bar(raw_file, today, market_close_dt.time()):
                                print(f"股票 {stock_id} 今日資料已包含收盤最後一筆，略過更新")
                                need_download = False
                            else:
                                print(f"股票 {stock_id} 今日資料尚未到收盤最後一筆，重新拉取當日資料")
                                need_download = True
                                start_date = last_date
            except Exception as e:
                print(f"讀取現有數據時發生錯誤：{e}，將重新下載")
                start_date = None

        if before_close and need_download:
            print(f"盤中時段，確保抓取股票 {stock_id} 最新資料")
        elif not before_close and need_download:
            print(f"已過收盤，確認股票 {stock_id} 是否補齊最後資料")

        if need_download:
            fetch_log[stock_id] = end_date
            save_fetch_log(fetch_log_path, fetch_log)
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
