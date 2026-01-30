#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TWSE (證交所) 歷史資料下載器 v1.0
功能：從證交所官網抓取指定股票過去 N 年的日成交資訊 (STOCK_DAY)
"""

import requests
import pandas as pd
import os
import time
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class TWSEDownloader:
    def __init__(self, output_dir='Data/backtest_data'):
        self.output_dir = output_dir
        self.base_url = "https://www.twse.com.tw/exchangeReport/STOCK_DAY"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        os.makedirs(self.output_dir, exist_ok=True)

    def _convert_date_to_ad(self, date_str):
        """民國曆轉西元日期 (103/01/02 -> 2014-01-02)"""
        try:
            parts = date_str.split('/')
            year = int(parts[0]) + 1911
            return f"{year}-{parts[1]}-{parts[2]}"
        except:
            return None

    def fetch_month_data(self, stock_id, date_str):
        """抓取特定月份資料 (date_str: YYYYMMDD)"""
        params = {
            'response': 'json',
            'date': date_str,
            'stockNo': stock_id
        }
        
        try:
            # 加入 verify=False 避免部分環境下 SSL 憑證檢查失敗
            response = requests.get(self.base_url, params=params, headers=self.headers, timeout=10, verify=False)
            if response.status_code != 200:
                print(f"❌ 請求失敗: Status {response.status_code}")
                return None
            
            data = response.json()
            if data.get('stat') != 'OK' or 'data' not in data:
                print(f"⚠️ 找不到資料: {date_str} for {stock_id} (可能當月休市或無成交)")
                return None
            
            # 轉換欄位內容
            # TWSE Data Index: 
            # 0:日期, 1:成交股數, 2:成交金額, 3:開盤價, 4:最高價, 5:最低價, 6:收盤價, 7:漲跌價差, 8:成交筆數
            raw_rows = data['data']
            cleaned_rows = []
            for row in raw_rows:
                ad_date = self._convert_date_to_ad(row[0])
                if ad_date:
                    cleaned_rows.append({
                        'ts': ad_date,
                        'Volume': int(row[1].replace(',', '')),
                        'Open': float(row[3].replace(',', '')),
                        'High': float(row[4].replace(',', '')),
                        'Low': float(row[5].replace(',', '')),
                        'Close': float(row[6].replace(',', ''))
                    })
            return cleaned_rows
        except Exception as e:
            print(f"❌ 發生錯誤: {e}")
            return None

    def download_history(self, stock_id, years=10):
        """抓取過去 N 年歷史資料，並按年度存檔"""
        print(f"🚀 開始從證交所抓取 {stock_id} 過去 {years} 年資料...")
        
        # 建立股票專屬目錄
        stock_dir = os.path.join(self.output_dir, stock_id)
        os.makedirs(stock_dir, exist_ok=True)
        
        all_data = []
        current_date = datetime.now()
        start_date = current_date - relativedelta(years=years)
        
        # 月度遍歷
        iter_date = start_date
        while iter_date <= current_date:
            date_query = iter_date.strftime("%Y%m") + "01"
            print(f"  📅 抓取 {iter_date.strftime('%Y/%m')}...")
            
            month_data = self.fetch_month_data(stock_id, date_query)
            if month_data:
                all_data.extend(month_data)
                print(f"    ✅ 取得 {len(month_data)} 筆資料")
            
            # 強制延遲 (重要！)
            sleep_time = random.uniform(5, 8)
            print(f"    ☕ 休息 {sleep_time:.1f} 秒...")
            time.sleep(sleep_time)
            
            iter_date += relativedelta(months=1)
            
        if all_data:
            df = pd.DataFrame(all_data)
            df['ts'] = pd.to_datetime(df['ts'])
            df = df.sort_values('ts').drop_duplicates('ts')
            
            # 按年度存檔
            years = df['ts'].dt.year.unique()
            for year in years:
                df_year = df[df['ts'].dt.year == year]
                year_file = os.path.join(stock_dir, f"{year}.csv")
                df_year.to_csv(year_file, index=False)
                print(f"    💾 已儲存: {year_file}")
                
            print(f"\n✨ 下載完成！資料已按年度存於: {stock_dir}")
            print(f"📊 總計資料筆數: {len(df)}")
            return df
        else:
            print("❌ 未能取得任何資料。")
            return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='TWSE 歷史資料下載器')
    parser.add_argument('stock_id', type=str, help='股票代碼 (例如: 2330)')
    parser.add_argument('--years', type=int, default=10, help='抓取年數 (預設: 10)')
    
    args = parser.parse_args()
    
    downloader = TWSEDownloader()
    downloader.download_history(args.stock_id, years=args.years)
