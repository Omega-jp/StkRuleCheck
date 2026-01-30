# Momentum Shift 勝率分析介面規格 (api.md)

## 1. 輸入參數 (Input)

回測引擎應接受以下參數：

| 參數名 | 類型 | 說明 | 來源 |
| :--- | :--- | :--- | :--- |
| `stock_id` | `str` | 股票代碼 | `"2330"` |
| `data` | `pd.DataFrame` | 10年歷史資料 | `Data/backtest_data/` (TWSE) |
| `initial_capital` | `float` | 初始虛擬庫存單位 | `1.0` |

## 2. 內部資料結構 (State Tracker)

回測過程中需維護一個 `Trade` 物件或字典，記錄當前交易狀態：

```python
{
    "entry_date": "2024-01-01",
    "entry_price": 500.0,
    "status": "INITIAL",      # "INITIAL" | "TRENDING"
    "units": 1.0,             # 當前持股數量 (1.0 -> 0.5 -> 0.0)
    "sell_half_date": None,
    "sell_half_price": None,
    "exit_date": None,
    "exit_price": None,
    "total_profit": 0.0       # 累計收益
}
```

## 3. 輸出結果規格 (Output)

### 3.1 交易明細表 (Trade Logs)
回傳一個列表，每筆完成的交易包含：
- `StockID`: 股票代號
- `EntryDate`: 進場日期
- `ExitDate`: 清倉日期
- `BuyPrice`: 平均進場價
- `SellPrice`: 加權平均出場價
- `ProfitPct`: 收益百分比 (e.g. 0.05 代表 5%)
- `Result`: "Win" 或 "Loss"

### 3.2 彙總統計 (Summary)
- `TotalTrades`: 總交易次數
- `Wins`: 獲利次數
- `Losses`: 虧損次數
- `WinRate`: 勝率 (Wins / TotalTrades)
- `AverageProfit`: 獲利時的平均報酬
- `AverageLoss`: 虧損時的平均報酬
- `TotalReturn`: 累計複利報酬率
