import os
import shioaji as sj
from dotenv import load_dotenv

load_dotenv()

def test_login_prod():
    print("Testing login with simulation=False")
    api = sj.Shioaji(simulation=False)
    try:
        api.login(
            api_key=os.getenv('SHIOAJI_API_KEY'),
            secret_key=os.getenv('SHIOAJI_SECRET_KEY')
        )
        print("Login success (Production)")
        accounts = api.list_accounts()
        for acc in accounts:
            print(f"Account ID: {acc.account_id}")
    except Exception as e:
        print(f"Login failed (Production): {e}")
    finally:
        api.logout()

if __name__ == "__main__":
    test_login_prod()
