#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TD Sequential (九轉) 測試腳本

此程式參考 test_resistance_breakthrough.py 的互動式結構,提供以下功能:
1. 讓使用者輸入股票代碼與觀察天數,並載入實際的日線資料。
2. 根據指定 comparison_offset 與 setup_length 計算 TD Sequential 買賣訊號。
3. 以圖表標記買賣訊號,並展示 setup count 的變化。
"""

from __future__ import annotations

import os
import sys
from typing import Tuple

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

# 將 src 目錄加入路徑,與 test_resistance_breakthrough.py 相同
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.buyRule.td_sequential_buy_rule import compute_td_sequential_signals


def _load_stock_dataframe(stock_id: str, days: int) -> pd.DataFrame:
    """
    載入股票資料,並確保索引為日期,欄位至少包含 Close。
    """
    from src.validate_buy_rule import load_stock_data

    df = load_stock_data(stock_id, "D")
    if df is None or df.empty:
        raise ValueError(f"無法載入股票 {stock_id} 的資料")

    if not isinstance(df.index, pd.DatetimeIndex):
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
        else:
            raise ValueError("資料無日期索引,請確認資料來源")

    df = df.sort_index()
    if days > 0:
        df = df.tail(days)

    if "Close" not in df.columns:
        raise ValueError("資料缺少 Close 欄位,無法計算 TD Sequential")

    return df


def _select_font() -> None:
    """
    與壓力線測試相同,優先嘗試常見中文字體,避免圖表顯示亂碼。
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

    # 如果系統沒有中文字體,嘗試使用 repo 中的 NotoSans 字型作為後備。
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


