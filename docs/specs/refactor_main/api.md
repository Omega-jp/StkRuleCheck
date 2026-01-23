# API Specification: Refactor main.py

Since these are executable scripts (entry points), the "API" refers to Command Line Interface (CLI) input/output and function calls to internal modules.

## 1. `prepare_data.py`

### 1.1 Interface
-   **Execution**: `python prepare_data.py [options]`
-   **Arguments**:
    -   `--check-missing`: Trigger the data quality check (check_missing_timestamps).
    -   `--baseline [STOCK_ID]`: (Optional) Specify baseline stock for checking, default `00631L`.

### 1.2 Module Interactions
-   **Calls**:
    1.  `src.data_initial.kbar_collector.collect_and_save_kbars()`
        -   **Input**: Reads `config/stklist.cfg` (internally).
        -   **Output**: Writes files to `Data/kbar/`.
    2.  `src.data_initial.append_indicator.append_indicators_to_csv()`
        -   **Input**: Reads `Data/kbar/`.
        -   **Output**: Updates `Data/kbar/` with calculated columns.
    3.  `check_missing_timestamps.check_all()` (Optional)
        -   **Input**: Reads `Data/kbar/`.
        -   **Output**: Print analysis.

## 2. `detect_signals.py`

### 2.1 Interface
-   **Execution**: `python detect_signals.py`
-   **Arguments**: None (currently hardcoded to process all stocks in config).

### 2.2 Module Interactions
-   **Calls**:
    1.  `src.validate_buy_rule.get_stock_list()`
    2.  `src.validate_buy_rule.validate_buy_rule(stock_id)`
        -   **Input**: `stock_id` (str).
        -   **Reads**: `Data/kbar/{stock_id}_[D|W].csv`.
        -   **Output**:
            -   `output/buy_rules/{stock_id}_D_Rule.csv`
            -   `output/chart/{stock_id}_validation_chart.png`
            -   `output/base_rule/*` (intermediate files).
    3.  `src.summarize_buy_rules.main()`
        -   **Input**: Reads all files in `output/buy_rules/`.
        -   **Output**: Generates `output/buy_rules_summary.csv`.
