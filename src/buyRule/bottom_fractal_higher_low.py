import pandas as pd
from typing import Optional, List, Tuple

from ..baseRule.turning_point_identification import identify_turning_points
from ..baseRule.bottom_fractal_identification import identify_bottom_fractals


def check_bottom_fractal_higher_low(
    df: pd.DataFrame,
    turning_points_df: Optional[pd.DataFrame] = None,
    bottom_fractal_df: Optional[pd.DataFrame] = None,
    left: int = 2,
    right: int = 2,
    tol: float = 0.0,
) -> pd.DataFrame:
    """
    底分型「底底高」試單買入檢查

    規則概要：
    1) 只在最近轉折點為「轉折高」後尋找底分型；
    2) 底分型列表由 baseRule identify_bottom_fractals 提供；
    3) 分型低點必須高於最近一個轉折低點（底底高），且 L 到分型期間不得破 Low_L；
    4) 成立則於分型確立日標記 'O' 至 bottom_fractal_buy。
    """
    if df is None or df.empty:
        return pd.DataFrame()

    if left < 0 or right < 0:
        raise ValueError("left/right 必須為非負整數")

    required_cols = {"Open", "High", "Low", "Close"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame 缺少必要欄位: {missing}")

    df_work = df.copy()
    if not isinstance(df_work.index, pd.DatetimeIndex):
        if "date" in df_work.columns:
            df_work["date"] = pd.to_datetime(df_work["date"], errors="coerce")
            df_work.set_index("date", inplace=True)
        else:
            raise ValueError("缺少 datetime index 或 date 欄位")

    if turning_points_df is None:
        if "ma5" not in df_work.columns:
            df_work["ma5"] = df_work["Close"].rolling(window=5, min_periods=1).mean()
        turning_points_df = identify_turning_points(df_work)

    if bottom_fractal_df is None:
        bottom_fractal_df = identify_bottom_fractals(df_work, left=left, right=right, tol=tol)

    tp = turning_points_df.copy()
    tp["date"] = pd.to_datetime(tp["date"], errors="coerce")
    tp = tp[tp["date"].notna()].sort_values("date")

    # 預先取得轉折點列表（按時間）
    tp_list: List[Tuple[pd.Timestamp, str]] = []
    for _, row in tp.iterrows():
        if row.get("turning_high_point") == "O":
            tp_list.append((row["date"], "high"))
        elif row.get("turning_low_point") == "O":
            tp_list.append((row["date"], "low"))
    tp_list.sort(key=lambda x: x[0])

    # 取所有轉折低點日期（供查詢 Low_L）
    low_tp_dates = [d for d, t in tp_list if t == "low"]

    # 映射日期到索引位置，加速查詢
    date_to_idx = {d: i for i, d in enumerate(df_work.index)}

    # 將分型結果對齊 df
    bf = bottom_fractal_df.copy()
    if not isinstance(bf.index, pd.DatetimeIndex):
        bf["date"] = pd.to_datetime(bf["date"], errors="coerce")
        bf = bf.set_index("date")
    bf = bf.reindex(df_work.index)

    results = []
    last_tp_idx = 0
    last_tp_type: Optional[str] = None

    for i, (idx, row) in enumerate(df_work.iterrows()):
        date = idx

        # 更新最近轉折點類型
        while last_tp_idx < len(tp_list) and tp_list[last_tp_idx][0] <= date:
            last_tp_type = tp_list[last_tp_idx][1]
            last_tp_idx += 1

        # 預設空信號
        signal = ""
        fractal_low = 0.0
        fractal_low_date = ""
        last_turning_low_price = 0.0
        last_turning_low_date = ""
        crossed_higher_low = False

        # 只在最近轉折是高點時，且當日為分型確立日，才檢查底底高
        if last_tp_type == "high" and bf.iloc[i]["bottom_fractal"] == "O":
            p_date = pd.to_datetime(bf.iloc[i]["fractal_low_date"])
            if pd.notna(p_date):
                low_p = float(bf.iloc[i]["fractal_low"])

                # 找最近轉折低點 L（在 p 日期之前）
                prev_lows = [d for d in low_tp_dates if d < p_date]
                if prev_lows:
                    L_date = prev_lows[-1]
                    if L_date in date_to_idx:
                        L_idx = date_to_idx[L_date]
                        Low_L = df_work.iloc[L_idx]["Low"]

                        # 確認期間未跌破 Low_L
                        p_idx = df_work.index.get_loc(p_date)
                        if L_idx + 1 <= p_idx:
                            slice_min = df_work.iloc[L_idx + 1 : p_idx + 1]["Low"].min()
                        else:
                            slice_min = low_p
                        intact_base = slice_min >= Low_L

                        higher_low = low_p > Low_L * (1 + tol / 100.0)

                        if intact_base and higher_low:
                            signal = "O"
                            fractal_low = float(low_p)
                            fractal_low_date = p_date.strftime("%Y-%m-%d")
                            last_turning_low_price = float(Low_L)
                            last_turning_low_date = L_date.strftime("%Y-%m-%d")
                            crossed_higher_low = True

        results.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "bottom_fractal_buy": signal,
                "fractal_low": fractal_low,
                "fractal_low_date": fractal_low_date,
                "last_turning_low": last_turning_low_price,
                "last_turning_low_date": last_turning_low_date,
                "crossed_higher_low": crossed_higher_low,
            }
        )

    return pd.DataFrame(results)
