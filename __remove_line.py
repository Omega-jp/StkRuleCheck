from pathlib import Path
path = Path("test_descending_trendline_breakthrough.py")
text = path.read_text(encoding='utf-8')
text = text.replace("    latest_turning_high_date = max(high_point_dates) if high_point_dates else None\n", "")
path.write_text(text, encoding='utf-8')
