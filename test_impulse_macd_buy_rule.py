#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Impulse MACD 買入規則測試程式

此腳本會建立一組可控的測試資料,驗證 impulse_macd_buy_rule.py 中三個買入檢查函數的行為:
1. 零線交叉買入訊號
2. 信號線交叉買入訊號
3. 綜合買入訊號 (含可選的正柱狀圖條件)

亦支援透過輸入股票代碼載入真實資料進行驗證。
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd

# 將 src 目錄加入 Python 搜尋路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.buyRule.impulse_macd_buy_rule import (
    check_impulse_macd_zero_cross_buy,
    check_impulse_macd_signal_cross_buy,
    check_impulse_macd_combined_buy,
)


def build_sample_dataframe() -> pd.DataFrame:
    """
    建立具備已知 Impulse MACD 行為的測試 DataFrame。
    日期索引採每日頻率,所有欄位皆為數值型態,確保測試結果穩定。
    """
    dates = pd.date_range('2024-01-01', periods=7, freq='D')
    data = {
        'ImpulseMACD': [-0.8, -0.2, 0.15, 0.30, 0.05, -0.10, 0.20],
        'ImpulseSignal': [-0.5, -0.1, -0.05, 0.10, 0.08, 0.00, 0.05],
        'ImpulseHistogram': [-0.3, -0.1, 0.20, 0.20, -0.03, -0.10, 0.15],
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = 'date'
    return df


def load_real_dataframe(stock_id: str, days: int) -> pd.DataFrame:
    """
    透過 load_stock_data 載入真實股票資料,並確保包含必要欄位。
    """
    from src.validate_buy_rule import load_stock_data
    from src.data_initial.calculate_impulse_macd import calculate_impulse_macd

    df = load_stock_data(stock_id, 'D')
    if df is None or df.empty:
        raise ValueError(f"無法載入股票 {stock_id} 的日線資料")

    if not isinstance(df.index, pd.DatetimeIndex):
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
        else:
            raise ValueError("載入的資料缺少日期索引,無法進行測試")

    df = df.sort_index()
    if days > 0:
        df = df.tail(days)

    required_cols = ['ImpulseMACD', 'ImpulseSignal', 'ImpulseHistogram']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"⚙️  股票 {stock_id} 缺少欄位 {missing_cols},自動計算 Impulse MACD 指標...")
        df = calculate_impulse_macd(df)
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(
                f"股票 {stock_id} 缺少必要欄位: {', '.join(missing_cols)}\n"
                "請先執行 append_indicator 產生對應指標"
            )

    return df


def assert_signal(result_df: pd.DataFrame, column: str, expected: List[str]) -> None:
    """
    確認結果欄位內容與預期一致,若不相符則拋出 AssertionError。
    """
    actual = result_df[column].tolist()
    assert actual == expected, (
        f"{column} 驗證失敗\n"
        f"  期望: {expected}\n"
        f"  實際: {actual}\n"
        f"結果 DataFrame:\n{result_df}"
    )


def summarize_signals(result_df: pd.DataFrame, column: str, label: str) -> None:
    """
    輸出指定結果欄位的觸發日期摘要。
    """
    hits = result_df[result_df[column] == 'O']
    if hits.empty:
        print(f"   ➤ 未偵測到 {label} 訊號")
    else:
        dates = ', '.join(hits['date'].tolist())
        print(f"   ➤ {label} 訊號共 {len(hits)} 次: {dates}")


