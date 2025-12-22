#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
將 kbar CSV 中重複的指標欄位精簡，只保留每個基礎欄位的第一個版本。

適用情境：像 009800_D.csv 這類檔案含有大量以「.1 .1.1 …」尾碼重複的欄位。
此工具會去除連續數字尾碼後判斷基礎欄位名稱，保留第一個出現者，其餘捨棄。

用法：
    python3 trim_kbar_columns.py Data/kbar/009800_D.csv
    python3 trim_kbar_columns.py Data/kbar/009800_D.csv --output Data/kbar/009800_D.trim.csv
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Dict, List, Tuple

import pandas as pd


def _base_name(col: str) -> str:
    """
    移除欄位名稱尾端的 .數字 重複標記，取得基礎名稱。
    例：'Close.1.2' -> 'Close'
    """
    return re.sub(r"(?:\.\d+)+$", "", col)


def trim_columns(input_path: str, output_path: str) -> Tuple[int, int, List[str]]:
    if not os.path.exists(input_path):
        raise FileNotFoundError(input_path)

    df = pd.read_csv(input_path, low_memory=False)
    original_cols = list(df.columns)

    seen: Dict[str, str] = {}
    keep_cols: List[str] = []
    dropped_cols: List[str] = []

    for col in original_cols:
        base = _base_name(col)
        if base not in seen:
            seen[base] = col
            keep_cols.append(col)
        else:
            dropped_cols.append(col)

    trimmed_df = df[keep_cols]
    trimmed_df.to_csv(output_path, index=False)

    return len(original_cols), len(keep_cols), dropped_cols


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="精簡 kbar CSV 重複欄位")
    parser.add_argument("input", help="原始 CSV 路徑")
    parser.add_argument(
        "--output",
        help="輸出 CSV 路徑 (預設在原檔名後加 .trim)",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    input_path = args.input
    output_path = args.output or f"{os.path.splitext(input_path)[0]}.trim.csv"

    orig_cnt, keep_cnt, dropped = trim_columns(input_path, output_path)
    print(f"輸入欄位數: {orig_cnt}")
    print(f"保留欄位數: {keep_cnt}")
    print(f"已輸出: {output_path}")
    if dropped:
        preview = ", ".join(dropped[:10])
        more = f"... 以及 {len(dropped) - 10} 個" if len(dropped) > 10 else ""
        print(f"移除欄位: {preview} {more}")


if __name__ == "__main__":
    main()
