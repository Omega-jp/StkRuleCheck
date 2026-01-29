#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三陽開泰 (breakthrough_san_yang_kai_tai) 規則測試工具

互動式流程與 test_td_sequential_buy_rule.py 相同風格:
- 可用內建範例資料快速驗證邏輯
- 可輸入股票代碼與顯示天數，載入真實日線資料並計算訊號
- 自動繪製 Close 與 ma5/ma10/ma20 折線，標記買進訊號
"""

from __future__ import annotations

import os
import sys
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager as fm

# 將 src 目錄加入搜尋路徑，與其他測試腳本一致
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.buyRule.breakthrough_san_yang_kai_tai import check_san_yang_kai_tai


def _build_sample_dataframe() -> pd.DataFrame:
    """
    建立一組包含 Close 與 ma5/ma10/ma20 的測試資料。
    第三根 K 棒會同時突破三條均線, 最後一根示範再次站回均線的命中。
    """
    dates = pd.date_range("2024-01-01", periods=8, freq="D")
    data = {
        "Close": [9.0, 9.1, 10.0, 9.7, 9.5, 9.4, 9.8, 10.2],
        "ma5": [10.0, 9.5, 9.6, 9.8, 9.7, 9.6, 9.7, 9.9],
        "ma10": [10.2, 9.7, 9.6, 9.9, 9.8, 9.7, 9.8, 9.9],
        "ma20": [10.4, 9.9, 9.6, 10.0, 9.9, 9.8, 9.9, 10.0],
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = "date"
    return df


def _ensure_mas(df: pd.DataFrame) -> pd.DataFrame:
    """
    確保存在 ma5/ma10/ma20 欄位，不足則以收盤價 rolling 生成。
    """
    df = df.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
        else:
            raise ValueError("資料缺少日期索引，無法計算均線")

    df = df.sort_index()
    for window in (5, 10, 20):
        col = f"ma{window}"
        if col not in df.columns:
            df[col] = df["Close"].rolling(window=window, min_periods=window).mean()
    return df


def _load_stock_dataframe(stock_id: str, days: int) -> pd.DataFrame:
    """
    透過 load_stock_data 載入日線資料並補齊均線欄位。
    """
    from src.validate_buy_rule import load_stock_data

    df = load_stock_data(stock_id, "D")
    if df is None or df.empty:
        raise ValueError(f"無法載入股票 {stock_id} 的資料")

    if "Close" not in df.columns:
        raise ValueError("資料缺少 Close 欄位,無法計算三陽開泰")

    df = _ensure_mas(df)
    if days > 0:
        df = df.tail(days)
    return df


def _select_font() -> None:
    """
    與其他測試腳本一致: 優先使用系統中文字體，再嘗試隨附的 NotoSans。
    """
    preferred_fonts = ["Microsoft JhengHei", "Arial Unicode MS", "SimHei"]
    for font_name in preferred_fonts:
        try:
            fm.findfont(font_name, fallback_to_default=False)
            plt.rcParams["font.sans-serif"] = [font_name]
            plt.rcParams["axes.unicode_minus"] = False
            return
        except ValueError:
            continue

    fallback_font = os.path.join(
        os.path.dirname(__file__),
        "assets",
        "fonts",
        "NotoSansCJKtc-Regular.otf",
    )
    if os.path.exists(fallback_font):
        try:
            fm.fontManager.addfont(fallback_font)
            font_prop = fm.FontProperties(fname=fallback_font)
            plt.rcParams["font.sans-serif"] = [font_prop.get_name()]
        except Exception as exc:
            print(f"⚠️ 無法載入後備字型: {exc}")

    plt.rcParams["axes.unicode_minus"] = False


def _summarize_signals(result_df: pd.DataFrame) -> List[str]:
    """
    回傳買訊日期列表，並在終端輸出摘要。
    """
    hits = result_df[result_df["san_yang_kai_tai_check"] == "O"]
    if hits.empty:
        print("   ➤ 未偵測到三陽開泰買進訊號")
        return []

    dates = hits["date"].tolist()
    print(f"   ➤ 三陽開泰買進訊號 {len(dates)} 次: {', '.join(dates)}")
    return dates


def _plot_candles(ax: plt.Axes, df: pd.DataFrame) -> None:
    """
    若有 OHLC 資料則畫簡易 K 線, 否則退回收盤線。
    """
    dates = df.index
    # 先畫收盤線，確保缺 OHLC 時也有連續走勢
    ax.plot(dates, df["Close"], label="Close", color="black", linewidth=1.2)

    if not {"Open", "High", "Low"}.issubset(df.columns):
        return

    ohlc = df[["Open", "High", "Low", "Close"]].dropna()
    if ohlc.empty:
        return

    bar_width = pd.Timedelta(days=0.6)
    for date, row in ohlc.iterrows():
        o = row["Open"]
        h = row["High"]
        l = row["Low"]
        c = row["Close"]
        is_up = c >= o
        ax.plot([date, date], [l, h], color="black", linewidth=0.8, alpha=0.8)
        body_bottom = min(o, c)
        body_height = abs(c - o) or 0.01
        color = "white" if is_up else "green"
        edge = "red" if is_up else "green"
        rect = plt.Rectangle(
            (date - bar_width / 2, body_bottom),
            bar_width,
            body_height,
            facecolor=color,
            edgecolor=edge,
            linewidth=1.0,
            alpha=0.9,
        )
        ax.add_patch(rect)


def _create_chart(
    stock_id: str,
    df: pd.DataFrame,
    result_df: pd.DataFrame,
    save_chart: bool = True,
) -> None:
    """
    繪製 Close 與三條均線，並標示買訊。
    """
    _select_font()
    plt.figure(figsize=(14, 8))
    ax = plt.gca()

    dates = df.index
    _plot_candles(ax, df)
    for col, color in (("ma5", "green"), ("ma10", "orange"), ("ma20", "purple")):
        if col in df.columns:
            ax.plot(dates, df[col], label=col, linewidth=1.1, alpha=0.8, color=color)

    date_lookup = {idx.strftime("%Y-%m-%d"): idx for idx in df.index}
    hits = result_df[result_df["san_yang_kai_tai_check"] == "O"]
    if not hits.empty:
        hit_dates = [date_lookup.get(d) for d in hits["date"].tolist()]
        hit_dates = [d for d in hit_dates if d is not None]
        if hit_dates:
            price_range = df["Close"].max() - df["Close"].min()
            base_padding = max(price_range * 0.01, 0.1)
            if {"High", "Low"}.issubset(df.columns):
                candle_span = (df.loc[hit_dates, "High"] - df.loc[hit_dates, "Low"]).abs().fillna(0)
                y_vals = df.loc[hit_dates, "High"] + base_padding + candle_span * 0.3
            else:
                y_vals = df.loc[hit_dates, "Close"] + base_padding
            ax.scatter(
                hit_dates,
                y_vals,
                color="lime",
                edgecolor="black",
                s=60,
                marker="v",
                zorder=10,
                label="買進訊號",
            )

    ax.set_title(f"{stock_id} 三陽開泰訊號", fontsize=15)
    ax.set_xlabel("日期")
    ax.set_ylabel("價格")
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()

    if not save_chart:
        plt.close()
        return

    output_dir = "output/test_charts"
    os.makedirs(output_dir, exist_ok=True)
    chart_file = os.path.join(output_dir, f"{stock_id}_san_yang_kai_tai.png")
    plt.savefig(chart_file, dpi=300, bbox_inches="tight")
    print(f"✅ 圖表已保存至: {chart_file}")

    plt.close()


def _run_with_dataframe(
    stock_id: str,
    df: pd.DataFrame,
    preview_rows: int = 6,
    save_chart: bool = True,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    核心計算流程，回傳結果與命中日期。
    """
    print(f"✅ 已載入 {len(df)} 筆資料")
    preview = df.tail(min(len(df), preview_rows))
    print("\n📊 價格資料預覽:")
    preview_cols = [col for col in ["Close", "ma5", "ma10", "ma20"] if col in preview.columns]
    print(preview[preview_cols])

    print("\n🧮 計算三陽開泰訊號...")
    result_df = check_san_yang_kai_tai(df)
    if result_df.empty:
        raise ValueError("無可供計算的資料列")

    print(result_df.tail(min(len(result_df), 10)).to_string(index=False))
    hits = _summarize_signals(result_df)

    print("\n🎨 生成圖表...")
    _create_chart(stock_id, df, result_df, save_chart=save_chart)
    return result_df, hits


