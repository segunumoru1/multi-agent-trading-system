from __future__ import annotations
"""Risk engine service.

Provides portfolio exposure aggregation and simple stop logic utilities.
This is intentionally lightweight; can evolve toward more sophisticated
risk models (VaR, volatility targeting, etc.).
"""
from typing import List, Dict, Any
import pandas as pd
import math
from collections import defaultdict


def aggregate_exposure(orders: List[Dict[str, Any]]) -> Dict[str, float]:
    exposure: Dict[str, float] = defaultdict(float)
    for o in orders:
        qty = float(o.get("qty", 0))
        side = o.get("side")
        if side == "SELL":
            qty = -qty
        exposure[o.get("symbol", "?")] += qty
    return dict(exposure)


def apply_stop_losses(positions: Dict[str, Dict[str, Any]], price_map: Dict[str, float], stop_pct: float = 0.1) -> List[Dict[str, Any]]:
    """Return list of close orders for positions breaching stop percentage.

    positions: symbol -> {"avg_price": float, "qty": int}
    price_map: symbol -> current_price
    stop_pct: fraction (0.1 == 10%)
    """
    closes: List[Dict[str, Any]] = []
    for sym, pos in positions.items():
        avg = pos.get("avg_price")
        qty = pos.get("qty", 0)
        if not qty:
            continue
        cur = price_map.get(sym)
        if cur is None or avg is None:
            continue
        drawdown = (avg - cur) / avg if avg else 0
        if drawdown >= stop_pct:
            closes.append({"symbol": sym, "side": "SELL" if qty > 0 else "BUY", "qty": abs(qty), "reason": "STOP"})
    return closes


__all__ = ["aggregate_exposure", "apply_stop_losses"]
def historical_var(price_series: pd.Series, confidence: float = 0.95) -> float:
    if price_series is None or price_series.empty:
        return 0.0
    returns = price_series.pct_change().dropna()
    if returns.empty:
        return 0.0
    sorted_returns = returns.sort_values()
    index = int((1 - confidence) * len(sorted_returns))
    if index < 0:
        index = 0
    var = -sorted_returns.iloc[index]
    return float(var)


def volatility(price_series: pd.Series, window: int = 20) -> float:
    if price_series is None or price_series.empty:
        return 0.0
    returns = price_series.pct_change().dropna().tail(window)
    if returns.empty:
        return 0.0
    vol = returns.std() * math.sqrt(252)
    return float(vol) if not math.isnan(vol) else 0.0


__all__ += ["historical_var", "volatility"]
