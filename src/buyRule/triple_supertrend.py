import pandas as pd
from src.baseRule.supertrend import calculate_supertrend

def check_triple_supertrend(df: pd.DataFrame) -> pd.DataFrame:
    """
    Check Triple Supertrend Buy Signals
    Returns DataFrame with 3 check columns:
    - triple_supertrend_g1_check: Standard (ATR 11, Factor 2.0) Break
    - triple_supertrend_g2_check: Scalping (ATR 10, Factor 1.0) Break
    - triple_supertrend_all_check: All 3 Systems Up (Signal at the transition)
    """
    results = []
    
    # Calculate 3 Supertrends
    # Group 1: Standard (11, 2.0)
    st1 = calculate_supertrend(df, period=11, factor=2.0)
    # Group 2: Scalping (10, 1.0)
    st2 = calculate_supertrend(df, period=10, factor=1.0)
    # Group 3: Major (12, 3.0)
    st3 = calculate_supertrend(df, period=12, factor=3.0)
    
    # Merge into a single alignment for iteration
    # Using underlying arrays for performance is better but DataFrame iterrows is standard in this project
    # merging all into one DF for easier row access
    combined = pd.DataFrame({
        'Close': df['Close'],
        'Dir1': st1['Direction'],
        'Dir2': st2['Direction'],
        'Dir3': st3['Direction']
    }, index=df.index)
    
    for i, (idx, row) in enumerate(combined.iterrows()):
        date = idx.strftime('%Y-%m-%d')
        
        # Default empty
        res = {
            'date': date,
            'triple_supertrend_g1_check': '',
            'triple_supertrend_g2_check': '',
            'triple_supertrend_all_check': ''
        }
        
        if i == 0:
            results.append(res)
            continue
            
        prev_row = combined.iloc[i-1]
        
        # Signal Prioritization Logic: Only mark the strongest signal if multiple occur
        
        # Priority 1: All 3 Up (Transition)
        all_now_up = (row['Dir1'] == 1) and (row['Dir2'] == 1) and (row['Dir3'] == 1)
        any_prev_down = (prev_row['Dir1'] == -1) or (prev_row['Dir2'] == -1) or (prev_row['Dir3'] == -1)
        
        if all_now_up and any_prev_down:
             res['triple_supertrend_all_check'] = 'O'
        else:
            # Priority 2: Group 1 Break (Trend -1 -> 1)
            if row['Dir1'] == 1 and prev_row['Dir1'] == -1:
                res['triple_supertrend_g1_check'] = 'O'
            # Priority 3: Group 2 Break (Trend -1 -> 1)
            elif row['Dir2'] == 1 and prev_row['Dir2'] == -1:
                res['triple_supertrend_g2_check'] = 'O'
             
        results.append(res)
        
    return pd.DataFrame(results).set_index('date', drop=False)
