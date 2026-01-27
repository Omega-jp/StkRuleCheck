# Logic Specification: Default Stock ID Change

## Overview
Change the default stock ID from `2330` (TSMC) to `00631L` (Yuanta Daily Taiwan 50 Bull 2X) across all testing, debugging scripts, and documentation.

## Scope
- All `test_*.py` files in the root directory.
- All `debug_*.py` files in the root directory.
- Temporary debug files like `_tmp_debug_wave.py`.
- Documentation files (e.g., `README_MAIN.md`).
- Scripts in `src/` that use `2330` as a default parameter value.

## Logic Changes
- Update function signatures where `stock_id` defaults to `'2330'`.
- Update `input()` prompts where `2330` is mentioned as the default.
- Update hardcoded fallback values in script logic.
- Update example commands and descriptions in documentation.

## User Flow
- When a user runs a test script and doesn't provide a stock ID, it will now default to `00631L`.
- Input prompts will UI-hint `00631L` instead of `2330`.
