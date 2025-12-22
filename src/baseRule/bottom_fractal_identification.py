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
        }
        for idx in data.index
    ]

    for i, (idx, row) in enumerate(data.iterrows()):
        p = i - right
        if p < 0 or p - left < 0:
            continue

        low_p = data.iloc[p]["Low"]
        has_left = left == 0 or len(data.iloc[p - left : p]) == left
        has_right = right == 0 or len(data.iloc[p + 1 : p + right + 1]) == right
        if not (has_left and has_right):
            continue

        min_left = data.iloc[p - left : p]["Low"].min() if left > 0 else low_p
        min_right = data.iloc[p + 1 : p + right + 1]["Low"].min() if right > 0 else low_p
        tol_factor = 1 + tol / 100.0
        confirm_close = data.iloc[i]["Close"]
        left_high_ref = data.iloc[p - left]["High"] if left > 0 else data.iloc[p]["High"]
        # 中間區間（不含右K）不得突破左K高點（含開盤/最高）
        inter_high_ok = True
        if right > 0 and left > 0:
            inter_slice = data.iloc[p - left + 1 : p + right]  # 開區間，排除最左與最右
            if not inter_slice.empty:
                inter_high_ok = (
                    inter_slice["High"].max() <= left_high_ref
                    and inter_slice["Open"].max() <= left_high_ref
                )
        elif right > 0:
            inter_slice = data.iloc[p + 1 : p + right]
            if not inter_slice.empty:
                inter_high_ok = (
                    inter_slice["High"].max() <= left_high_ref
                    and inter_slice["Open"].max() <= left_high_ref
                )

        is_fractal = (
            low_p <= min_left * tol_factor
            and low_p <= min_right * tol_factor
            and (confirm_close > left_high_ref)
            and inter_high_ok
        )
        if is_fractal:
            # 標記在「成立那一天」（右窗口的末日），但記錄實際分型低點資訊
            results[i]["bottom_fractal"] = "O"
            results[i]["fractal_low"] = float(low_p)
            results[i]["fractal_low_date"] = data.index[p].strftime("%Y-%m-%d")

    return pd.DataFrame(results)
