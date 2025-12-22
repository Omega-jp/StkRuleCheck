# 底分型「底底高」試單買入規則規格書（n 根分型版）

本文定義新的買入規則，依據最近轉折方向，偵測 n 根分型的「底底高」形態，於分型確立日（右側觀察窗口結束日）給出試單買入信號。僅涵蓋進場條件，不含出場邏輯。

## 名稱
- 模組建議名：`bottom_fractal_higher_low.py`
- 對外函式建議：`check_bottom_fractal_higher_low(df, turning_points_df=None, left=2, right=2, tol=0.0)`
- 規則顯示名稱建議：`底底高分型`

## 依賴與輸入
- 必要欄位：`date`（index 或欄位，可轉換為 datetime）、`Open`、`High`、`Low`、`Close`。
- 轉折點資料：`turning_points_df`，需有 `date`、`turning_high_point`、`turning_low_point`（'O' 或空字串）。若未提供，內部應呼叫現有 `identify_turning_points`。
- 資料頻率：日線。
- 不使用量能、均線、間距等其他過濾。

## 參數
- `left`、`right`：分型左/右窗口長度（天數，含當下日之外的觀察日數），預設 2。分型低點索引 `p` 必須同時滿足左右窗口條件，分型在日 `i = p + right` 確立並輸出信號。
- `tol`：平低容忍度（百分比，小數，預設 0）。比較低點時，`Low[p] >= min_left * (1 - tol/100)` 且 `Low[p] >= min_right * (1 - tol/100)`，`Low[p]` 仍需是窗口內最低（或平最低在容忍度內）。

## 規則邏輯
1) **決定搜尋方向**  
   - 取時間序列上最近的一個轉折點（含當日或之前）。  
   - 若最近為「轉折高點」→ 接下來尋找「底分型」。  
   - 若最近為「轉折低點」→ 本規則不觸發（或可直接輸出空白）。

2) **分型檢測（n 根底分型）**  
   - 對每個候選低點位置 `p`：  
     - 左窗口：`Low[p]` 不高於區間 `[p-left, p-1]` 的最低價（容忍 `tol`）。  
     - 右窗口：`Low[p]` 不高於區間 `[p+1, p+right]` 的最低價（容忍 `tol`）。  
     - 必須有足夠的左/右資料；若資料不足則不判定。  
   - 底分型確立日在 `i = p + right`（因需觀察完整右窗口），信號判斷放在日 `i`。

3) **底底高條件（試單買入）**  
   - 找到底分型低點 `p` 後，往前找到最近的轉折低點 `L`（比 `p` 早，且是最近一個 `turning_low_point == 'O'`）。  
   - 條件：`Low[p] > Low_L * (1 + tol/100)`（預設嚴格大於；若 `tol=0` 則不允許平價）。  
   - 若成立，則在分型確立日 `i = p + right` 標記試單買入信號。

4) **中間 K 根限制**  
   - A（`L`）與分型低點 `p` 之間、中間任何 K 不得低於 `Low_L`，否則視為已破底，該組合失效。  
   - `p` 與 `i` 之間的 K 可存在盤整，無需快速反轉限制。

## 輸出格式（建議）
- 回傳 DataFrame，按日期一列，至少包含：  
  - `date`：字串 `YYYY-MM-DD`。  
  - `bottom_fractal_buy`：'O' 或 ''（分型確立日且符合底底高時為 'O'）。  
  - `fractal_low`：分型低點價格（`Low[p]`）。  
  - `fractal_low_date`：分型低點日期。  
  - `last_turning_low`：最近轉折低點價格（`Low_L`）。  
  - `last_turning_low_date`：最近轉折低點日期。  
  - `crossed_higher_low`：布林，是否滿足 `fractal_low > Low_L * (1 + tol/100)`。
- 未觸發時，`bottom_fractal_buy` 置空，其餘欄位可填 0/空或不填（視現有規則慣例）。

## 邊界與例外
- 資料不足（窗口不滿 `left/right`）時不判定分型。  
- 若缺少轉折低點 `L`，則當期分型不產生試單信號。  
- 若最近轉折點為低點，則跳過（不搜尋底分型）。  
- 如果 `turning_points_df` 日期需對齊 index，需先標準化日期格式並合併或比對時間序列。  
- 不檢查量能、均線、實體比例、上下影線、間距。

## 測試要點
- 正例：序列中最近轉折為高點；之後形成一個底分型，其低點高於前一轉折低點，且右側窗口走完當日產生 'O'。  
- 邊界：正例若右窗口不足，不應提前觸發；若中途 K 破 `Low_L`，應失效。  
- 容忍度：設定 `tol>0` 時，允許分型低點與轉折低點微幅接近但仍高於容忍線。

## 與現有系統整合指引
- 模組路徑：`src/buyRule/bottom_fractal_higher_low.py`；函式名：`check_bottom_fractal_higher_low(df, turning_points_df=None, left=2, right=2, tol=0.0)`。  
- 返回欄位對齊：每日一列，至少 `date`（字串）、`bottom_fractal_buy`（'O'/''）。`summarize_buy_rules.get_latest_result` 會優先抓含 `check`、`_buy`、`signal` 的欄位，`_buy` 結尾即可被辨識。其他輔助欄位可選保留。  
- 顯示名稱：在 `get_rule_display_name` 加入映射 `bottom_fractal_higher_low: 底底高分型`。`get_buy_rules` 會自動掃描檔名並加入流程，無需額外白名單。  
- 轉折點取得：若未傳入 `turning_points_df`，需補齊 `ma5`（若缺以 `Close.rolling(5, min_periods=1)` 計算），再呼叫 `identify_turning_points`，沿用其他 buyRule 模式。  
- 輸出長度與日期格式：結果 DataFrame 長度與輸入 df 對齊，`date` 字串化為 `YYYY-MM-DD`，與既有規則一致，便於匯總 CSV 與圖表疊合。
