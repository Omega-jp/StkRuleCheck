# Logic Specification: Triple Supertrend

## 1. Supertrend Algorithm
The Supertrend indicator is calculated as follows:

1.  **True Range (TR)**: $Max(High - Low, |High - PreviousClose|, |Low - PreviousClose|)$
2.  **ATR**: Simple Moving Average (or Wilder's Smoothing) of TR over `period`. (Pine script `ta.atr` uses RMA - Wilder's Smoothing).
    *   *Note*: Standard `ta.atr` in Pine is RMA (Running Moving Average).
    *   Formula: $RMA_t = \alpha \times x_t + (1-\alpha) \times RMA_{t-1}$ where $\alpha = 1/length$.
3.  **Basic Upper Band**: $(High + Low) / 2 + (Factor \times ATR)$
4.  **Basic Lower Band**: $(High + Low) / 2 - (Factor \times ATR)$
5.  **Final Upper Band**:
    *   If $CurrentBasicUpper < PreviousFinalUpper$ OR $PreviousClose > PreviousFinalUpper$:
        *   $CurrentFinalUpper = CurrentBasicUpper$
    *   Else:
        *   $CurrentFinalUpper = PreviousFinalUpper$
6.  **Final Lower Band**:
    *   If $CurrentBasicLower > PreviousFinalLower$ OR $PreviousClose < PreviousFinalLower$:
        *   $CurrentFinalLower = CurrentBasicLower$
    *   Else:
        *   $CurrentFinalLower = PreviousFinalLower$
7.  **Trend Direction**:
    *   If $PreviousTrend$ was DOWN and $Close > PreviousFinalUpper$: Trend becomes UP.
    *   If $PreviousTrend$ was UP and $Close < PreviousFinalLower$: Trend becomes DOWN.
8.  **Supertrend Value**:
    *   If Trend is UP: $FinalLowerBand$
    *   If Trend is DOWN: $FinalUpperBand$

## 2. Configuration Groups

| Group | Factor | ATR Period | Output Column suffix | Display Name |
| :--- | :--- | :--- | :--- | :--- |
| **Group 1** | 2.0 | 11 | `_g1_check` | 超級趨勢(標準) |
| **Group 2** | 1.0 | 10 | `_g2_check` | 超級趨勢(短線) |
| **Group 3** | 3.0 | 12 | `_all_check` | 超級趨勢(三線共振) |

## 3. Buy Signals

### Signal 1: Group 1 Break (`triple_supertrend_g1_check`)
- **Condition**: Close > Supertrend1 AND PrevClose <= PrevSupertrend1 (Trend turned Up).
- **Marker**: 'O'

### Signal 2: Group 2 Break (`triple_supertrend_g2_check`)
- **Condition**: Close > Supertrend2 AND PrevClose <= PrevSupertrend2.
- **Marker**: 'O'

### Signal 3: All 3 Confirm (`triple_supertrend_all_check`)
- **Condition**: 
    - Trend1 is UP AND Trend2 is UP AND Trend3 is UP.
    - **Trigger**: The current bar is the *first* bar where this condition became true (i.e., the last of the 3 lines has just been broken).
- **Marker**: 'O'

## 4. Visual Logic (for Test Tool)
- **Fill**:
    - Calculate `bodyMiddle = (Open + Close) / 2`.
    - Fill region between `bodyMiddle` and `SupertrendLine`.
    - Color Green if Trend is Up, Red if Trend is Down.
