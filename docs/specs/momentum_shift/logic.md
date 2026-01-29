# Momentum Shift 系統邏輯規格書

## 1. 概述
動能轉移（Momentum Shift）系統旨在透過偵測 K 線之間的「不效率（Inefficiency）」空隙，辨識市場動能的轉向。系統產生的「中心價格（Center Price）」將作為動態支撐或壓力位，並用於產生買進訊號。

## 2. 不效率識別模型

### A. 三根 K 線模型 (Fair Value Gap, FVG)
*   **看漲不效率 (Bullish)**：當前 K 線 (Candle 3) 的最低價 > 兩根前的 K 線 (Candle 1) 的最高價。
*   **看跌不效率 (Bearish)**：當前 K 線 (Candle 3) 的最高價 < 兩根前的 K 線 (Candle 1) 的最低價。

### B. 群組不效率模型 (Group Inefficiency Model)
*   **定義**：系統追蹤當前 K 線與「最近一個波段高點或低點（Swing Point）」之間是否存在影線未觸及的空隙。
*   **邏輯**：
    *   **看漲**：`當前 Low > 最近一個波段高點 (Recent Swing High)`。
    *   **看跌**：`當前 High < 最近一個波段低點 (Recent Swing Low)`。
*   **波段點定義**：採用專案中已實作的 `turning_point_identification.py` 邏輯（基於 MA5 區間極值）或 N 根 K 線分形（Fractal）高低點。

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
