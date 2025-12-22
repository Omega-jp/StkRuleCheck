import os
import re

import pandas as pd

from src.data_initial.calculate_impulse_macd import calculate_impulse_macd
from src.data_initial.calculate_kd import calculate_kd
from src.data_initial.calculate_macd import calculate_macd
from src.data_initial.calculate_ma import calculate_ma
from src.data_initial.kbar_downloader import process_kbars


def _base_name(col: str) -> str:
    """移除欄位尾端自動加的 .1/.2 後綴"""
    return re.sub(r"(?:\.\d+)+$", "", col)


def _rebuild_kbars_from_raw(stock_id: str, data_dir: str) -> None:
    """如果缺 _D/_W 且有 Raw，從 Raw 重建日/週線 CSV。"""
    raw_path = os.path.join(data_dir, f"{stock_id}_Raw.csv")
    if not os.path.exists(raw_path):
        return

    need_daily = not os.path.exists(os.path.join(data_dir, f"{stock_id}_D.csv"))
    need_weekly = not os.path.exists(os.path.join(data_dir, f"{stock_id}_W.csv"))
    if not (need_daily or need_weekly):
        return

    try:
        raw_df = pd.read_csv(raw_path, index_col="ts", parse_dates=True)
    except Exception as exc:
        print(f"重建 {stock_id}: 無法讀取 Raw -> {exc}")
        return

    column_mapping = {
        "開盤價": "Open",
        "最高價": "High",
        "最低價": "Low",
        "收盤價": "Close",
        "成交量": "Volume",
    }
    if "收盤價" in raw_df.columns:
        raw_df.rename(columns=column_mapping, inplace=True)

    required = ["Open", "High", "Low", "Close", "Volume"]
    missing = [c for c in required if c not in raw_df.columns]
    if missing:
        print(f"重建 {stock_id}: Raw 缺欄位 {missing}，略過")
        return

    raw_df = raw_df[required]
    daily_k, weekly_k = process_kbars(raw_df)
    if daily_k is not None and need_daily:
        daily_k.index.name = "ts"
        daily_path = os.path.join(data_dir, f"{stock_id}_D.csv")
        daily_k.to_csv(daily_path)
        print(f"重建 {stock_id} 日線 -> {daily_path}")
    if weekly_k is not None and need_weekly:
        weekly_k.index.name = "ts"
        weekly_path = os.path.join(data_dir, f"{stock_id}_W.csv")
        weekly_k.to_csv(weekly_path)
        print(f"重建 {stock_id} 週線 -> {weekly_path}")

def append_indicators_to_csv(input_dir='Data/kbar', output_dir='Data/kbar'):
    """
    Reads CSV files from input_dir, calculates KD, MACD, MA, and Impulse MACD, 
    and appends them to the DataFrame, then saves the updated DataFrame back to the output_dir.
    """
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' not found.")
        return

    os.makedirs(output_dir, exist_ok=True)

    # 先用 Raw 重建缺失的 D/W 檔
    raw_stock_ids = {
        fname[:-8]  # 去掉 _Raw.csv
        for fname in os.listdir(input_dir)
        if fname.endswith('_Raw.csv')
    }
    for stock_id in sorted(raw_stock_ids):
        _rebuild_kbars_from_raw(stock_id, input_dir)

    for filename in os.listdir(input_dir):
        if filename.endswith('_D.csv') or filename.endswith('_W.csv'): # Process daily and weekly kbar files
            file_path = os.path.join(input_dir, filename)
            print(f"Processing {filename}...")

            try:
                df = pd.read_csv(file_path, index_col='ts', parse_dates=True)

                # Ensure necessary columns are numeric
                for col in ['Open', 'High', 'Low', 'Close']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                df.dropna(subset=['Open', 'High', 'Low', 'Close'], inplace=True)

                if df.empty:
                    print(f"Skipping {filename}: DataFrame is empty after cleaning.")
                    continue

                # 清除既有指標欄位（含自動加的 .1/.2 後綴）避免重複
                indicator_bases = {
                    'RSV', '%K', '%D',
                    'EMA_short', 'EMA_long', 'MACD', 'Signal', 'Histogram',
                    'MA_5', 'MA_10', 'MA_20', 'MA_60', 'MA_120',
                    'ma5', 'ma10', 'ma20', 'ma60', 'ma120',
                    'ImpulseMACD', 'ImpulseSignal', 'ImpulseHistogram'
                }
                columns_to_remove = [col for col in df.columns if _base_name(col) in indicator_bases]
                if columns_to_remove:
                    df.drop(columns=columns_to_remove, inplace=True, errors='ignore')

                # Calculate KD
                kd_df = calculate_kd(df.copy())
                # Round KD values to two decimal places
                kd_df['RSV'] = kd_df['RSV'].round(2)
                kd_df['%K'] = kd_df['%K'].round(2)
                kd_df['%D'] = kd_df['%D'].round(2)
                df = pd.concat([df, kd_df], axis=1)

                # Calculate MACD
                macd_df = calculate_macd(df.copy())
                # Round MACD values to two decimal places
                macd_df['MACD'] = macd_df['MACD'].round(2)
                macd_df['Signal'] = macd_df['Signal'].round(2)
                macd_df['Histogram'] = macd_df['Histogram'].round(2)
                df = pd.concat([df, macd_df], axis=1)

                # Calculate MA
                ma_df = calculate_ma(df.copy())
                # Round MA values to two decimal places
                for col in ma_df.columns:
                    ma_df[col] = ma_df[col].round(2)
                df = pd.concat([df, ma_df], axis=1)

                # Calculate Impulse MACD
                impulse_macd_df = calculate_impulse_macd(df.copy())
                # Round Impulse MACD values to two decimal places
                for col in impulse_macd_df.columns:
                    impulse_macd_df[col] = impulse_macd_df[col].round(2)
                df = pd.concat([df, impulse_macd_df], axis=1)

                # 確保欄位名稱唯一（若原始檔仍有重複 OHLC/Volume 後綴，保留第一個）
                seen = set()
                dedup_cols = []
                for col in df.columns:
                    base = _base_name(col)
                    if base in seen:
                        continue
                    seen.add(base)
                    dedup_cols.append(col)
                df = df[dedup_cols]

                # Save the updated DataFrame
                output_file_path = os.path.join(output_dir, filename)
                df.to_csv(output_file_path)
                print(f"Indicators (including Impulse MACD) appended and saved to {output_file_path}")

            except Exception as e:
                print(f"Error processing {filename}: {e}")
        else:
            print(f"Skipping {filename}: Not a daily or weekly kbar CSV.")
    print("-" * 30)

if __name__ == "__main__":
    append_indicators_to_csv()
