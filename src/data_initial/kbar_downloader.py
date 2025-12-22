import shioaji as sj 
import os
import pandas as pd
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

def get_stock_kbars(stock_id, start_date=None, end_date=None, max_retries=3, retry_delay=5):
    """獲取指定股票的K線數據
    
    Args:
        stock_id (str): 股票代碼
        start_date (datetime, optional): 起始日期。如果未指定，默認為當前日期往前540天
        end_date (datetime, optional): 結束日期。如果未指定，默認為當前日期
        max_retries (int): 最大重試次數
        retry_delay (int): 重試延遲秒數
    """
    for attempt in range(max_retries):
        try:
            api = sj.Shioaji(simulation=True)
            
            userdata = {
                'APIKey': os.getenv('SHIOAJI_API_KEY'),
                'SecretKey': os.getenv('SHIOAJI_SECRET_KEY')
            }
            
            if not userdata['APIKey'] or not userdata['SecretKey']:
                raise ValueError("API金鑰未設置，請檢查.env文件")
            
            api.login(
                api_key=str(userdata["APIKey"]),
                secret_key=str(userdata['SecretKey'])
            )
            
            # 設置日期範圍
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                start_date = end_date - timedelta(days=540)
            
            contract = api.Contracts.Stocks[stock_id]
            kbars = api.kbars(contract, 
                             start=start_date.strftime('%Y-%m-%d'),
                             end=end_date.strftime('%Y-%m-%d'))
            
            df = pd.DataFrame({**kbars})
            df.ts = pd.to_datetime(df.ts)
            df.set_index('ts', inplace=True)
            
            api.logout()
            return df
            
        except Exception as e:
            print(f"第{attempt + 1}次嘗試失敗：{str(e)}")
            if attempt < max_retries - 1:
                print(f"等待{retry_delay}秒後重試...")
                time.sleep(retry_delay)
            else:
                print("已達到最大重試次數，無法獲取數據")
                return None

def process_kbars(df):
    """處理K線數據，生成日K線和週K線

    修改重點：
    - 由於非交易日沒有日K資料，因此以日K資料的 ISO 年及週數作分組，
      並以每組中最小的日期作為該週的第一個交易日（即週K的時間戳）。
    - 週K的各項數據計算：
        Open 取該週第一個交易日的開盤價，
        Close 取該週最後一個交易日的收盤價，
        High/Low 為該週所有交易日中的最大/最小值，
        Volume 為該週成交量的總和。
    """
    if df is None or df.empty:
        return None, None

    if not isinstance(df.index, (pd.DatetimeIndex, pd.PeriodIndex, pd.TimedeltaIndex)):
        try:
            df = df.copy()
            df.index = pd.to_datetime(df.index, errors='coerce')
        except Exception:
            return None, None
    
    # 生成日K線：由於部分日期無交易資料，會產生缺失
    # 生成日K線：由於部分日期無交易資料，會產生缺失
    # 首先，使用現有的重採樣邏輯計算 High, Low, Close, Volume
    daily_k = df.resample('D').agg({
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    })

    # 根據成交量 > 0 的第一筆數據計算開盤價
    def get_first_open_with_volume(group):
        # 過濾成交量大於 0 的數據
        entries_with_volume = group[group['Volume'] > 0]
        if not entries_with_volume.empty:
            # 返回第一筆有成交量數據的開盤價
            return entries_with_volume['Open'].iloc[0]
        else:
            # 如果當天沒有任何成交量數據，則開盤價為 NaN
            return pd.NA

    daily_open_prices = df.groupby(df.index.date).apply(get_first_open_with_volume)
    daily_open_prices.index = pd.to_datetime(daily_open_prices.index) # 將日期索引轉換回 datetime

    # 將計算出的開盤價賦值給 daily_k DataFrame
    daily_k['Open'] = daily_open_prices

    daily_k = daily_k.dropna() # 刪除任何聚合值為 NaN 的行（例如，如果某天沒有數據，或開盤價沒有成交量）
    
    # 使用 ISO 年與週數分組，確保以實際有交易的日子來分組
    weekly_k = pd.DataFrame()
    groups = daily_k.groupby([daily_k.index.isocalendar().year, daily_k.index.isocalendar().week])
    
    for (year, week), group in groups:
        # 取該週實際的第一個與最後一個交易日
        first_trade_date = group.index.min()
        last_trade_date = group.index.max()
        
        weekly_k.loc[first_trade_date, 'Open'] = group.loc[first_trade_date, 'Open']       # 週首交易日的開盤價
        weekly_k.loc[first_trade_date, 'High'] = group['High'].max()                       # 該週最高價
        weekly_k.loc[first_trade_date, 'Low'] = group['Low'].min()                         # 該週最低價
        weekly_k.loc[first_trade_date, 'Close'] = group.loc[last_trade_date, 'Close']        # 週末交易日的收盤價
        weekly_k.loc[first_trade_date, 'Volume'] = group['Volume'].sum()                     # 該週成交量總和

    weekly_k = weekly_k.dropna()
    
    # 確保使用實際的交易日期，且不包含未來日期
    current_date = pd.Timestamp.now()
    weekly_k = weekly_k[weekly_k.index <= current_date]
    
    # 移除可能的重複索引
    weekly_k = weekly_k[~weekly_k.index.duplicated(keep='first')]

    # 重新排序 daily_k 的列為 OHLCV
    daily_k = daily_k[['Open', 'High', 'Low', 'Close', 'Volume']]
    
    return daily_k, weekly_k

def save_kbars(stock_id):
    """主函數：獲取並保存K線數據"""
    # 創建 Data 目錄（如果不存在）
    data_dir = os.path.join(os.path.dirname(__file__), '../Data')
    os.makedirs(data_dir, exist_ok=True)
    
    # 獲取K線數據
    df = get_stock_kbars(stock_id)
    if df is not None:
        # 處理數據
        daily_k, weekly_k = process_kbars(df)
        
        # 設定索引名稱為 'ts'，以確保 CSV 中包含正確的 Header
        if daily_k is not None:
            daily_k.index.name = 'ts'
            daily_file = os.path.join(data_dir, f"{stock_id}_D.csv")
            daily_k.to_csv(daily_file)
            print(f"日K線數據已保存到：{daily_file}")
        
        if weekly_k is not None:
            weekly_k.index.name = 'ts'
            weekly_file = os.path.join(data_dir, f"{stock_id}_W.csv")
            weekly_k.to_csv(weekly_file)
            print(f"週K線數據已保存到：{weekly_file}")
    else:
        print(f"無法獲取股票 {stock_id} 的K線數據")

if __name__ == "__main__":
    # 在這裡指定要下載的股票代碼
    stock_id: str = "0050"
    save_kbars(stock_id)


