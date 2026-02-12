# 趨勢判斷介面規格書 (Trend Identification API)

## 1. 概述
本文件定義趨勢判斷模組的程式介面 (API)，供其他模組調用以獲取股票的趨勢狀態。

## 2. 模組位置
- **路徑**：`src/analysis/trend_analyzer.py` (建議新增)
- **依賴**：
    - `src.baseRule.turning_point_identification`
    - `src.baseRule.waving_point_identification`

## 3. 核心函式

### 3.1 get_trend_status
計算並回傳指定股票資料的當前趨勢狀態。

```python
def get_trend_status(df: pd.DataFrame) -> TrendResult:
    """
    分析輸入的 K 線資料，回傳最後一筆資料的趨勢狀態。
    
    Args:
        df (pd.DataFrame): 包含 Open, High, Low, Close, ma5 的 K 線資料。
        
    Returns:
        TrendResult: 包含趨勢枚舉與相關資訊的物件。
    """
    pass
```

## 4. 資料結構

### 4.1 TrendType (Enum)
```python
class TrendType(Enum):
    UP = "UP"                     # 漲勢
    DOWN = "DOWN"                 # 跌勢
    CONSOLIDATION = "CONSOLIDATION" # 盤整
    UNKNOWN = "UNKNOWN"           # 未知 (資料不足)
```

### 4.2 TrendResult (Dataclass)
```python
@dataclass
class TrendResult:
    status: TrendType             # 目前趨勢狀態
    last_high: float              # 最近一個轉折高點價格
    last_low: float               # 最近一個轉折低點價格
    confirmation_date: str        # 趨勢確認日期 (YYYY-MM-DD)
    details: str                  # 描述 (例如 "突破前高 150.0 確認漲勢")
```

## 5. 錯誤處理
- **ValueError**: 若輸入 DataFrame 缺少必要欄位 (`ma5` 等)。
- **InsufficientDataError**: 若資料筆數過少，無法計算轉折點。
