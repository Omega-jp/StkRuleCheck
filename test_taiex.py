import shioaji as sj
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

api = sj.Shioaji(simulation=True)
api.login(
    api_key=os.getenv('SHIOAJI_API_KEY'),
    secret_key=os.getenv('SHIOAJI_SECRET_KEY')
)

try:
    # Try different codes for TAIEX
    target_codes = ["001", "TSE001", "IX0001"] 
    # Valid TAIEX code in Shioi is likely '001' in Stocks or 'TSE001' in Indices? 
    # Actually for Stocks it is usually just '001' (Fact: 001 is rarely used as stock, TAIEX is usually an Index)
    # Let's try to search for it or just try "001" which is often mapped to TAIEX in Taiwan systems, 
    # but Shioaji might separate Stocks and Indices.
    
    # Try to find TAIEX in Contracts
    # In Shioaji, indices are often under api.Contracts.Indexs
    print("Checking Indices...")
    for name in dir(api.Contracts.Indexs):
        if "TSE" in name:
            print(f"Found Index Category: {name}")
            
    # Try to fetch kbar for 001 (if it exists as a stock, unlikely) or as Index
    # Often TAIEX is 'TSE001' or '001' in Indices.
    
    # Let's try to get '001' from Stocks first just in case
    try:
        contract = api.Contracts.Stocks['001']
        print(f"Found Stock 001: {contract}")
    except:
        print("Stock 001 not found")

    try:
        # TAIEX is typically 'TSE:001' or similar. 
        # Shioaji documentation says Indicies are in `api.Contracts.Indexs`
        # Let's look for TAIEX
        taiex = None
        for category in api.Contracts.Indexs:
            # category is likely 'TSE', 'OTC'
            for contract in category:
                 if contract.code == '001':
                     taiex = contract
                     print(f"Found Index 001: {contract}")
                     break
            if taiex: break
            
        if taiex:
            print("Fetching Kbar for TAIEX...")
            kbars = api.kbars(taiex, 
                              start=datetime.now().strftime('%Y-%m-%d'), 
                              end=datetime.now().strftime('%Y-%m-%d'))
            print(f"Kbars: {len(kbars.ts) if kbars and hasattr(kbars, 'ts') else 'None'}")
    except Exception as e:
        print(f"Index fetch failed: {e}")

except Exception as e:
    print(f"General Error: {e}")

api.logout()
