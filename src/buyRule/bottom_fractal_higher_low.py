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

    Args:
        df: 必須包含 Open/High/Low/Close，日期索引或 date 欄位可轉 datetime。
        turning_points_df: 可選，預先計算的轉折點 DataFrame。
            若為 None，將自動調用 identify_turning_points(df)。
            必須包含欄位：date, turning_high_point, turning_low_point。
        bottom_fractal_df: 可選，預先偵測的底分型 DataFrame。
            若為 None，將自動調用 identify_bottom_fractals(df, left, right, tol)。
            必須包含欄位：date, bottom_fractal, fractal_low, fractal_low_date。
            **建議使用預先偵測的結果以提高性能和確保一致性**。
        left: 分型左窗口長度（僅在 bottom_fractal_df 為 None 時使用）。
        right: 分型右窗口長度（僅在 bottom_fractal_df 為 None 時使用）。
        tol: 容忍百分比（小數），容許平低的誤差。

    Returns:
        DataFrame 與 df 等長，包含：
            - date: 日期字串
            - bottom_fractal_buy: 'O' 表示底底高買訊，'' 表示無訊號
            - fractal_low: 分型低點價格
            - fractal_low_date: 分型低點日期
            - last_turning_low: 最近轉折低點價格
            - last_turning_low_date: 最近轉折低點日期
            - crossed_higher_low: 是否符合底底高條件

    Example:
        >>> # 方式 1：使用預先偵測的底分型（推薦）
        >>> turning_points = identify_turning_points(df)
        >>> bottom_fractals = identify_bottom_fractals(df, left=2, right=2, tol=0.0)
        >>> signals = check_bottom_fractal_higher_low(
        ...     df,
        ...     turning_points_df=turning_points,
        ...     bottom_fractal_df=bottom_fractals
        ... )
        >>>
        >>> # 方式 2：自動偵測（較慢）
        >>> signals = check_bottom_fractal_higher_low(df, left=2, right=2, tol=0.0)
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

    # 驗證或生成轉折點數據
    if turning_points_df is None:
        if "ma5" not in df_work.columns:
            df_work["ma5"] = df_work["Close"].rolling(window=5, min_periods=1).mean()
        turning_points_df = identify_turning_points(df_work)

    # 驗證或生成底分型數據
    if bottom_fractal_df is None:
        # 自動生成時也傳入轉折點，啟用上下文過濾
        bottom_fractal_df = identify_bottom_fractals(
            df_work, 
            left=left, 
            right=right, 
            tol=tol,
            turning_points_df=turning_points_df
        )
    else:
        # 驗證預先提供的底分型數據包含必要欄位
        required_fractal_cols = {"date", "bottom_fractal", "fractal_low", "fractal_low_date"}
        if not isinstance(bottom_fractal_df, pd.DataFrame):
            raise TypeError("bottom_fractal_df 必須是 pandas DataFrame")
        missing_fractal_cols = required_fractal_cols - set(bottom_fractal_df.columns)
        if missing_fractal_cols:
            raise ValueError(f"bottom_fractal_df 缺少必要欄位: {missing_fractal_cols}")

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

    # 將分型結果對齊 df_work 的索引，確保每個交易日都有對應的分型數據行
    # 未偵測到分型的日期會填充為 NaN，後續處理時會過濾掉
    bf = bottom_fractal_df.copy()
    if not isinstance(bf.index, pd.DatetimeIndex):
        bf["date"] = pd.to_datetime(bf["date"], errors="coerce")
        bf = bf.set_index("date")
    bf = bf.reindex(df_work.index)  # 對齊索引，未匹配的行會是 NaN

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
        # 這確保我們在下跌趨勢後的反彈階段尋找買入機會
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