def _summarize_signals(result_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    分別回傳買賣訊號的資料列,並輸出摘要到終端。
    """
    buy_hits = result_df[result_df["td_buy_signal"] == "O"]
    sell_hits = result_df[result_df["td_sell_signal"] == "O"]

    if buy_hits.empty:
        print("   ➤ 未偵測到 TD Sequential 買進訊號")
    else:
        dates = ", ".join(buy_hits["date"].tolist())
        print(f"   ➤ TD 買進訊號 {len(buy_hits)} 次: {dates}")

    if sell_hits.empty:
        print("   ➤ 未偵測到 TD Sequential 賣出訊號")
    else:
        dates = ", ".join(sell_hits["date"].tolist())
        print(f"   ➤ TD 賣出訊號 {len(sell_hits)} 次: {dates}")

    return buy_hits, sell_hits


def _plot_candles(ax: plt.Axes, df: pd.DataFrame) -> None:
    """
    繪製簡化版 K 棒,若缺少 O/H/L 欄位則改為收盤線。
    """
    dates = df.index
    if {"Open", "High", "Low"}.issubset(df.columns):
        opens = df["Open"]
        highs = df["High"]
        lows = df["Low"]
        closes = df["Close"]
        bar_width = pd.Timedelta(days=0.6)
        for i, date in enumerate(dates):
            o = opens.iloc[i]
            h = highs.iloc[i]
            l = lows.iloc[i]
            c = closes.iloc[i]
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
    else:
        ax.plot(dates, df["Close"], color="steelblue", linewidth=1.5, label="Close")


def _create_td_chart(
    stock_id: str,
    price_df: pd.DataFrame,
    result_df: pd.DataFrame,
    comparison_offset: int,
    setup_length: int,
) -> None:
    """繪製價格 + 訊號 + setup count 圖表。"""
    _select_font()
    plt.figure(figsize=(15, 9))

    ax_price = plt.subplot(2, 1, 1)
    _plot_candles(ax_price, price_df)
    ax_price.set_title(
        f"{stock_id} TD Sequential 訊號 (offset={comparison_offset}, length={setup_length})",
        fontsize=15,
    )
    ax_price.set_ylabel("價格")
    ax_price.grid(True, alpha=0.3)

    # 建立字串日期 -> 實際 Timestamp 映射
    date_lookup = {idx.strftime("%Y-%m-%d"): idx for idx in price_df.index}
    buy_hits = result_df[result_df["td_buy_signal"] == "O"]
    sell_hits = result_df[result_df["td_sell_signal"] == "O"]

    def _plot_signal_markers(hits: pd.DataFrame, color: str, marker: str, label: str) -> None:
        if hits.empty:
            return
        hit_dates = [date_lookup.get(d) for d in hits["date"].tolist()]
        hit_dates = [d for d in hit_dates if d is not None]
        if not hit_dates:
            return
        prices = price_df.loc[hit_dates, "Close"]
        ax_price.scatter(
            hit_dates,
            prices,
            color=color,
            edgecolor="black",
            linewidths=1.1,
            s=60,
            marker=marker,
            label=label,
            zorder=10,
        )

    _plot_signal_markers(buy_hits, "lime", "^", "TD 買進訊號")
    _plot_signal_markers(sell_hits, "orange", "v", "TD 賣出訊號")
    ax_price.legend(loc="upper left")

    ax_setup = plt.subplot(2, 1, 2, sharex=ax_price)
    signal_dates = pd.to_datetime(result_df["date"])
    ax_setup.plot(signal_dates, result_df["td_setup_buy_count"], label="Setup Buy Count", color="green")
    ax_setup.plot(signal_dates, result_df["td_setup_sell_count"], label="Setup Sell Count", color="red")
    ax_setup.axhline(setup_length, color="gray", linestyle="--", linewidth=1, label="目標計數")
    ax_setup.set_ylabel("Setup Count")
    ax_setup.set_xlabel("日期")
    ax_setup.grid(True, alpha=0.3)
    ax_setup.legend(loc="upper left")

    plt.tight_layout()

    output_dir = "output/test_charts"
    os.makedirs(output_dir, exist_ok=True)
    chart_file = os.path.join(output_dir, f"{stock_id}_td_sequential.png")
    plt.savefig(chart_file, dpi=300, bbox_inches="tight")
    print(f"✅ 圖表已保存至: {chart_file}")

    # 部分環境 (如 CLI 測試) 使用 Agg backend,直接 show 會出現警告
    backend = plt.get_backend().lower()
    if "agg" not in backend:
        plt.show()
    else:
        plt.close()


def run_td_sequential_test(
    stock_id: str = "00631L",
    days: int = 180,
    comparison_offset: int = 2,
    setup_length: int = 9,
) -> bool:
    """主測試流程,回傳測試是否成功完成。"""
    print("\n" + "=" * 60)
    print(f"TD Sequential 測試 - 股票 {stock_id}")
    print("=" * 60)
    try:
        print("🔄 載入股票資料...")
        price_df = _load_stock_dataframe(stock_id, days)
        print(f"✅ 已載入 {len(price_df)} 筆資料 (最近 {days} 天)")
        preview = price_df.tail(min(len(price_df), 5))
        print("\n📊 價格資料預覽:")
        preview_cols = [col for col in ["Open", "High", "Low", "Close", "Volume"] if col in preview.columns]
        if preview_cols:
            print(preview[preview_cols])
        else:
            print(preview["Close"])

        print("\n🧮 計算 TD Sequential 訊號...")
        result_df = compute_td_sequential_signals(
            price_df,
            comparison_offset=comparison_offset,
            setup_length=setup_length,
            price_column="Close",
        )
        if result_df.empty:
            print("⚠️ 無資料可供計算,請確認輸入參數")
            return False

        print(result_df.tail(min(len(result_df), 10)).to_string(index=False))
        buy_hits, sell_hits = _summarize_signals(result_df)

        print("\n🎨 生成圖表...")
        _create_td_chart(stock_id, price_df, result_df, comparison_offset, setup_length)

        print("\n📈 統計資訊:")
        print(f"   最近 {len(result_df)} 根 K 棒")
        print(f"   TD 買進訊號: {len(buy_hits)} 次")
        print(f"   TD 賣出訊號: {len(sell_hits)} 次")
        return True
    except Exception as exc:  # pragma: no cover - 互動式腳本錯誤輸出
        print(f"❌ 測試發生錯誤: {exc}")
        return False


def main() -> None:
    """模仿 test_resistance_breakthrough.py 的互動式流程。"""
    print("TD Sequential (九轉) 測試工具")
    print("=" * 50)
    while True:
        stock_id = input("\n請輸入股票代碼 (預設00631L,輸入 quit 離開): ").strip()
        if stock_id.lower() == "quit":
            print("程式結束")
            break
        if not stock_id:
            stock_id = "00631L"

        days_input = input("請輸入顯示天數 (預設180): ").strip()
        try:
            days = int(days_input) if days_input else 180
        except ValueError:
            days = 180

        offset_input = input("請輸入 comparison_offset (預設2): ").strip()
        try:
            comparison_offset = int(offset_input) if offset_input else 2
        except ValueError:
            comparison_offset = 2

        length_input = input("請輸入 setup_length (預設9): ").strip()
        try:
            setup_length = int(length_input) if length_input else 9
        except ValueError:
            setup_length = 9

        print(
            f"\n開始測試 {stock_id} "
            f"(最近 {days} 天, offset={comparison_offset}, setup_length={setup_length})..."
        )
        success = run_td_sequential_test(
            stock_id=stock_id,
            days=days,
            comparison_offset=comparison_offset,
            setup_length=setup_length,
        )

        if success:
            print(f"\n🎉 {stock_id} 測試完成!")
        else:
            print(f"\n❌ {stock_id} 測試失敗!")

        cont = input("\n是否測試其他股票? (y/n): ").strip().lower()
        if cont != "y":
            break


if __name__ == "__main__":
    main()
