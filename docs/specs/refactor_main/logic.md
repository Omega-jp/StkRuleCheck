# Logic Specification: Refactor main.py

## 1. Objective
Split the existing `main.py` into two independent executable scripts to separate the "Data Preparation" phase from the "Signal Detection" phase.

## 2. `prepare_data.py` (Data Preparation)
This script allows the user to prepare the dataset (download + calculate indicators) without running the detection logic.

### 2.1 Workflow
1.  **Initialization**:
    -   Define a `step` printer for console output.
    -   Ensure `Data/kbar` directory exists.

2.  **Step 1: KBar Collection**:
    -   Module: `src.data_initial.kbar_collector`
    -   Function: `collect_and_save_kbars()`
    -   Action: Downloads or updates raw K-bar data for stocks defined in config.
    -   Error Handling: Catch exceptions, print error, but decide whether to proceed (usually hard stop if no data, but original `main.py` continues). *Refinement: We will continue to Step 2 even if Step 1 has partial failures, but if the module crashes, we abort.*

3.  **Step 2: Append Indicators**:
    -   Module: `src.data_initial.append_indicator`
    -   Function: `append_indicators_to_csv()`
    -   Action: Reads raw/partial CSVs, calculates TA indicators (MA, KD, MACD), and overwrites/saves the files.
    -   Error Handling: Catch exceptions, print error.

4.  **Step 3: Data Quality Check (Optional)**:
    -   Trigger: Command line argument `--check-missing` or similar.
    -   Module: `check_missing_timestamps.py`
    -   Function: `check_all()`
    -   Action: Checks for missing timestamps against a baseline stock (default 00631L).
    -   Output: Console output of missing/extra timestamps.

5.  **Completion**:
    -   Print summary of execution time and success status.

## 3. `detect_signals.py` (Signal Detection)
This script assumes data is ready and focuses on running the strategy logic.

### 3.1 Workflow
1.  **Initialization**:
    -   Define a `step` printer.
    -   Ensure `output/chart` and `output/buy_rules` directories exist.

2.  **Step 1: Validate Buy Rules**:
    -   Module: `src.validate_buy_rule`
    -   Function: `get_stock_list()` to retrieve the list of stocks.
    -   Function: `validate_buy_rule(stock_id)` for each stock.
    -   Action:
        -   Loads data from `Data/kbar`.
        -   Runs all configured buy rules (San Yang, Four Seas, MACD, etc.).
        -   Generates individual CSV reports and Chart PNGs per stock.
    -   Loop: Iterate through all stocks in `stklist.cfg`.

3.  **Step 2: Summarize Buy Rules**:
    -   Module: `src.summarize_buy_rules`
    -   Function: `main()` (aliased as `summarize_main` in `main.py`).
    -   Action: Aggregates all individual `output/buy_rules/*.csv` into a single summary CSV `output/buy_rules_summary.csv`.

4.  **Completion**:
    -   Print summary of execution time, number of stocks processed, and output locations.

## 4. Shared Logic
-   Both scripts will need to modify `sys.path` to include `src` if they are placed in the root directory (same as `main.py`).
-   `print_step` helper function can be duplicated for simplicity to avoid creating a new utils file just for this.
