# API Specification: Triple Supertrend

## 1. Base Calculation Module
**Path**: `src/baseRule/supertrend.py`

### `calculate_supertrend(df: pd.DataFrame, period: int, factor: float) -> pd.DataFrame`
- **Input**: DataFrame with `High`, `Low`, `Close`.
- **Output**: DataFrame with columns:
    - `Supertrend`: The value of the line.
    - `Direction`: 1 (Up/Green), -1 (Down/Red).

## 2. Buy Rule Module
**Path**: `src/buyRule/triple_supertrend.py`

### `check_triple_supertrend(df: pd.DataFrame) -> pd.DataFrame`
- **Input**: DataFrame with Open, High, Low, Close.
- **Output**: DataFrame with same index, containing columns:
    - `triple_supertrend_g1_check`: 'O' or ''
    - `triple_supertrend_g2_check`: 'O' or ''
    - `triple_supertrend_all_check`: 'O' or ''

## 3. Summary Script Update
**Path**: `src/summarize_buy_rules.py`

### `get_latest_result(df, rule_name, stock_id)`
- **Behavior Change**:
    - Detects if the result DataFrame allows multiple check columns.
    - If multiple found (e.g., `_check`), returns a dictionary `{col_name: value}`.
    - If single found (legacy), returns value `str`.

### `main()`
- **Behavior Change**:
    - If `result` is dict, iterate keys and use `get_rule_display_name(key)` to populate row.

## 4. Visualization Test
**Path**: `test_triple_supertrend.py`
- Standalone script using `matplotlib`.
- Replicates the "Fill" visualization from Pine Script.
