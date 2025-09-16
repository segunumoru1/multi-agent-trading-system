from __future__ import annotations
"""Lightweight wrapper around yfinance for price history retrieval.

Designed to be side-effect free and easily mockable in tests.
"""
from typing import List, Optional
import yfinance as yf
import pandas as pd
from tools.retry import retry


@retry()
def fetch_history(symbol: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)
    df.reset_index(inplace=True)
    return df


@retry()
def fetch_batch(symbols: List[str], period: str = "1mo", interval: str = "1d") -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for s in symbols:
        df = fetch_history(s, period=period, interval=interval)
        if isinstance(df, pd.DataFrame):
            out[s] = df
    return out


__all__ = ["fetch_history", "fetch_batch"]
