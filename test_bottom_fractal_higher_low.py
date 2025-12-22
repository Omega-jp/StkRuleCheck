#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
底分型「底底高」試單買入規則測試程式

參照 test_descending_trendline_breakthrough.py 的風格：
- 可直接執行的 CLI，支援樣本模式與指定股票模式
- 執行過程清楚輸出流程、結果摘要

執行範例：
    python3 test_bottom_fractal_higher_low.py
    python3 test_bottom_fractal_higher_low.py --stock 2330 --days 120 --left 2 --right 2 --tol 0.0
"""

import argparse
import os
import sys
from typing import Tuple

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 添加 src 目錄到 Python 路徑
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.buyRule.bottom_fractal_higher_low import check_bottom_fractal_higher_low
from src.validate_buy_rule import load_stock_data
from src.baseRule.turning_point_identification import identify_turning_points
from src.baseRule.bottom_fractal_identification import identify_bottom_fractals


def _register_local_fonts():
    """嘗試註冊專案內附的中文字體（若存在）。"""
    local_font_paths = [
        os.path.join(os.path.dirname(__file__), "assets", "fonts", "NotoSansCJKtc-Regular.otf"),
        os.path.join(os.path.dirname(__file__), "assets", "fonts", "NotoSansCJKsc-Regular.otf"),
    ]
    for font_path in local_font_paths:
        if os.path.isfile(font_path):
            try:
                fm.fontManager.addfont(font_path)
            except Exception:
                pass


def _ensure_plot_fonts():
    """
    嘗試使用常見的中文字體，避免圖表中文字顯示警告。
    若找不到就使用預設字體。
    """
    _register_local_fonts()

    preferred_fonts = [
        "Microsoft JhengHei",
        "Microsoft YaHei",
        "SimHei",
        "Arial Unicode MS",
        "PingFang TC",
        "Noto Sans CJK TC",
        "Noto Sans CJK SC",
        "WenQuanYi Zen Hei",
        "Source Han Sans TC",
        "Source Han Sans SC",
        "Noto Sans CJK TC Regular",
        "Noto Sans CJK SC Regular",
    ]

    available_fonts = {f.name for f in fm.fontManager.ttflist}
    for font in preferred_fonts:
        if font in available_fonts:
            plt.rcParams["font.sans-serif"] = [font]
            plt.rcParams["axes.unicode_minus"] = False
            return

    # fallback
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def build_positive_case() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    正例：
    - 最近轉折為高點（2024-01-03）
    - 最近轉折低點 L 在 2024-01-02，Low_L = 7.5
    - 分型窗口 left=1, right=1，分型低點在 2024-01-04，高於 Low_L
    - 分型確立日 2024-01-05 應標記 'O'
    """
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    df = pd.DataFrame(
        {
            "Open": [11, 8.5, 8.6, 8.4, 8.8],
            "High": [12, 9.0, 9.0, 9.0, 9.5],
            "Low": [10.0, 7.5, 8.2, 8.0, 8.5],
            "Close": [11.5, 8.0, 8.5, 8.6, 9.0],
        },
        index=dates,
    )
    turning_points_df = pd.DataFrame(
        [
            {"date": "2024-01-02", "turning_high_point": "", "turning_low_point": "O"},  # L = 7.5
            {"date": "2024-01-03", "turning_high_point": "O", "turning_low_point": ""},  # 最新轉折為高
        ]
    )
    return df, turning_points_df


