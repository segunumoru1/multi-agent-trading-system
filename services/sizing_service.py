from __future__ import annotations
"""Position sizing utilities.

Provides:
 - rolling_volatility: estimates annualized volatility from price history
 - compute_position_size: converts signal confidence & volatility into size pct

This is intentionally simple and can be extended to Kelly, risk parity, etc.
"""
from typing import Optional
import pandas as pd
import math


def rolling_volatility(price_series: pd.Series, window: int = 20) -> float:
    if price_series is None or price_series.empty or len(price_series) < 2:
        return 0.0
    returns = price_series.pct_change().dropna()
    if returns.empty:
        return 0.0
    windowed = returns.tail(window)
    vol = windowed.std() * math.sqrt(252)
    if math.isnan(vol):
        return 0.0
    return float(vol)


def compute_position_size(
    confidence: float,
    volatility: float,
    max_pct: float,
    target_risk_vol: float = 0.25,
    min_pct: float = 0.01,
) -> float:
    """Compute position size percentage of equity.

    Heuristic:
      base = confidence scaled into [min_pct, max_pct]
      vol_adjust = target_risk_vol / (volatility or target_risk_vol)
      final = base * min(1.5, max(0.25, vol_adjust))
      clipped to [min_pct, max_pct]
    """
    confidence = max(0.0, min(1.0, confidence or 0.0))
    base = min_pct + (max_pct - min_pct) * confidence
    if volatility <= 0:
        return min(base, max_pct)
    vol_adjust = (target_risk_vol / volatility)
    scale = min(1.5, max(0.25, vol_adjust))
    final = base * scale
    return max(min_pct, min(max_pct, final))


__all__ = ["rolling_volatility", "compute_position_size"]
