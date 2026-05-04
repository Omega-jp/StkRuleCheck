import os
import shioaji as sj
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta

load_dotenv()

def test_fetch():
    api = sj.Shioaji(simulation=False)
    try:
        api.login(
            api_key=os.getenv('SHIOAJI_API_KEY'),
            secret_key=os.getenv('SHIOAJI_SECRET_KEY')
        )
        print("Login success")
        
        stock_id = "0050"
        contract = api.Contracts.Stocks[stock_id]
        print(f"Contract: {contract.code}")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=10)
        
        print(f"Fetching kbars for {stock_id} from {start_date} to {end_date}")
        kbars = api.kbars(contract, 
                         start=start_date.strftime('%Y-%m-%d'),
                         end=end_date.strftime('%Y-%m-%d'))
        
        df = pd.DataFrame({**kbars})
        if not df.empty:
            print("Fetch success!")
            print(df.head())
        else:
            print("Fetch returned empty data")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        api.logout()

if __name__ == "__main__":
    test_fetch()
