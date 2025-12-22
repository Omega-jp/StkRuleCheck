#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查各股票資料檔是否缺少時間戳記。

以 baseline 股票 (預設 00631L) 的資料檔為完整樣本，對比同頻率的其他檔案，
列出少掉哪些日期 (或時間)。

用法:
    python3 check_missing_timestamps.py
    python3 check_missing_timestamps.py --suffix D --baseline 00631L --data-dir Data/kbar
"""

from __future__ import annotations

import argparse
import os
from typing import Iterable, List, Optional, Set, Tuple

import pandas as pd


def _detect_ts_column(columns: Iterable[str]) -> str:
    """
    在欄位中找出代表時間戳的欄位名稱，找不到則回傳第一個欄位。
    """
    candidates = ["ts", "timestamp", "datetime", "date", "time"]
    lowered = [c.lower() for c in columns]
    for name in candidates:
        if name in lowered:
            idx = lowered.index(name)
            return list(columns)[idx]
    return list(columns)[0]


def _load_timestamps(path: str) -> List[pd.Timestamp]:
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    # 只讀取時間欄位即可
    tmp_df = pd.read_csv(path, nrows=0)
    ts_col = _detect_ts_column(tmp_df.columns)
    df = pd.read_csv(path, usecols=[ts_col])
    ts_series = pd.to_datetime(df[ts_col], errors="coerce").dropna()
    # 如果只有日期，normalize 也不影響有時間戳的比對
    return sorted(ts_series.unique())


def _summarize_missing(
    baseline_ts: List[pd.Timestamp], target_ts: List[pd.Timestamp]
) -> Tuple[Set[pd.Timestamp], Set[pd.Timestamp]]:
    baseline_set = set(baseline_ts)
    target_set = set(target_ts)
    missing = baseline_set - target_set
    extras = target_set - baseline_set
    return missing, extras


def check_all(
    data_dir: str,
    suffix: str,
    baseline: str,
    limit: int = 10,
) -> None:
    baseline_path = os.path.join(data_dir, f"{baseline}_{suffix}.csv")
    print(f"載入基準檔: {baseline_path}")
    baseline_ts = _load_timestamps(baseline_path)
    print(f"   時間戳總數: {len(baseline_ts)}\n")

    # 找出同 suffix 的其他檔案
    candidates = [
        fname
        for fname in os.listdir(data_dir)
        if fname.endswith(f"_{suffix}.csv") and not fname.startswith(baseline)
    ]
    if not candidates:
        print("未找到其他對比檔案。")
        return

    for fname in sorted(candidates):
        target_path = os.path.join(data_dir, fname)
        stock_id = fname.rsplit("_", 1)[0]
        try:
            target_ts = _load_timestamps(target_path)
        except Exception as exc:
            print(f"{stock_id}: 讀取失敗 -> {exc}")
            continue

        missing, extras = _summarize_missing(baseline_ts, target_ts)
        status = "✅ 無缺漏" if not missing else f"⚠️ 缺 {len(missing)} 筆"
        print(f"{stock_id}: {status}")
        if missing:
            preview = sorted(missing)[:limit]
            print("   缺少時間戳:", ", ".join(ts.strftime("%Y-%m-%d %H:%M:%S") for ts in preview))
            if len(missing) > limit:
                print(f"   ... 以及其他 {len(missing) - limit} 筆")
        if extras:
            preview = sorted(extras)[:limit]
            print("   額外時間戳:", ", ".join(ts.strftime("%Y-%m-%d %H:%M:%S") for ts in preview))
            if len(extras) > limit:
                print(f"   ... 以及其他 {len(extras) - limit} 筆")
        print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="檢查資料檔的時間戳缺漏")
    parser.add_argument("--data-dir", default="Data/kbar", help="資料目錄 (預設: Data/kbar)")
    parser.add_argument("--suffix", default="D", help="檔名頻率尾碼，如 D/W/Raw (預設: D)")
    parser.add_argument("--baseline", default="00631L", help="基準股票代碼 (預設: 00631L)")
    parser.add_argument(
        "--limit", type=int, default=10, help="每檔缺漏/額外時間戳預覽數量 (預設: 10)"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    check_all(
        data_dir=args.data_dir,
        suffix=args.suffix,
        baseline=args.baseline,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