def run_tests(
    stock_id: Optional[str] = None,
    days: int = 120,
    plot_chart: bool = False,
    chart_path: Optional[str] = None,
) -> None:
    """
    執行三項買入規則的整合測試並輸出結果。
    若提供 stock_id, 則以真實資料驗證; 否則使用範例資料並進行斷言。
    """
    print("=== Impulse MACD 買入規則測試 ===\n")
    if stock_id:
        try:
            df = load_real_dataframe(stock_id, days)
        except ValueError as exc:
            print(f"❌ 測試無法進行: {exc}")
            return

        print(f"📈 使用股票 {stock_id} 日線資料 (最近 {len(df)} 筆)")
        preview_len = min(len(df), 10)
        print(df.tail(preview_len).to_string())
        print()
    else:
        df = build_sample_dataframe()
        print("📊 測試資料 (含 ImpulseMACD、ImpulseSignal、ImpulseHistogram):")
        print(df)
        print()

    print("1️⃣ 測試零線交叉買入訊號...")
    zero_cross_df = check_impulse_macd_zero_cross_buy(df)
    print(zero_cross_df if not stock_id else zero_cross_df.tail(10))
    if stock_id:
        summarize_signals(zero_cross_df, 'impulse_macd_zero_cross_buy', '零線交叉')
    else:
        assert_signal(
            zero_cross_df,
            'impulse_macd_zero_cross_buy',
            ['', '', 'O', '', '', '', 'O'],
        )
        print("✅ 零線交叉測試通過")
    print()

    print("2️⃣ 測試信號線交叉買入訊號...")
    signal_cross_df = check_impulse_macd_signal_cross_buy(df)
    print(signal_cross_df if not stock_id else signal_cross_df.tail(10))
    if stock_id:
        summarize_signals(signal_cross_df, 'impulse_macd_signal_cross_buy', '信號線交叉')
    else:
        assert_signal(
            signal_cross_df,
            'impulse_macd_signal_cross_buy',
            ['', '', 'O', '', '', '', 'O'],
        )
        print("✅ 信號線交叉測試通過")
    print()

    print("3️⃣ 測試綜合買入訊號 (不限制柱狀圖)...")
    combined_df = check_impulse_macd_combined_buy(df, require_positive_histo=False)
    print(combined_df if not stock_id else combined_df.tail(10))
    if stock_id:
        summarize_signals(combined_df, 'impulse_macd_buy', '綜合買入')
    else:
        assert_signal(
            combined_df,
            'impulse_macd_buy',
            ['', '', 'O', '', '', '', 'O'],
        )
        print("✅ 綜合買入測試 (無柱狀圖限制) 通過")
    print()

    print("4️⃣ 測試綜合買入訊號 (要求柱狀圖為正)...")
    combined_positive_df = check_impulse_macd_combined_buy(df, require_positive_histo=True)
    print(combined_positive_df if not stock_id else combined_positive_df.tail(10))
    if stock_id:
        summarize_signals(combined_positive_df, 'impulse_macd_buy', '綜合買入 (柱狀圖>0)')
    else:
        assert_signal(
            combined_positive_df,
            'impulse_macd_buy',
            ['', '', 'O', '', '', '', 'O'],
        )
        print("✅ 綜合買入測試 (含柱狀圖限制) 通過")
        print("\n🎉 所有測試皆成功!")
    print()

    if stock_id and plot_chart:
        try:
            chart_file = chart_path or f"output/test_charts/impulse_macd_{stock_id}.png"
            chart_file = str(Path(chart_file).expanduser())
            Path(chart_file).parent.mkdir(parents=True, exist_ok=True)
            create_impulse_chart(
                stock_id,
                df,
                zero_cross_df,
                signal_cross_df,
                combined_df,
                combined_positive_df,
                chart_file,
            )
            print(f"🖼️  圖表已輸出: {chart_file}")
        except Exception as exc:
            print(f"⚠️  生成圖表時發生問題: {exc}")
            import traceback
            traceback.print_exc()


