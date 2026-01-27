# Logic Specification: Column Order Adjustment for Triple Supertrend

## Overview
Adjust the column order and mapping in `buy_rules_summary.csv` to ensure "G1 (Scalp)", "G2 (Standard)", and "G3 (Triple Resonance)" are displayed in that specific order.

## Background
In a previous step, Triple Supertrend G1 was redefined as Scalp Break and G2 as Standard Break. The summary script mapping and column order currently show G2 before G1 or have inconsistent labeling.

## Scope
- `src/summarize_buy_rules.py`: Update the display name mapping and the `column_order` list.
- `src/buyRule/triple_supertrend.py`: Correct the docstring to match the actual implementation.

## Logic Changes
- **Mapping Update**:
  - `triple_supertrend_g1_check` -> `超級趨勢(短線)`
  - `triple_supertrend_g2_check` -> `超級趨勢(標準)`
- **Order Update**:
  - The `column_order` list should prioritize `超級趨勢(短線)` then `超級趨勢(標準)`.