def build_break_base_case() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    破底例：
    - 最近轉折低在 2024-02-02（Low_L=7.5），最近轉折高在 2024-02-03（最新為高）
    - 2024-02-03 同時破 Low_L，基底被破壞 → 不應產生信號
    """
    dates = pd.date_range("2024-02-01", periods=5, freq="D")
    df = pd.DataFrame(
        {
            "Open": [10, 9.0, 8.8, 8.6, 8.9],
            "High": [10.5, 9.2, 9.0, 8.9, 9.2],
            "Low": [9.5, 7.5, 7.0, 7.4, 7.8],  # day3 破 Low_L=7.5
            "Close": [10.0, 8.0, 7.2, 7.6, 8.5],
        },
        index=dates,
    )
    turning_points_df = pd.DataFrame(
        [
            {"date": "2024-02-02", "turning_high_point": "", "turning_low_point": "O"},  # L = 7.5
            {"date": "2024-02-03", "turning_high_point": "O", "turning_low_point": ""},  # 最新轉折為高
        ]
    )
    return df, turning_points_df


def run_positive_case():
    print("\n=== 正例：底底高分型應觸發 ===")
    df, turning_points_df = build_positive_case()
    result = check_bottom_fractal_higher_low(df, turning_points_df, left=1, right=1, tol=0.0)
    print(result[["date", "bottom_fractal_buy", "fractal_low", "fractal_low_date", "last_turning_low", "last_turning_low_date", "crossed_higher_low"]].to_string(index=False))

    signal_row = result[result["date"] == "2024-01-05"].iloc[0]
    assert signal_row["bottom_fractal_buy"] == "O", "正例未標記試單信號"
    assert signal_row["fractal_low_date"] == "2024-01-04"
    assert signal_row["last_turning_low_date"] == "2024-01-02"
    print("✅ 通過：2024-01-05 標記 'O'")


def run_break_base_case():
    print("\n=== 破底例：基底被破壞不應觸發 ===")
    df, turning_points_df = build_break_base_case()
    result = check_bottom_fractal_higher_low(df, turning_points_df, left=1, right=1, tol=0.0)

    print(result[["date", "bottom_fractal_buy", "fractal_low", "fractal_low_date", "last_turning_low", "last_turning_low_date", "crossed_higher_low"]].to_string(index=False))
    assert result["bottom_fractal_buy"].eq("O").sum() == 0, "破底例不應產生信號"
    print("✅ 通過：未標記信號")


def run_real_data(stock_id: str, days: int, left: int, right: int, tol: float):
    print(f"\n=== 實際資料模式：{stock_id} (最近 {days} 天) ===")
    df = load_stock_data(stock_id, "D")
    if df is None or df.empty:
        raise ValueError(f"無法載入股票 {stock_id} 的數據")

    if not isinstance(df.index, pd.DatetimeIndex):
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
        else:
            raise ValueError("缺少日期索引，無法測試")

    df = df.sort_index()
    if days > 0:
        df = df.tail(days)

    if "ma5" not in df.columns:
        df["ma5"] = df["Close"].rolling(window=5, min_periods=1).mean()

    turning_points_df = identify_turning_points(df)
    bottom_fractal_df = identify_bottom_fractals(df, left=left, right=right, tol=tol)
    result = check_bottom_fractal_higher_low(
        df,
        turning_points_df=turning_points_df,
        bottom_fractal_df=bottom_fractal_df,
        left=left,
        right=right,
        tol=tol,
    )

    hits = result[result["bottom_fractal_buy"] == "O"]
    print("\n--- 近10日結果 ---")
    print(result.tail(10)[["date", "bottom_fractal_buy", "fractal_low", "fractal_low_date", "last_turning_low", "last_turning_low_date", "crossed_higher_low"]].to_string(index=False))
    if hits.empty:
        print("➤ 未偵測到底底高分型訊號")
    else:
        dates = ", ".join(hits["date"].tolist())
        print(f"➤ 偵測到 {len(hits)} 次訊號：{dates}")

    # 轉折點對齊 df
    tp = turning_points_df.copy()
    if "date" in tp.columns:
        tp["date"] = pd.to_datetime(tp["date"], errors="coerce")
        tp = tp.set_index("date")
    tp = tp.reindex(df.index)

    # 繪圖：K 線 + 轉折點 + 底底高買訊
    try:
        _ensure_plot_fonts()
        fig, ax = plt.subplots(figsize=(12, 6))

        # 畫簡易 K 線
        width = 0.6
        color_up = "red"
        color_down = "green"
        for d, row in df.iterrows():
            open_p, high_p, low_p, close_p = row[["Open", "High", "Low", "Close"]]
            color = color_up if close_p >= open_p else color_down
            ax.plot([d, d], [low_p, high_p], color=color, linewidth=1)
            body_bottom = min(open_p, close_p)
            body_height = abs(close_p - open_p)
            ax.bar(
                d,
                body_height if body_height > 0 else 0.2,
                bottom=body_bottom,
                color=color,
                width=width,
                align="center",
                alpha=0.8,
            )

        # 標記轉折高低點
        highs = tp[tp["turning_high_point"] == "O"]
        lows = tp[tp["turning_low_point"] == "O"]
        if not highs.empty:
            ax.scatter(
                highs.index,
                df.loc[highs.index, "High"] * 1.01,  # 稍微上移避免遮擋
                marker="v",
                color="orange",
                s=80,
                label="轉折高",
                zorder=5,
            )
        if not lows.empty:
            ax.scatter(
                lows.index,
                df.loc[lows.index, "Low"] * 0.99,  # 稍微下移避免遮擋
                marker="^",
                color="blue",
                s=80,
                label="轉折低",
                zorder=5,
            )

        # 標記所有底分型（淡色）
        bf_hits = bottom_fractal_df[bottom_fractal_df["bottom_fractal"] == "O"]
        if not bf_hits.empty:
            bf_hits = bf_hits.copy()
            bf_hits["date"] = pd.to_datetime(bf_hits["date"])
            bf_hits = bf_hits.set_index("date")
            bf_hits = bf_hits.reindex(df.index)
            ax.scatter(
                bf_hits.index,
                df.loc[bf_hits.index, "Low"] * 0.97,
                marker="o",
                color="gray",
                alpha=0.5,
                s=40,
                label="底分型",
                zorder=4,
            )

        # 標記分型低點與買訊
        if not hits.empty:
            for _, row in hits.iterrows():
                hit_date = pd.to_datetime(row["date"])
                if hit_date in df.index:
                    close_val = df.loc[hit_date, "Close"]
                    ax.scatter(
                        hit_date,
                        close_val,
                        color="red",
                        marker="^",
                        s=120,
                        zorder=6,
                        label="底底高買訊",
                    )

        ax.set_title(f"{stock_id} K線 + 轉折點 + 底底高訊號", fontsize=14)
        ax.set_xlabel("Date")
        ax.set_ylabel("Price")
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.legend(loc="best")
        ax.grid(True, linestyle="--", alpha=0.3)
        output_dir = os.path.join("output", "test_charts")
        os.makedirs(output_dir, exist_ok=True)
        chart_path = os.path.join(output_dir, f"{stock_id}_bottom_fractal.png")
        plt.tight_layout()
        plt.savefig(chart_path)
        plt.close(fig)
        print(f"🖼️  圖表已保存: {chart_path}")
    except Exception as exc:
        print(f"⚠️  繪圖失敗: {exc}")


def main():
    parser = argparse.ArgumentParser(description="底分型「底底高」試單買入規則測試")
    parser.add_argument("--stock", type=str, help="指定股票代碼跑真實資料，若不填則跑可控樣本")
    parser.add_argument("--days", type=int, default=120, help="載入近 N 天資料")
    parser.add_argument("--left", type=int, default=2, help="分型左窗口")
    parser.add_argument("--right", type=int, default=2, help="分型右窗口")
    parser.add_argument("--tol", type=float, default=0.0, help="容忍百分比 (小數)")
    args = parser.parse_args()

    print("=== 底分型「底底高」試單買入規則測試 ===")

    if args.stock:
        run_real_data(args.stock, args.days, args.left, args.right, args.tol)

    else:
        while True:
            user_input = input("請輸入股票代碼 (預設2330，輸入'y'結束，輸入'sample'跑樣本): ").strip()
            if user_input.lower() == "y":
                print("結束測試")
                break
            if user_input.lower() == "sample" or user_input == "":
                run_positive_case()
                run_break_base_case()
                print("\n🎉 測試完成，樣本模式")
                continue
            stock_id = user_input if user_input else "2330"
            try:
                run_real_data(stock_id, args.days, args.left, args.right, args.tol)
            except Exception as exc:
                print(f"❌ 測試失敗: {exc}")


if __name__ == "__main__":
    main()
