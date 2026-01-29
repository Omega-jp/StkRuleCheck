# Momentum Shift API 規格書

## 1. 介面定義

### 函數名稱：`detect_momentum_shift`

### 輸入參數 (Input)
*   `df` (pandas.DataFrame): 包含以下欄位的 K 線資料：
    *   `datetime` (Datetime): 時間戳記。
    *   `open`, `high`, `low`, `close` (Float): OHLC 價格資訊。
*   `parameters` (Dict):
    *   `mode` (String): `"3-candle"` 或 `"group"`（預設 `"3-candle"`）。
    *   `lookback_period` (Int): 當 `mode="group"` 時的起始掃描範圍（預設為無限，或設為特定大數值）。

### 輸出結果 (Output)
*   `df` (pandas.DataFrame): 新增以下欄位的資料表：
    *   `momentum_shift_level` (Float): 當前的中心價格水平。
    *   `shift_type` (Enum): `"Bullish"`, `"Bearish"`, 或 `None`。
    *   `ms_buy_signal` (Boolean): 當日是否觸發買進訊號。

## 2. 錯誤處理
*   若 K 線資料少於三根，返回空值或錯誤。
*   輸入資料含有 NaN 時，應先進行填充或報錯。
