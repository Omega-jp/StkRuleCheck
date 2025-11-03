from src.validate_buy_rule import load_stock_data
from src.baseRule.turning_point_identification import identify_turning_points
from src.baseRule.waving_point_identification import identify_waving_points
from src.buyRule.long_term_descending_trendline import identify_descending_trendlines
from src.buyRule.breakthrough_descending_trendline import check_breakthrough_descending_trendline

stock_id = "00631l"
df = load_stock_data(stock_id, "D").tail(360)
turning = identify_turning_points(df)
waves = identify_waving_points(df, turning)
trend = identify_descending_trendlines(df, waves)
print('diagonal lines count:', len(trend.get('diagonal_lines', [])))
for idx, line in enumerate(trend.get('diagonal_lines', [])):
    print(f'Line {idx+1}:', line)

signals = check_breakthrough_descending_trendline(
    df,
    trend,
)
print('signal rows:', len(signals))
print(signals[['date','breakthrough_check','breakthrough_type','signal_strength','breakthrough_pct']])
