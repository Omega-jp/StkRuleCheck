import os
import shioaji as sj
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

def test_fetch_limit(stock_id="0050", days=1000):
    api = sj.Shioaji(simulation=True)
    userdata = {
        'APIKey': os.getenv('SHIOAJI_API_KEY'),
        'SecretKey': os.getenv('SHIOAJI_SECRET_KEY')
    }
    
    try:
        api.login(api_key=userdata['APIKey'], secret_key=userdata['SecretKey'])
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        print(f"嘗試抓取 {stock_id} 從 {start_date.date()} 到 {end_date.date()} 的資料 (約 {days} 天)")
        
        contract = api.Contracts.Stocks[stock_id]
        kbars = api.kbars(contract, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
        
        df = pd.DataFrame({**kbars})
        if not df.empty:
            df.ts = pd.to_datetime(df.ts)
            print(f"成功抓取！資料範圍: {df.ts.min()} 至 {df.ts.max()}")
            print(f"總共 {len(df)} 筆 K 線 (以 1 分 K 為基礎的話會很多，若是日 K 就還好)")
            # 判斷回傳的是什麼格式
            # sj.kbars 預設通常是 1 分 K。
        else:
            print("抓取成功但資料是空的。")
        
        api.logout()
    except Exception as e:
        print(f"抓取失敗: {e}")

if __name__ == "__main__":
    test_fetch_limit()
