# API: SVG Chart Output

## Internal Functions

### `create_simple_chart(stock_id, recent_df, turning_points_df, resistance_results, resistance_data, days)`

- **Purpose**: Generates and saves a technical analysis chart.
- **Input**:
    - `stock_id` (str): Stock ticker symbol.
    - `recent_df` (pd.DataFrame): Price data.
    - `turning_points_df` (pd.DataFrame): Identified turning points.
    - `resistance_results` (pd.DataFrame): Breakthrough analysis results.
    - `resistance_data` (pd.DataFrame): Raw resistance data.
    - `days` (int): Number of days to display.
- **Output**: Writes files to disk.
- **Change**:
    - Adds a second `plt.savefig()` call or modifies the existing logic to iterate over desired formats.
    - Target file path for SVG: `f'output/test_charts/{stock_id}_resistance_with_turning_points.svg'`.
