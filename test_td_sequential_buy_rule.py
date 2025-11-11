#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

import pandas as pd

from src.buyRule.td_sequential_buy_rule import (
    compute_td_sequential_signals,
    check_td_sequential_buy_rule,
)


def _build_df(values):
    dates = pd.date_range("2024-01-01", periods=len(values), freq="D")
    return pd.DataFrame({"Close": values}, index=dates)


class TDSequentialBuyRuleTests(unittest.TestCase):
    def test_td_sequential_generates_buy_signal_with_offset_two(self):
        closes = [12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        df = _build_df(closes)

        result = compute_td_sequential_signals(df, comparison_offset=2, setup_length=9)

        buy_signals = result[result["td_buy_signal"] == "O"]
        self.assertEqual(len(buy_signals), 1)
        self.assertEqual(buy_signals.iloc[0]["date"], "2024-01-11")
        self.assertEqual(buy_signals.iloc[0]["td_setup_buy_count"], 9)

    def test_td_sequential_generates_sell_signal_with_offset_two(self):
        closes = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        df = _build_df(closes)

        result = compute_td_sequential_signals(df, comparison_offset=2, setup_length=9)

        sell_signals = result[result["td_sell_signal"] == "O"]
        self.assertEqual(len(sell_signals), 1)
        self.assertEqual(sell_signals.iloc[0]["date"], "2024-01-11")
        self.assertEqual(sell_signals.iloc[0]["td_setup_sell_count"], 9)

    def test_missing_close_column_raises_value_error(self):
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        df = pd.DataFrame({"Open": [1, 2, 3]}, index=dates)

        with self.assertRaises(ValueError):
            compute_td_sequential_signals(df)

    def test_check_wrapper_returns_standard_columns(self):
        closes = [5, 4, 3, 2, 1, 0, -1, -2, -3, -4, -5]
        df = _build_df(closes)

        wrapper_df = check_td_sequential_buy_rule(df, comparison_offset=2, setup_length=4)
        self.assertIn("td_sequential_buy_check", wrapper_df.columns)
        last_signal = wrapper_df[wrapper_df["td_sequential_buy_check"] == "O"]
        self.assertFalse(last_signal.empty)


if __name__ == "__main__":
    unittest.main()
