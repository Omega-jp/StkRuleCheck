# K線繪製規格書

本文件定義了系統中所有自定義 K 線圖表的繪製標準，以確保視覺一致性與正確性。

## 1. 顏色規範 (Color Scheme)

| 元素 | 描述 | 顏色代碼/名稱 | 備註 |
|:--- |:--- |:--- |:--- |
| **上漲 K 棒 (Up Candle)** | 收盤價 >= 開盤價 | `Red` (#FF0000) | 實體可為空心或白色填充，邊框紅色 |
| **下跌 K 棒 (Down Candle)** | 收盤價 < 開盤價 | `Green` (#008000) | 實體填充綠色，邊框綠色 |
| **影線 (Wick/Shadow)** | 最高價至最低價連線 | `Black` (#000000) | 需位於實體下方 (Low Z-order) |
| **背景 (Background)** | 圖表背景區 | `White` (#FFFFFF) | |
| **網格 (Grid)** | 輔助參考線 | `Gray` (#808080) | `alpha=0.3` |

## 2. 圖層順序 (Z-Order)

為避免視覺錯誤（如影線穿過實體），必須嚴格遵守以下 Z-Order 規範：

| 層級 (Z-Order) | 元素類型 | 說明 |
|:---:|:--- |:--- |
| **1** | 影線 (Wicks) | 必須在最底層，避免遮擋實體 |
| **2** | K 棒實體 (Candle Bodies) | 必須蓋過影線，且 `alpha=1.0` (不透明) |
| **5** | 移動平均線 (MA) | 覆蓋於 K 線之上 |
| **7** | 水平壓力/支撐線 | |
| **8** | 趨勢線/斜率線 | |
| **15** | 轉折點標記 (High/Low Points) | 確保不被線條遮擋 |
| **16** | 買賣訊號/突破標記 | 最上層，醒目顯示 |

## 3. 字體與文字 (Fonts & Text)

*   **中文字體支持**：必須優先檢測並使用支持中文的字體（如 `Microsoft JhengHei`, `SimHei`, `Arial Unicode MS`），避免出現亂碼方塊。
*   **負號顯示**：確保 `matplotlib` 的 `axes.unicode_minus` 設為 `False` 以正確顯示負號。

## 4. 版面配置 (Layout)

*   **主圖表 (Main Chart)**：佔據畫面主要部分 (如 70-80%)，繪製 K 線、均線、趨勢線。
*   **副圖表 (Sub Chart)**：位於下方 (如 20-30%)，通常用於繪製成交量 (Volume) 或副指標 (MACD, KD)。
*   **Y 軸範圍**：應動態計算，並預留上下緩衝空間 (如 2%-5%) 以容納高低點標記。

## 5. 技術實現指引 (Implementation Guide)

### 實作方法 A: Z-Order (推薦)

簡單且有效，利用圖層遮罩。

```python
# 影線 (Z-Order 1) - 全長繪製
plt.plot([date, date], [low, high], color='black', zorder=1)

# 實體 (Z-Order 2, Alpha 1.0) - 必須不透明
rect = plt.Rectangle((x, y), width, height, facecolor=color, alpha=1.0, zorder=2)
ax.add_patch(rect)
```

### 實作方法 B: 分段繪製 (Legacy / Alternative)

若實體必須有透明度 (Alpha < 1.0)，則必須使用此方法，將影線切分為上下兩段，避開實體區域。

```python
# 上影線
ax.vlines(x, body_top, high, color='black', linewidth=0.2)
# 下影線
ax.vlines(x, low, body_bottom, color='black', linewidth=0.2)
# 實體
ax.add_patch(rect)
```

## 6. 其他規範 (From Original)

*   **尺寸**：建議 `figsize=(18, 8)`
*   **解析度**：建議 `dpi=200`
*   **線寬**：K 棒寬度 `0.6`，影線線寬 `0.2`~`0.8` (視解析度調整)

### 驗證標準
1. 放大檢視 K 棒，確認實體內部無黑色影線穿過。
2. 確認文字標籤無亂碼。
3. 確認關鍵訊號（如箭頭、圓點）未被 K 棒或均線遮蔽。
