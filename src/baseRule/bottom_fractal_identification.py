import pandas as pd
from typing import Optional


def identify_bottom_fractals(
    df: pd.DataFrame,
    left: int = 2,
    right: int = 2,
    tol: float = 0.0,
) -> pd.DataFrame:
    """
    掃描所有底分型（不判斷底底高），僅基於價序列標記 n 根窗口的區間最低點。

    定義：
    - 分型低點位置 p 滿足：
        Low[p] <= min(Low[p-left:p]) * (1 + tol/100)
        Low[p] <= min(Low[p+1:p+right+1]) * (1 + tol/100)
      需有足夠左右窗口資料。
    - 分型在右窗口結束日 i = p + right 確立。

    Args:
        df: 必須包含 Open/High/Low/Close，日期索引或 date 欄位可轉 datetime。
        left: 左窗口長度。
        right: 右窗口長度。
        tol: 容忍百分比（小數），容許平低的誤差。

    Returns:
        DataFrame 與 df 等長，包含：
            - date
            - bottom_fractal: 'O' 或 ''
            - fractal_low: 分型低點價
            - fractal_low_date: 分型低點日期
    """
    if df is None or df.empty:
        return pd.DataFrame()

    required = {"Open", "High", "Low", "Close"}
    if missing := (required - set(df.columns)):
        raise ValueError(f"DataFrame 缺少必要欄位: {missing}")

    data = df.copy()
    if not isinstance(data.index, pd.DatetimeIndex):
        if "date" in data.columns:
            data["date"] = pd.to_datetime(data["date"], errors="coerce")
            data = data.set_index("date")
        else:
            raise ValueError("缺少 datetime index 或 date 欄位")

    # 預先建立與原始資料等長的結果，之後在確立時回填標記到「中心位置」
    results = [
        {
            "date": idx.strftime("%Y-%m-%d"),
            "bottom_fractal": "",
            "fractal_low": 0.0,
            "fractal_low_date": "",
            "fractal_left_date": "",
            "fractal_right_date": "",
        }
        for idx in data.index
    ]

    for i, (idx, row) in enumerate(data.iterrows()):
        tol_factor = 1 + tol / 100.0
        found = False
        matched_low_p = None
        matched_p = None
        # 可變窗長：視窗總長 3~5，最低點落在左右兩根之間即可
        max_window = min(left + right + 1, 5)
        min_window = 3
        for window_len in range(min_window, max_window + 1):
            left_idx = i - window_len + 1
            if left_idx < 0:
                continue

            left_high_ref = data.iloc[left_idx]["High"]
            left_low_ref = data.iloc[left_idx]["Low"]
            right_low_ref = data.iloc[i]["Low"]
            confirm_close = data.iloc[i]["Close"]

            inter_slice = data.iloc[left_idx + 1 : i]
            if inter_slice.empty:
                continue

            low_p = inter_slice["Low"].min()
            matched_p = inter_slice["Low"].idxmin()

            # 中間區間（不含左右端）不得突破左K高點（含開盤/最高）
            inter_high_ok = (
                inter_slice["High"].max() <= left_high_ref
                and inter_slice["Open"].max() <= left_high_ref
            )
            inside_mask = (inter_slice["High"] <= left_high_ref) & (inter_slice["Low"] >= left_low_ref)
            inter_inside_ok = inside_mask.sum() <= 3

            is_fractal = (
                low_p <= left_low_ref * tol_factor
                and low_p <= right_low_ref * tol_factor
                and (confirm_close > left_high_ref)
                and inter_high_ok
                and inter_inside_ok
            )
            if is_fractal:
                found = True
                matched_low_p = low_p
                matched_p = data.index.get_loc(matched_p)
                break

        if found:
            # 標記在「成立那一天」（右窗口的末日），但記錄實際分型低點資訊
            results[i]["bottom_fractal"] = "O"
            results[i]["fractal_low"] = float(matched_low_p)
            results[i]["fractal_low_date"] = data.index[matched_p].strftime("%Y-%m-%d")
            results[i]["fractal_left_date"] = data.index[left_idx].strftime("%Y-%m-%d")
            results[i]["fractal_right_date"] = data.index[i].strftime("%Y-%m-%d")

    return pd.DataFrame(results)