def create_impulse_chart(
    stock_id: str,
    df: pd.DataFrame,
    zero_cross_df: pd.DataFrame,
    signal_cross_df: pd.DataFrame,
    combined_df: pd.DataFrame,
    combined_positive_df: pd.DataFrame,
    chart_path: str,
) -> None:
    """
    建立並儲存含買入訊號的 K 線圖與 Impulse MACD 指標面板。
    """
    import mplfinance as mpf
    import matplotlib.font_manager as fm

    plot_df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    plot_df = plot_df.sort_index()

    def _signal_series(source_df: pd.DataFrame, column: str, offset: float) -> pd.Series:
        signal_dates = pd.to_datetime(source_df[source_df[column] == 'O']['date'], errors='coerce')
        signal_dates = [d for d in signal_dates if pd.notna(d) and d in plot_df.index]
        series = pd.Series(data=float('nan'), index=plot_df.index)
        if signal_dates:
            prices = plot_df.loc[signal_dates, 'Close']
            series.loc[signal_dates] = prices * offset
        return series

    addplots = []
    signal_settings = [
        ('impulse_macd_zero_cross_buy', zero_cross_df, 0.99, 'tab:green', '^', '零線交叉'),
        ('impulse_macd_signal_cross_buy', signal_cross_df, 0.97, 'tab:orange', '^', '信號線交叉'),
        ('impulse_macd_buy', combined_df, 1.02, 'tab:blue', 'o', '綜合買入'),
        ('impulse_macd_buy', combined_positive_df, 1.04, 'tab:purple', 'D', '綜合買入(柱狀圖>0)'),
    ]

    for column, source_df, offset, color, marker, label in signal_settings:
        series = _signal_series(source_df, column, offset)
        if series.notna().any():
            addplots.append(
                mpf.make_addplot(
                    series,
                    type='scatter',
                    markersize=120,
                    marker=marker,
                    color=color,
                    label=label,
                )
            )

    # Impulse MACD 面板
    if {'ImpulseMACD', 'ImpulseSignal', 'ImpulseHistogram'}.issubset(df.columns):
        impulse_panel = 1
        addplots.append(
            mpf.make_addplot(
                df['ImpulseMACD'],
                panel=impulse_panel,
                color='tab:blue',
                width=1.2,
                ylabel='Impulse MACD',
            )
        )
        addplots.append(
            mpf.make_addplot(
                df['ImpulseSignal'],
                panel=impulse_panel,
                color='tab:orange',
                width=1.0,
            )
        )
        histogram_colors = ['tab:green' if val >= 0 else 'tab:red' for val in df['ImpulseHistogram']]
        addplots.append(
            mpf.make_addplot(
                df['ImpulseHistogram'],
                type='bar',
                panel=impulse_panel,
                color=histogram_colors,
                alpha=0.6,
            )
        )
        panel_ratios = (4, 2, 1)
        volume_panel = 2
    else:
        impulse_panel = None
        panel_ratios = (4, 1)
        volume_panel = 1

    available_fonts = {f.name for f in fm.fontManager.ttflist}
    preferred_fonts = [
        'Microsoft JhengHei',
        'Microsoft YaHei',
        'SimHei',
        'PingFang TC',
        'PingFang SC',
        'Noto Sans CJK TC',
        'Noto Sans CJK SC',
        'WenQuanYi Zen Hei',
        'Source Han Sans TC',
        'Source Han Sans SC',
        'Arial Unicode MS',
    ]
    selected_font = next((font for font in preferred_fonts if font in available_fonts), 'DejaVu Sans')

    rc_kwargs = {
        'font.family': 'sans-serif',
        'font.sans-serif': [
            selected_font,
            'DejaVu Sans',
        ],
    }
    style = mpf.make_mpf_style(base_mpf_style='yahoo', rc=rc_kwargs)
    title = f"{stock_id} Impulse MACD 買入訊號"

    mpf.plot(
        plot_df,
        type='candle',
        volume=True,
        volume_panel=volume_panel,
        addplot=addplots,
        style=style,
        title=title,
        figscale=1.2,
        figratio=(16, 9),
        panel_ratios=panel_ratios,
        savefig=chart_path,
        datetime_format='%Y-%m-%d',
        tight_layout=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Impulse MACD 買入規則測試程式")
    parser.add_argument(
        '--stock',
        help="指定股票代碼,將以真實數據進行買入訊號檢測",
    )
    parser.add_argument(
        '--days',
        type=int,
        default=120,
        help="載入股票資料時取用的最近天數 (預設: 120)",
    )
    parser.add_argument(
        '--plot',
        action='store_true',
        help="輸出含買入訊號的 K 線圖",
    )
    parser.add_argument(
        '--chart-path',
        help="自訂圖表輸出路徑 (須與 --plot 搭配使用)",
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    stock_id = args.stock
    plot_chart = args.plot
    chart_path = args.chart_path

    if stock_id is None and sys.stdin.isatty():
        try:
            user_input = input("輸入股票代碼 (直接 Enter 使用內建範例資料): ").strip()
        except EOFError:
            user_input = ''
        if user_input:
            stock_id = user_input
            if not plot_chart:
                try:
                    plot_choice = input("是否輸出含買入訊號的圖表? (y/N): ").strip().lower()
                except EOFError:
                    plot_choice = 'n'
                plot_chart = plot_choice == 'y'

    if plot_chart and not chart_path and stock_id:
        chart_path = f"output/test_charts/impulse_macd_{stock_id}.png"

    run_tests(
        stock_id=stock_id,
        days=args.days,
        plot_chart=plot_chart,
        chart_path=chart_path,
    )
