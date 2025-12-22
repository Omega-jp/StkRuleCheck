# 買入規則規格書 (src/buyRule)

本文件彙整主程式支援的所有買入規則。每節包含規則概念、依賴欄位，以及輸出欄位或函式。若需了解數據收集與流程框架，請參考 `DESIGN_SPEC.md`。

## 1. breakthrough_san_yang_kai_tai (三陽開泰)
- **概念**：連續三根紅 K，且每根收盤價高於前一根的高點。
- **輸入**：日線 OHLCV。
- **輸出欄位**：`san_yang_kai_tai_buy_check` (命中為 `O`)。
- **附註**：可擴充成交量條件，確保量能同步放大。

## 2. breakthrough_four_seas_dragon (四海游龍)
- **概念**：5/10/20/60 MA 呈現多頭排列，且收盤價突破所有均線平台。
- **輸入**：日線資料需包含 `[5,10,20,60]` MA 欄位。
- **輸出欄位**：`four_seas_dragon_buy_check`。
- **使用方式**：呼叫時傳入 MA 組合及 `stock_id`（參考 `summarize_buy_rules.py`）。

## 3. macd_golden_cross_above_zero
- **概念**：MACD 線在 0 軸之上黃金交叉 Signal 線。
- **輸入**：MACD、Signal、Histogram。
- **輸出欄位**：`macd_golden_cross_above_zero_buy_check`。

## 4. macd_golden_cross_above_zero_positive_histogram
- **概念**：在 (3) 條件外，Histogram 需為正，以確認動能。
- **輸出欄位**：`macd_golden_cross_above_zero_positive_histogram_buy_check`。

## 5. diamond_cross (鑽石劍)
- **概念**：以 `ma20` 上穿 `ma60` 的黃金交叉為前提，突破黃金交叉前最近的轉折高點收盤即觸發。
- **輸入**：日線 OHLCV；均線 `ma20`、`ma60`（缺則會用 `Close` rolling 計算）；轉折點 `turning_points_df`（缺則程式內會自行呼叫 `identify_turning_points`）。
- **邏輯**：
  1) 找出所有 `ma20` 由下往上穿越 `ma60` 的日期（黃金交叉）。
  2) 針對每個黃金交叉，回看最多 60 根 K，取黃金交叉前最近一個 `turning_high_point` 當作前波高點。
  3) 在黃金交叉後的日子，若收盤價第一次向上突破該前波高點（前一日收盤 ≤ 該高點、當日收盤 > 該高點），標記為 `O`。
- **輸出欄位**：`diamond_cross_buy_check`。
- **pipeline**：`validate_buy_rule` 會先跑轉折點，並把結果傳給 `check_diamond_cross`（若沒傳入則函式內會自行計算）。

## 6. breakthrough_resistance_line (壓力線突破)
- **概念**：由轉折高點推算水平壓力帶，當收盤價有效突破該水準觸發買訊。
- **輸入**：日線 OHLCV、`turning_points_df`。
- **輸出欄位**：`resistance_line_breakthrough_check`，以及人可讀的阻力價、來源日期。

## 7. breakthrough_descending_trendline (下降趨勢線突破)
- **概念**：以轉折點/波段點建立下降趨勢線，確認斜率壓力被收盤價擊穿。
- **輸入**：日線資料、`turning_points_df`、`wave_points_df`。
- **輸出欄位**：`descending_trendline_breakthrough_check` 與突破幅度、線段端點資料。
- **詳細流程**：見 `DESIGN_SPEC.md` 第 4 章。

## 8. impulse_macd_buy_rule (Impulse MACD 買入)
- **函式**：
  - `check_impulse_macd_zero_cross_buy`
  - `check_impulse_macd_signal_cross_buy`
  - `check_impulse_macd_combined_buy`
- **概念**：使用衝量 MACD 指標偵測零軸穿越、訊號交叉與綜合條件。
- **輸入**：`ImpulseMACD`, `ImpulseSignal`, `ImpulseHistogram`。
- **輸出欄位**：`impulse_macd_zero_cross_buy`, `impulse_macd_signal_cross_buy`, `impulse_macd_buy`。
- **選項**：可於綜合檢查指定 `require_positive_histo=True`。

## 9. td_sequential_buy_rule (TD 九轉)
- **函式**：`compute_td_sequential_signals`、`check_td_sequential_buy_rule`。
- **概念**：根據 `comparison_offset` 與 `setup_length` 計算連續 setup，當買/賣 setup 命中目標值 (預設 9) 即產生 `O`。
- **輸出欄位**：
  - `td_setup_buy_count`, `td_buy_signal`, `td_setup_sell_count`, `td_sell_signal`
  - Wrapper 版本：`td_sequential_buy_check`, `td_setup_buy_count`, `td_sequential_sell_check`, `td_setup_sell_count`。
- **輸入要求**：需具備 `Close` 欄位即可；適合用於 `append_indicator` 之後的資料。

## 10. 其他
- 如新增買入規則，請於此文件登錄概念、必要欄位與輸出欄位，並同步於 `summarize_buy_rules.py` 內映射顯示名稱。
