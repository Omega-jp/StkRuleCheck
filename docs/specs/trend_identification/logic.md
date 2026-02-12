# 趨勢判斷邏輯規格書 (Trend Identification Logic)

## 1. 目的
本文件定義如何利用「轉折點 (Turning Points)」與「波段 (Waves)」來判斷股票的趨勢狀態（漲勢、跌勢、盤整）。
核心邏輯基於道氏理論 (Dow Theory) 的市場結構分析。

## 2. 核心定義

### 2.1 轉折點 (Turning Points)
- **轉折高點 (High Point, H)**：價格走勢中的局部高點。
- **轉折低點 (Low Point, L)**：價格走勢中的局部低點。
- 轉折點識別演算法詳見 `src/baseRule/turning_point_identification.py`。

### 2.2 趨勢狀態 (Trend Status)
系統將市場分為三種主要狀態：
1. **漲勢 (Uptrend)**
2. **跌勢 (Downtrend)**
3. **盤整 (Consolidation)**

---

## 3. 判斷邏輯

### 3.1 漲勢 (Uptrend) - "N字突破"
- **關鍵序列**：$L_{prev} \rightarrow H_{prev} \rightarrow L_{curr} \rightarrow \text{Breakout}$
- **所需點位** (往前看 3 個轉折點)：
    1. 前波低點 ($L_{prev}$)
    2. 前波高點 ($H_{prev}$)
    3. 最近低點 ($L_{curr}$)
- **判斷條件**：
    1. **底底高**：$L_{curr} > L_{prev}$
    2. **突破確認**：當前價格 (Close) $> H_{prev}$

### 3.2 跌勢 (Downtrend) - "倒N跌破"
- **關鍵序列**：$H_{prev} \rightarrow L_{prev} \rightarrow H_{curr} \rightarrow \text{Breakdown}$
- **所需點位** (往前看 3 個轉折點)：
    1. 前波高點 ($H_{prev}$)
    2. 前波低點 ($L_{prev}$)
    3. 最近高點 ($H_{curr}$)
- **判斷條件**：
    1. **頭頭低**：$H_{curr} < H_{prev}$
    2. **跌破確認**：當前價格 (Close) $< L_{prev}$

### 3.3 盤整 (Consolidation)
- **定義**：任何不符合上述明確漲勢或跌勢的狀態。
- **常見型態**：
    - **擴張 (Expanding)**：$H_{new} > H_{prev}$ 但 $L_{new} < L_{prev}$ (喇叭口)。
    - **收斂 (Contracting)**：$H_{new} < H_{prev}$ 但 $L_{new} > L_{prev}$ (三角收斂)。
    - **箱型 (Box)**：價格在 $H_{box}$ 與 $L_{box}$ 區間內震盪。

### 3.4 趨勢反轉 (Trend Reversal)
- **由跌轉漲**：
    - 原始狀態：跌勢 (Lower Highs + Lower Lows)。
    - 警示信號：出現 Higher Low (底底高)。
    - 確認信號：隨後突破前高 (Higher High)，完成趨勢反轉。
- **由漲轉跌**：
    - 原始狀態：漲勢 (Higher Highs + Higher Lows)。
    - 警示信號：出現 Lower High (頭頭低)。
    - 確認信號：隨後跌破前低 (Lower Low)，完成趨勢反轉。

---

## 4. 異常處理
- **轉折點不足**：若歷史資料不足以形成至少兩個高點與兩個低點，則狀態為 `UNKNOWN` 或 `INSUFFICIENT_DATA`。
- **假突破 (False Breakout)**：系統應具備過濾機制（如收盤價確認或百分比過濾），但在本階段先採用「收盤價突破/跌破」作為單純判斷標準。
