# Momentum Shift 勝率分析資料持久化規格 (data.md)

## 1. 輸出檔案路徑

回測結果應存放於 `output/analysis/` 目錄下：

| 檔案類型 | 檔案路徑 |
| :--- | :--- |
| **長期歷史資料** | `Data/backtest_data/{stock_id}/{year}.csv` |
| **交易明細** | `output/analysis/momentum_shift_trades.csv` |
| **匯總統計** | `output/analysis/momentum_shift_summary.csv` |

## 2. 長期歷史資料格式 (TWSE Raw to Clean)

由 `twse_downloader.py` 產出，欄位對應如下：
- `ts`: 日期 (YYYY-MM-DD, 民國轉西元)
- `Open`: 開盤價
- `High`: 最高價
- `Low`: 最低價
- `Close`: 收盤價
- `Volume`: 成交量 (單位：股)

## 2. 欄位定義

### 2.1 `momentum_shift_trades.csv` (交易明細)
- `stock_id`: 股票代碼 (e.g., 2330)
- `entry_date`: 進場日 (T+1 開盤)
- `entry_price`: 進場價格 (T+1 Open)
- `standing_on_ma5_date`: 進入 TRENDING 階段的日期 (可選)
- `sell_half_date`: 賣出一半的日期
- `sell_half_price`: 賣出一半的價格 (T_half+1 Open)
- `exit_date`: 全數清倉日期
- `exit_price`: 全數清倉價格 (T_full+1 Open)
- `profit_percent`: 該筆交易總報酬率
- `win_loss`: 勝/負 (Win/Loss)

### 2.2 `momentum_shift_summary.csv` (彙總統計)
- `stock_id`: 股票代碼
- `test_period`: 回測時間範圍 (e.g., "2023-01-01 to 2024-01-30")
- `total_trades`: 交易總次數
- `win_rate`: 總勝率
- `avg_profit`: 平均獲利率 (勝場)
- `avg_loss`: 平均虧損率 (負場)
- `max_profit`: 單筆最高獲利
- `max_loss`: 單筆最高虧損
- `total_return`: 累計複利報酬率