def run_san_yang_kai_tai_test(
    stock_id: Optional[str] = None,
    days: int = 180,
) -> bool:
    """
    主測試流程，stock_id 為 None 時使用內建範例資料。
    """
    print("\n" + "=" * 60)
    title = "內建範例資料" if not stock_id else f"股票 {stock_id}"
    print(f"三陽開泰 測試 - {title}")
    print("=" * 60)
    try:
        if stock_id:
            df = _load_stock_dataframe(stock_id, days)
        else:
            df = _build_sample_dataframe()
        df = _ensure_mas(df)
        save_chart = bool(stock_id)
        _, hits = _run_with_dataframe(stock_id or "sample", df, save_chart=save_chart)

        print("\n📈 統計資訊:")
        print(f"   最近 {len(df)} 根 K 棒")
        print(f"   三陽開泰買進訊號: {len(hits)} 次")
        return True
    except Exception as exc:  # pragma: no cover - 互動式腳本錯誤輸出
        print(f"❌ 測試發生錯誤: {exc}")
        return False


def main() -> None:
    """
    互動式流程，模仿 test_td_sequential_buy_rule.py。
    """
    print("三陽開泰 規則測試工具")
    print("=" * 50)
    while True:
        stock_id_input = input("\n請輸入股票代碼 (輸入 sample 使用內建資料, quit 離開): ").strip()
        if stock_id_input.lower() == "quit":
            print("程式結束")
            break
        stock_id = None if stock_id_input.lower() == "sample" else stock_id_input or "00631L"

        days_input = input("請輸入顯示天數 (預設180): ").strip()
        try:
            days = int(days_input) if days_input else 180
        except ValueError:
            days = 180

        label = "內建資料" if stock_id is None else f"{stock_id} (最近 {days} 天)"
        print(f"\n開始測試 {label} ...")
        success = run_san_yang_kai_tai_test(stock_id=stock_id, days=days)
        if success:
            print(f"\n🎉 {label} 測試完成!")
        else:
            print(f"\n❌ {label} 測試失敗!")

        cont = input("\n是否測試其他股票? (y/n): ").strip().lower()
        if cont != "y":
            break


if __name__ == "__main__":
    main()
