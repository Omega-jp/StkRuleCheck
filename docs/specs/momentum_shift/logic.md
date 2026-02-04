# Momentum Shift 系統邏輯規格書

## 1. 概述
動能轉移（Momentum Shift）系統旨在透過偵測 K 線之間的「不效率（Inefficiency）」空隙，辨識市場動能的轉向。系統產生的「中心價格（Center Price）」將作為動態支撐或壓力位，並用於產生買進訊號。

## 2. 不效率識別模型

### A. 三根 K 線模型 (Fair Value Gap, FVG)
*   **看漲不效率 (Bullish)**：當前 K 線 (Candle 3) 的最低價 > 兩根前的 K 線 (Candle 1) 的最高價。
*   **看跌不效率 (Bearish)**：當前 K 線 (Candle 3) 的最高價 < 兩根前的 K 線 (Candle 1) 的最低價。

### B. 群組不效率模型 (Group FVG - GFVG)
*   **概念**：這是 FVG 的擴充版，不侷限於固定 3 根 K 線，而是動態向回掃描尋找最近的未填補空隙。
*   **識別邏輯**：
    1.  **看跌 GFVG (Bearish)**：
        *   **掃描對象**：當前收盤 K 線 (Candle N) 的高點 (`High[N]`)。
        *   **對比目標**：往前回溯 (`k < N`)，尋找**最近**的一根 K 線 (Boundary Candle)，其低點 (`Low[k]`) **大於** 當前 K 線的高點 (`High[N]`)。
        *   **空隙與邊界**：
            *   **上邊界**：邊界 K 線的低點 (`Low[k]`)。
            *   **下邊界**：當前 K 線的高點 (`High[N]`)。
        *   **條件**：`Low[k] > High[N]` (即存在空隙)。

    2.  **看漲 GFVG (Bullish)**：
        *   **掃描對象**：當前收盤 K 線 (Candle N) 的低點 (`Low[N]`)。
        *   **對比目標**：往前回溯 (`k < N`)，尋找**最近**的一根 K 線 (Boundary Candle)，其高點 (`High[k]`) **小於** 當前 K 線的低點 (`Low[N]`)。
        *   **空隙與邊界**：
            *   **上邊界**：當前 K 線的低點 (`Low[N]`)。
            *   **下邊界**：邊界 K 線的高點 (`High[k]`)。
        *   **條件**：`Low[N] > High[k]` (即存在空隙)。

*   **掃描限制**：為了效能與實用性，通常限制回溯範圍（例如最近 20 根），若找不到則視為無新 GFVG。
*   **優先權**：若同時存在標準 FVG (3根) 與 GFVG，由於 GFVG 的定義其實包含了標準 FVG (標準 FVG 是 回溯 k=N-2 的情況)，此邏輯是通用的。系統將統一使用此 GFVG 邏輯進行全域搜尋。

## 3. 中心價格 (Center Price) 計算

當偵測到不效率空隙時，計算該空隙的中心點作為 Momentum Shift 價格：

1.  **鎖定邊界**：
    *   **看漲**：
        *   上邊界 = 當前 K 線 (Candle 3) 的最低價 (`Low[3]`)。
        *   下邊界 = 先前相關 K 線 (Candle 1) 的最高價 (`High[1]`)。
    *   **看跌**：
        *   上邊界 = 先前相關 K 線 (Candle 1) 的最低價 (`Low[1]`)。
        *   下邊界 = 當前 K 線 (Candle 3) 的最高價 (`High[3]`)。
2.  **公式**：
    `Center Price = (上邊界 + 下邊界) / 2`

## 4. 動能轉移狀態與軌跡 (State Transitions & Staircase)

系統透過狀態機管理動能方向：

### A. 狀態更新觸發
*   **從 Bearish 轉 Bullish**：
    1.  **結構轉向**：偵測到新的「看漲不效率空隙」（Bullish FVG 或 Group Inefficiency）。此時中心價格更新為綠線。
    2.  **買進確認**：價格收盤突破 (Cross Up) 當前的紅線中心價格。
*   **從 Bullish 轉 Bearish**：偵測到新的「看跌不效率空隙」。中心價格更新為紅線。

### B. 軌跡維持 (Staircase Model)
*   系統僅維持「一條」當前的 `Momentum Shift Level`。
*   新的空隙一旦出現，不論類型，立即取代舊有的線。
*   **階梯式更新**：不考慮空隙填補（Gap Fill），只追蹤最新的動能結構。

## 5. 交易訊號 (Trading Signals)

### A. 買進訊號 (Buy Signal)
*   **觸發條件**：當前狀態為 **紅線 (Bearish)** 時，K 線收盤價 **由下往上突破 (Cross Up)** 該紅線。
*   **意義**：看跌動能發生反轉，新買力介入。

### B. 賣出訊號 (Sell Signal)
*   **觸發條件**：當前狀態為 **綠線 (Bullish)** 時，K 線收盤價 **由上往下穿破 (Cross Down)** 該綠線。
*   **意義**：看漲動能消失，支撐轉向。
*   **核心定義**：`Current_Level_Type == "Bullish"` 且 `Close[i] < Current_MS_Level`。
