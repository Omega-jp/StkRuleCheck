# Data Specification: Refactor main.py

This document defines the data structures exchanged between the two new scripts via the file system.

## 1. File Storage Structure
-   **Root Directory**: `Data/kbar/`
-   **Naming Convention**:
    -   Daily Data: `{stock_id}_D.csv`
    -   Weekly Data: `{stock_id}_W.csv`
    -   Raw Data: `{stock_id}_Raw.csv` (used for reconstruction if needed)

## 2. CSV Schema (Data Interface)

The `prepare_data.py` script ensures the CSVs contain the following columns before `detect_signals.py` reads them.

### 2.1 Columns
-   **Index**: `ts` (Timestamp)
-   **OHLCV**:
    -   `Open`, `High`, `Low`, `Close` (Float)
    -   `Volume` (Float/Int)
-   **Indicators** (Added by `append_indicator.py`):
    -   **KD**: `RSV`, `%K`, `%D`
    -   **MACD**: `EMA_short`, `EMA_long`, `MACD`, `Signal`, `Histogram`
    -   **Moving Averages**: `ma5`, `ma10`, `ma20`, `ma60`
    -   **Impulse MACD**: `ImpulseMACD`, `ImpulseSignal`, `ImpulseHistogram`

### 2.2 Data Integrity
-   `detect_signals.py` expects these columns to exist.
-   If validation fails (missing columns), `validate_buy_rule` typically attempts to re-calculate inline (`_append_indicators_inline`), providing a fallback mechanism. The refactoring retains this resilience.

## 3. Output Schema (Signal Detection)
-   **Summary File**: `output/buy_rules_summary.csv`
-   **Columns**:
    -   `stock_id`
    -   `date`
    -   `[Rule_Name]_check` (e.g., `san_yang_kai_tai_check`): 'O' (True) or '' (False).
    -   Other rule-specific output columns.
