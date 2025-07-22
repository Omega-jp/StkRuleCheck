# 股票技術分析系統設計規格

## 1. 系統概述
本系統旨在提供股票技術分析功能，包括數據收集、技術指標計算和買賣規則驗證。

## 2. 數據初始化模塊 (data_initial)

### 2.1 數據下載和收集
#### 2.1.1 K線數據下載器 (kbar_downloader.py)
- 功能：從券商API獲取股票K線數據
- 主要組件：
  - `get_stock_kbars()`：下載指定股票的K線數據
  - `process_kbars()`：處理並生成日K線和週K線數據
  - `save_kbars()`：保存K線數據到CSV文件

#### 2.1.2 K線數據收集器 (kbar_collector.py)
- 功能：批量收集多支股票的K線數據
- 主要組件：
  - `collect_and_save_kbars()`：根據配置文件收集並保存K線數據

### 2.2 技術指標計算
#### 2.2.1 移動平均線計算 (calculate_ma.py)
- 功能：計算多個週期的移動平均線
- 支持週期：5、10、20、60、120日
- 主要組件：
  - `calculate_ma()`：計算指定週期的移動平均線

#### 2.2.2 KD指標計算 (calculate_kd.py)
- 功能：計算KD隨機指標
- 主要組件：
  - `calculate_kd()`：計算RSV、%K和%D值
- 參數設置：
  - n：計算RSV的週期（默認9日）
  - m1：計算%K的週期（默認3日）
  - m2：計算%D的週期（默認3日）

#### 2.2.3 MACD指標計算 (calculate_macd.py)
- 功能：計算MACD指標
- 主要組件：
  - `calculate_macd()`：計算MACD相關指標
- 參數設置：
  - 短期EMA週期：12日
  - 長期EMA週期：26日
  - 信號線週期：9日

### 2.3 指標整合 (append_indicator.py)
- 功能：將各種技術指標添加到K線數據中
- 主要組件：
  - `append_indicators_to_csv()`：讀取CSV文件並添加技術指標
- 處理流程：
  1. 讀取原始K線數據
  2. 計算並添加KD指標
  3. 計算並添加MACD指標
  4. 計算並添加移動平均線
  5. 保存完整的分析數據

### 2.4 數據格式規範
#### 2.4.1 輸入數據格式
- CSV文件格式
- 必要欄位：
  - ts：時間戳（作為索引）
  - Open：開盤價
  - High：最高價
  - Low：最低價
  - Close：收盤價
  - Volume：成交量

#### 2.4.2 輸出數據格式
- CSV文件格式
- 包含原始數據和技術指標：
  - 原始OHLCV數據
  - KD指標（RSV、%K、%D）
  - MACD指標（MACD、Signal、Histogram）
  - 移動平均線（MA5、MA10、MA20、MA60、MA120）

## 3. 買賣規則驗證模塊 (validate_buy_rule.py)

### 3.1 功能概述
此模塊用於驗證和可視化基於特定技術指標的買賣規則。它會載入單一股票的歷史數據，根據預設規則（例如移動平均線交叉）生成買賣信號，並將結果繪製成K線圖，最後保存圖表和規則結果。

### 3.2 主要組件

#### 3.2.1 數據載入 (load_stock_data)
- **功能**：從 `Data/kbar/` 目錄載入指定股票的日K線數據 (CSV 格式)。
- **處理**：
  - 將中文欄位名稱（開盤價, 最高價, 最低價, 收盤價, 成交量）轉換為 `mplfinance` 兼容的英文名稱（Open, High, Low, Close, Volume）。
  - 將 `ts` 欄位作為時間索引。

#### 3.2.2 K線圖繪製 (plot_candlestick_chart)
- **功能**：使用 `mplfinance` 庫繪製包含買賣信號的K線圖。
- **特性**：
  - 顯示最近180天的數據。
  - K線圖樣式：上漲為紅色，下跌為綠色。
  - **附加圖表 (Addplot)**：
    - 將 `ma5`, `ma10`, `ma20` 移動平均線繪製為線圖。
    - 將買入信號（`buy_signals`）標記為向上的紅色箭頭 (`^`)。
    - 將賣出信號（`sell_signals`）標記為向下的藍色箭頭 (`v`)。
  - **成交量**：在下方繪製成交量圖。
  - **輸出**：將生成的圖表保存為 PNG 圖片到 `output/chart/` 目錄。

#### 3.2.3 股票列表讀取 (get_stock_list)
- **功能**：從 `config/stklist.cfg` 配置文件中讀取要進行驗證的股票代碼列表。

#### 3.2.4 買入規則驗證 (validate_buy_rule)
- **功能**：模塊的核心協調函數。
- **處理流程**：
  1. 載入指定股票的數據。
  2. 計算買賣信號（目前實現為5日均線和10日均線的交叉策略）。
  3. 調用 `plot_candlestick_chart` 繪製並保存結果圖表。
  4. 調用 `src.buyRule.breakthrough_ma.combine_buy_rules` 生成詳細的規則結果。
  5. 將規則結果保存為 CSV 文件到 `output/breakthrought_ma/` 目錄。

### 3.3 執行入口
- 當作為主程序執行時 (`if __name__ == "__main__"`)：
  1. 讀取股票列表。
  2. 遍歷列表中的每個股票代碼。
  3. 對每支股票執行 `validate_buy_rule` 函數。