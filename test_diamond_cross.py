#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鑽石叉 (diamond_cross) 規則測試程式

參考 test_td_sequential_buy_rule.py 的互動風格，提供：
1) 內建樣本資料驗證邏輯
2) 輸入股票代碼載入真實日線，計算並繪圖
"""

from __future__ import annotations

import os
import sys
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager as fm

# 加入 src 搜尋路徑
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.buyRule.diamond_cross import check_diamond_cross
from src.baseRule.turning_point_identification import identify_turning_points
from src.validate_buy_rule import load_stock_data


def _select_font() -> None:
    """選擇可用中文字體避免亂碼。"""
    preferred = ["Microsoft JhengHei", "Arial Unicode MS", "SimHei"]
    for name in preferred:
        try:
            fm.findfont(name, fallback_to_default=False)
            plt.rcParams["font.sans-serif"] = [name]
            plt.rcParams["axes.unicode_minus"] = False
            return
        except ValueError:
            continue
    fallback = os.path.join("assets", "fonts", "NotoSansCJKtc-Regular.otf")
    if os.path.exists(fallback):
        try:
            fm.fontManager.addfont(fallback)
            font_prop = fm.FontProperties(fname=fallback)
            plt.rcParams["font.sans-serif"] = [font_prop.get_name()]
        except Exception:
            pass
    plt.rcParams["axes.unicode_minus"] = False


def _build_sample_dataframe() -> pd.DataFrame:
    """
    內建樣本：
    - 第 6 根形成 ma20 上穿 ma60
    - 第 9 根收盤突破黃金交叉前最近轉折高點，應觸發一次
    """
    dates = pd.date_range("2024-01-01", periods=12, freq="D")
    close = [10, 10.2, 10.5, 10.4, 10.6, 11.0, 10.9, 11.1, 11.5, 11.4, 11.6, 11.7]
    df = pd.DataFrame(
        {
            "Open": close,
            "High": [c + 0.1 for c in close],
            "Low": [c - 0.1 for c in close],
            "Close": close,
            "Volume": [1000 + i * 10 for i in range(len(close))],
        },
        index=dates,
    )
    df["ma20"] = df["Close"].rolling(3, min_periods=1).mean()  # 短期
    df["ma60"] = df["Close"].rolling(5, min_periods=1).mean()  # 長期
    return df


def _summarize_signals(result_df: pd.DataFrame) -> List[str]:
    hits = result_df[result_df["diamond_cross_check"] == "O"]
    if hits.empty:
        print("   ➤ 未偵測到鑽石叉訊號")
        return []
    dates = hits["date"].tolist()
    print(f"   ➤ 鑽石叉訊號 {len(dates)} 次: {', '.join(dates)}")
    return dates


def _plot_chart(stock_id: str, df: pd.DataFrame, result_df: pd.DataFrame) -> None:
    _select_font()
    fig, ax = plt.subplots(figsize=(13, 7))
    dates = df.index
    ax.plot(dates, df["Close"], color="black", label="Close", linewidth=1.3)
    for col, color in (("ma20", "orange"), ("ma60", "purple"), ("ma5", "green"), ("ma10", "steelblue")):
        if col in df.columns:
            ax.plot(dates, df[col], label=col, linewidth=1.0, alpha=0.8, color=color)

    date_lookup = {idx.strftime("%Y-%m-%d"): idx for idx in df.index}
    hits = result_df[result_df["diamond_cross_check"] == "O"]
    if not hits.empty:
        hit_dates = [date_lookup.get(d) for d in hits["date"].tolist()]
        hit_dates = [d for d in hit_dates if d is not None]
        if hit_dates:
            ax.scatter(
                hit_dates,
                df.loc[hit_dates, "Close"] + (df["Close"].max() - df["Close"].min()) * 0.01,
                color="lime",
                edgecolor="black",
                s=60,
                marker="v",
                zorder=10,
                label="鑽石叉訊號",
            )

    # 標記 ma20 上穿 ma60 的交叉點
    prev_high_marks = []
    if {"ma20", "ma60"}.issubset(df.columns):
        ma20 = df["ma20"]
        ma60 = df["ma60"]
        crossover_mask = (ma20 > ma60) & (ma20.shift(1) <= ma60.shift(1))
        cross_dates = df.index[crossover_mask.fillna(False)]
        if len(cross_dates) > 0:
            ax.scatter(
                cross_dates,
                ma20.loc[cross_dates],
                color="red",
                edgecolor="black",
                s=50,
                marker="^",
                zorder=9,
                label="ma20上穿ma60",
            )

            # 標記黃金交叉前最近的轉折高點
            tp_df = identify_turning_points(df)
            tp_df["date"] = pd.to_datetime(tp_df["date"], errors="coerce")
            tp_df = tp_df.dropna(subset=["date"]).set_index("date")
            for cross_dt in cross_dates:
                lookback_start = cross_dt - pd.Timedelta(days=90)
                window = tp_df.loc[tp_df.index < cross_dt]
                window = window.loc[window.index >= lookback_start]
                highs = window[window["turning_high_point"] == "O"]
                if highs.empty:
                    continue
                latest_high = highs.iloc[-1]
                high_dt = latest_high.name
                if high_dt not in df.index:
                    continue
                high_price = df.loc[high_dt, "High"]
                prev_high_marks.append((high_dt, high_price))
            if prev_high_marks:
                dates_mark = [d for d, _ in prev_high_marks]
                prices_mark = [p for _, p in prev_high_marks]
                ax.scatter(
                    dates_mark,
                    prices_mark,
                    color="orange",
                    edgecolor="black",
                    s=60,
                    marker="s",
                    zorder=8,
                    label="黃金交叉前轉折高",
                )

    ax.set_title(f"{stock_id} 鑽石叉訊號", fontsize=15)
    ax.set_xlabel("日期")
    ax.set_ylabel("價格")
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()

    out_dir = "output/test_charts"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{stock_id}_diamond_cross.png")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    print(f"✅ 圖表已保存: {path}")
    backend = plt.get_backend().lower()
    if "agg" not in backend:
        plt.show()
    else:
        plt.close(fig)


def _run_test(stock_id: Optional[str] = None, days: int = 180) -> Tuple[pd.DataFrame, List[str]]:
    if stock_id:
        df = load_stock_data(stock_id, "D")
        if df is None or df.empty:
            raise ValueError(f"無法載入 {stock_id} 的日線資料")
        df = df.sort_index().tail(days)
        print(f"✅ 使用 {stock_id} 最近 {len(df)} 筆資料")
    else:
        df = _build_sample_dataframe()
        print("✅ 使用內建樣本資料")

    result_df = check_diamond_cross(df)
    hits = _summarize_signals(result_df)
    _plot_chart(stock_id or "sample", df, result_df)
    return result_df, hits


def main() -> None:
    print("鑽石叉 (diamond_cross) 測試工具")
    print("=" * 50)
    while True:
        stock_id_in = input("\n請輸入股票代碼 (輸入 sample 用內建資料, quit 離開): ").strip()
        if stock_id_in.lower() == "quit":
            print("程式結束")
            break
        stock_id = None if stock_id_in.lower() == "sample" else stock_id_in or "00631L"

        days_input = input("請輸入顯示天數 (預設180): ").strip()
        try:
            days = int(days_input) if days_input else 180
        except ValueError:
            days = 180

        try:
            _, hits = _run_test(stock_id, days)
            label = stock_id or "sample"
            print(f"\n🎉 {label} 完成，訊號數: {len(hits)}")
        except Exception as exc:
            print(f"❌ 測試失敗: {exc}")

        cont = input("\n是否測試其他股票? (y/n): ").strip().lower()
        if cont != "y":
            break


if __name__ == "__main__":
    main()
