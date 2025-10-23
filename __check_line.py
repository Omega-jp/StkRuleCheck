from src.validate_buy_rule import load_stock_data

stock_id = "00631l"
df = load_stock_data(stock_id, "D").tail(360)
start_idx = df.index.get_loc(df.index[df.index.get_loc("2025-01-07")])
