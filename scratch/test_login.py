import os
import shioaji as sj
from dotenv import load_dotenv

load_dotenv()

api = sj.Shioaji(simulation=True)
try:
    api.login(
        api_key=os.getenv('SHIOAJI_API_KEY'),
        secret_key=os.getenv('SHIOAJI_SECRET_KEY')
    )
    print("Login success")
    print(api.list_accounts())
except Exception as e:
    print(f"Login failed: {e}")
finally:
    api.logout()
