# 趨勢判斷資料規格書 (Trend Identification Data)

## 1. 資料庫變動
**本功能目前不需要修改資料庫 Schema。**
趨勢判斷為即時運算 (On-the-fly calculation)，基於既有的 K 線資料 (`stock_kbar`) 進行分析。

## 2. 暫存資料結構 (In-Memory)
系統執行時會使用以下結構暫存運算結果：

### 2.1 TrendContext
用於在遍歷 K 線時追蹤趨勢狀態的上下文物件。
- `current_trend`: 當前趨勢 (TrendType)
- `turning_points`: 歷史轉折點列表 (List[TurningPoint])
- `pending_signal`: 等待確認的反轉訊號 (Optional)

## 3. 輸出格式
若需將結果輸出為 CSV 或報表，建議格式如下：
- `StockID`: 股票代碼
- `Date`: 分析日期
- `Trend`: 趨勢 (UP/DOWN/CONSOLIDATION)
- `LastHigh`: 最近高點
- `LastLow`: 最近低點
