# Momentum Shift 資料結構與狀態規格書

## 1. 內部資料模型

為了追蹤動能轉移，系統需維護一個狀態機，包含以下狀態：

### A. 當前動能狀態 (Current State)
*   `active_level`: `Float` - 目前最新的中心價格。
*   `active_type`: `Enum["Bullish", "Bearish"]` - 目前是看漲還是看跌狀態。
*   `history`: `List[Dict]` - 紀錄歷史出現的所有 Momentum Shift 事件。
    *   `timestamp`: 事件發生時間。
    *   `level`: 當時的中心價格。
    *   `type`: 事件類型。
    *   `boundaries`: `(upper, lower)` 當時計算的邊界。

## 2. 快取與持久化
*   在處理大量 K 線時，應使用向量化運算（pandas `apply` 或 `numba`）來提升效能。
*   不效率空隙一旦偵測到且價格未回測（Revisit/Fill）前，該空隙維持有效。
    *   *註：目前的基礎規則不考慮空隙填補，僅追蹤最新產生的中心價格位移。*

## 3. 視覺化映射
*   **紅線 (Bearish)**：繪製在 `active_level` 當 `active_type == "Bearish"` 時。
*   **綠線 (Bullish)**：繪製在 `active_level` 當 `active_type == "Bullish"` 時。
