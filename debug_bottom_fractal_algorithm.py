#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
底分型 + 底底高訊號診斷程式

參照 debug_turning_point_algorithm.py 的風格，提供：
1. 載入指定股票近 N 日資料
2. 計算轉折點、底分型（baseRule）、底底高買訊（buyRule）
3. 列印統計與明細
4. 輸出圖表：K 線 + 均線 + 底分型

執行範例：
    python3 debug_bottom_fractal_algorithm.py --stock 2330 --days 120 --left 2 --right 2 --tol 0.0
"""

import argparse
import os
import sys
from typing import Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 添加 src 路徑
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.validate_buy_rule import load_stock_data
from src.baseRule.turning_point_identification import identify_turning_points
from src.baseRule.bottom_fractal_identification import identify_bottom_fractals
from src.buyRule.bottom_fractal_higher_low import check_bottom_fractal_higher_low


def _register_local_fonts():
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
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def load_data(stock_id: str, days: int) -> pd.DataFrame:
    df = load_stock_data(stock_id, "D")
    if df is None or df.empty:
        raise ValueError(f"無法載入股票 {stock_id} 的日線資料")
    if not isinstance(df.index, pd.DatetimeIndex):
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
        else:
            raise ValueError("缺少日期索引，無法進行診斷")
    df = df.sort_index()
    if days > 0:
        df = df.tail(days)
    # 確保常用均線存在，便於圖表顯示
    for window in (5, 10, 20, 60):
        col = f"ma{window}"
        if col not in df.columns:
            df[col] = df["Close"].rolling(window=window, min_periods=1).mean()
    return df


def summarize(turning: pd.DataFrame, fractals: pd.DataFrame, signals: pd.DataFrame):
    highs = turning[turning["turning_high_point"] == "O"]
    lows = turning[turning["turning_low_point"] == "O"]
    bf_hits = fractals[fractals["bottom_fractal"] == "O"]
    buys = signals[signals["bottom_fractal_buy"] == "O"]

    print("\n=== 統計 ===")
    print(f"轉折高: {len(highs)} 轉折低: {len(lows)}")
    print(f"底分型數量: {len(bf_hits)}")
    print(f"底底高買訊數量: {len(buys)}")

    if not buys.empty:
        print("\n底底高買訊日期：", ", ".join(buys["date"].tolist()))


def plot_chart(stock_id: str, df: pd.DataFrame, turning: pd.DataFrame, fractals: pd.DataFrame, signals: pd.DataFrame, left: int, right: int):
    _ensure_plot_fonts()
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.set_facecolor("#f9fbff")

    # 使用序列位置代替日期軸，避免非交易日的空白
    xs = np.arange(len(df))
    pos_map = {d: i for i, d in enumerate(df.index)}

    # 繪製簡易 K 線（引線置中於 K 棒）
    width = 0.45
    color_up = "#e74c3c"   # 紅
    color_down = "#2ecc71" # 綠
    for i, (d, row) in enumerate(df.iterrows()):
        open_p, high_p, low_p, close_p = row[["Open", "High", "Low", "Close"]]
        color = color_up if close_p >= open_p else color_down
        ax.vlines(xs[i], low_p, high_p, color=color, linewidth=1.2, alpha=0.9, zorder=2)
        body_bottom = min(open_p, close_p)
        body_height = abs(close_p - open_p)
        rect = plt.Rectangle(
            (xs[i] - width / 2, body_bottom),
            width,
            body_height if body_height > 0 else 0.2,
            facecolor=color,
            edgecolor="#ffffff",
            linewidth=0.5,
            alpha=0.9,
            zorder=3,
        )
        ax.add_patch(rect)

    # 對齊索引
    turning_idx = turning.copy()
    turning_idx["date"] = pd.to_datetime(turning_idx["date"])
    turning_idx = turning_idx.set_index("date").reindex(df.index)

    bf_idx = fractals.copy()
    bf_idx["date"] = pd.to_datetime(bf_idx["date"])
    bf_idx = bf_idx.set_index("date").reindex(df.index)

    sig_idx = signals.copy()
    sig_idx["date"] = pd.to_datetime(sig_idx["date"])
    sig_idx = sig_idx.set_index("date").reindex(df.index)

    # 繪製均線
    ma_palette = {
        "ma5": "#4a90e2",
        "ma10": "#f5a623",
        "ma20": "#50c878",
        "ma60": "#c0392b",
    }
    ma_cols = [col for col in ["ma5", "ma10", "ma20", "ma60"] if col in df.columns]
    for ma_col in ma_cols:
        ax.plot(xs, df[ma_col], label=ma_col.upper(), linewidth=1.4, color=ma_palette.get(ma_col, None))

    # 標記所有底分型的起點/終點（灰三角）
    bf_hits = bf_idx[bf_idx["bottom_fractal"] == "O"]
    if not bf_hits.empty:
        start_points = []
        end_points = []
        for row in bf_hits.itertuples():
            if hasattr(row, "fractal_left_date") and hasattr(row, "fractal_right_date"):
                left_date = pd.to_datetime(row.fractal_left_date)
                right_date = pd.to_datetime(row.fractal_right_date)
                if left_date in pos_map:
                    start_idx = pos_map[left_date]
                    start_points.append((start_idx, float(df.iloc[start_idx]["Low"])))
                if right_date in pos_map:
                    end_idx = pos_map[right_date]
                    end_points.append((end_idx, float(df.iloc[end_idx]["Low"])))
            else:
                center_date = pd.to_datetime(row.fractal_low_date)
                if center_date not in pos_map:
                    continue
                # 以中心位置推算起點/終點
                center_loc = df.index.get_loc(center_date)
                if isinstance(center_loc, slice):
                    center_loc = center_loc.start
                start_idx = center_loc - left
                end_idx = center_loc + right
                if start_idx >= 0:
                    start_points.append((start_idx, float(df.iloc[start_idx]["Low"])))
                if end_idx < len(df):
                    end_points.append((end_idx, float(df.iloc[end_idx]["Low"])))

        if start_points:
            end_xs = {x for x, _ in end_points} if end_points else set()
            start_points_sorted = sorted(start_points, key=lambda p: (p[0], p[1]))
            sx, sy = [], []
            start_seen = {}
            for x, y in start_points_sorted:
                offset = start_seen.get(x, 0)
                start_seen[x] = offset + 1
                sx.append(x)
                base = 0.975
                step = 0.02
                extra = 1 if x in end_xs else 0
                if offset == 0 and extra == 0:
                    sy.append(y * base)
                else:
                    sy.append(y * (base - step * (offset + extra)))
            ax.scatter(
                sx,
                sy,
                marker="^",
                color="#7f8c8d",
                alpha=0.85,
                s=90,
                label="分型起點",
                zorder=5,
            )
        if end_points:
            end_points_sorted = sorted(end_points, key=lambda p: (p[0], p[1]))
            ex, ey = [], []
            end_seen = {}
            for x, y in end_points_sorted:
                offset = end_seen.get(x, 0)
                end_seen[x] = offset + 1
                ex.append(x)
                base = 0.975
                ey.append(y * base)
            ax.scatter(
                ex,
                ey,
                marker="^",
                facecolors="none",
                edgecolors="#7f8c8d",
                alpha=0.9,
                s=110,
                label="分型終點",
                zorder=5,
            )

    ax.set_title(f"{stock_id} K線 + 均線 + 底分型", fontsize=14)
    # 調整 X 軸刻度：顯示部分日期避免擠在一起
    if len(xs) > 1:
        tick_idx = np.linspace(0, len(xs) - 1, num=10, dtype=int)
        ax.set_xticks(tick_idx)
        ax.set_xticklabels([df.index[i].strftime("%Y-%m-%d") for i in tick_idx], rotation=45, ha="right")
    ax.set_xlabel("Date")
    ax.grid(axis="y", linestyle="--", color="#e5e9f2", alpha=0.8)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color("#d0d6e2")
    ax.set_ylabel("Price")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend(loc="best")

    out_dir = os.path.join("output", "test_charts")
    os.makedirs(out_dir, exist_ok=True)
    chart_path = os.path.join(out_dir, f"{stock_id}_bottom_fractal_debug.png")
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close(fig)
    print(f"🖼️ 圖表已保存: {chart_path}")


def run(stock_id: str, days: int, left: int, right: int, tol: float):
    print(f"\n{'='*80}")
    print(f"底分型診斷：{stock_id}  最近 {days} 天  (left={left}, right={right}, tol={tol})")
    print(f"{'='*80}")

    df = load_data(stock_id, days)
    print(f"數據範圍：{df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')}  共 {len(df)} 筆")

    turning = identify_turning_points(df)
    fractals = identify_bottom_fractals(df, left=left, right=right, tol=tol)
    signals = check_bottom_fractal_higher_low(
        df,
        turning_points_df=turning,
        bottom_fractal_df=fractals,
        left=left,
        right=right,
        tol=tol,
    )

    summarize(turning, fractals, signals)
    plot_chart(stock_id, df, turning, fractals, signals, left, right)


def main():
    parser = argparse.ArgumentParser(description="底分型 + 底底高訊號診斷程式")
    parser.add_argument("--stock", type=str, default="00631L", help="股票代碼，預設 00631L")
    parser.add_argument("--days", type=int, default=180, help="近 N 天資料")
    parser.add_argument("--left", type=int, default=2, help="分型左窗口")
    parser.add_argument("--right", type=int, default=2, help="分型右窗口")
    parser.add_argument("--tol", type=float, default=0.0, help="容忍百分比 (小數)")
    args = parser.parse_args()

    try:
        run(args.stock, args.days, args.left, args.right, args.tol)
    except Exception as exc:
        print(f"❌ 無法完成診斷：{exc}")
        print("   請確認 data 檔是否存在，或改用 --stock 指定有資料的代碼，例如 00631L")


if __name__ == "__main__":
    main()
