from src.validate_buy_rule import load_stock_data
from src.baseRule.turning_point_identification import identify_turning_points
from src.baseRule.waving_point_identification import identify_waving_points
from src.buyRule.long_term_descending_trendline import _build_index_key_map,_collect_wave_high_points,_segment_respects_line
import pandas as pd

df=load_stock_data("00631l","D").tail(360)
turning=identify_turning_points(df)
waves=identify_waving_points(df,turning)
map=_build_index_key_map(df.index)
wh=_collect_wave_high_points(df,waves,map)
for i,p1 in enumerate(wh):
    for j,p2 in enumerate(wh):
        if j<=i: continue
        slope=(p2['price']-p1['price'])/(p2['idx']-p1['idx'])
        if slope>0: continue
        intercept=p1['price']-slope*p1['idx']
        diffs=[]
        ok=True
        for idx in range(p1['idx'],p2['idx']+1):
            trend=intercept+slope*idx
            high=df.iloc[idx]['High']
            diff=high-trend
            diffs.append(diff)
            if diff>trend*0.001: # 0.1%
                ok=False
        if ok:
            print('pair',i,j,'dates',p1['date'],p2['date'])
        print('pair',i,j,'maxdiff',max(diffs))
