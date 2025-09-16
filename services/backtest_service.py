from __future__ import annotations
"""Backtesting service.

Provides a minimal framework to evaluate a list of executed orders against
historical price series and compute basic performance metrics.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Mapping, Optional
import pandas as pd
import math


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    trades: List[Dict[str, Any]]
    sharpe: float
    max_drawdown: float
    total_commission: float = 0.0
    total_slippage_cost: float = 0.0
    total_notional: float = 0.0
    total_trades: int = 0
    average_cost_bps: float = 0.0  # (commission+slip)/notional * 1e4
    gross_exposure_peak: float = 0.0


def _compute_sharpe(returns: pd.Series, risk_free: float = 0.0) -> float:
    if returns.empty:
        return 0.0
    excess = returns - risk_free / len(returns)
    std = excess.std()
    if std == 0 or math.isnan(std):
        return 0.0
    return (excess.mean() / std) * (252 ** 0.5)


def _compute_max_drawdown(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    roll_max = equity.cummax()
    dd = (equity - roll_max) / roll_max
    return float(dd.min())


def backtest(
    price_df: pd.DataFrame,
    orders: List[Dict[str, Any]],
    commission_pct: float = 0.0005,
    slippage_bps: int = 5,
    participation_cap: Optional[float] = None,  # max fraction of synthetic bar volume
    base_spread_bps: int = 2,  # used if modeling partial fills to adjust effective price baseline
    impact_coef: float = 0.0,  # coefficient for market impact based on cumulative participation
    impact_model: str = "linear",  # linear | sqrt | power
    impact_power: float = 0.5,  # exponent if impact_model == 'power'
) -> BacktestResult:
    """Very simplified backtest engine with optional transaction costs.

    Assumptions:
    - All orders executed at close price of the day they appear (with slippage adjustment).
    - Single symbol per provided DataFrame; 'Close' column required.
    - Commission (percentage of notional) and slippage (bps) applied if non-zero.
    """
    if price_df.empty or 'Close' not in price_df.columns:
        raise ValueError("price_df must contain Close column")
    # Normalize index to datetime
    price_df = price_df.copy()
    if not isinstance(price_df.index, pd.DatetimeIndex):
        if 'Date' in price_df.columns:
            price_df = price_df.set_index(pd.to_datetime(price_df['Date']))
        else:
            raise ValueError("price_df must have a DatetimeIndex or a 'Date' column")

    position = 0
    cash = 100000.0
    trades: List[Dict[str, Any]] = []
    equity_values = []
    slip = slippage_bps / 10000.0
    gross_exposure_peak = 0.0
    cumulative_participation = 0.0  # fraction of cumulative volume we've represented
    cum_volume = 0.0
    for date, row in price_df.iterrows():
        bar_volume = float(row.get('Volume', 1.0)) if participation_cap else None
        # Execute any orders for this date (toy: all at same symbol)
        todays_orders: List[Dict[str, Any]] = []
        for o in orders:
            ts_val = o.get('timestamp')
            if ts_val is None:
                continue
            try:
                o_dt = pd.to_datetime(ts_val)
            except Exception:  # noqa: BLE001
                continue
            if o_dt <= date:
                todays_orders.append(o)
        for o in todays_orders:
            if o.get('_executed'):
                continue
            side = o['side']
            original_qty = int(o['qty'])
            remaining = int(o.get('_remaining', original_qty))
            # Partial fill sizing
            if participation_cap and bar_volume and bar_volume > 0:
                max_bar_qty = max(1, int(bar_volume * participation_cap))
                fill_qty = min(remaining, max_bar_qty)
            else:
                fill_qty = remaining
            price = float(row['Close'])
            # Include base spread if partial fill mode enabled
            spread_adj = 0.0
            if participation_cap:
                spread_adj = (base_spread_bps / 10000.0) * price * (1 if side == 'BUY' else -1)
            effective_price = price + spread_adj
            effective_price = effective_price * (1 + slip) if side == 'BUY' else effective_price * (1 - slip)
            # Track cumulative volume (if volume present)
            if bar_volume and bar_volume > 0:
                cum_volume += bar_volume
            impact = 0.0
            prev_abs_qty = 0.0
            if impact_coef > 0 and cum_volume > 0:
                prev_abs_qty = cumulative_participation * cum_volume
                prospective_participation = (prev_abs_qty + fill_qty) / cum_volume
                if impact_model == 'sqrt':
                    scale = prospective_participation ** 0.5
                elif impact_model == 'power':
                    scale = prospective_participation ** max(1e-6, impact_power)
                else:  # linear
                    scale = prospective_participation
                impact = impact_coef * scale * price
                effective_price = effective_price + (impact if side == 'BUY' else -impact)
            notional = fill_qty * effective_price
            commission = notional * commission_pct
            if side == 'BUY':
                cash -= notional + commission
                position += fill_qty
            else:  # SELL
                cash += notional - commission
                position -= fill_qty
            remaining_after = remaining - fill_qty
            if remaining_after > 0:
                o['_remaining'] = remaining_after
            else:
                o['_executed'] = True
            trades.append({
                'date': date,
                'side': side,
                'qty': fill_qty,
                'price': price,
                'effective_price': effective_price,
                'commission': commission,
                'slippage_bps': slippage_bps,
                'remaining': max(0, remaining_after),
                'original_qty': original_qty,
                'impact_applied': impact,
                'position_after': position,
                'cash_after': cash,
            })
            # Update cumulative participation after applying fill
            if bar_volume and bar_volume > 0 and cum_volume > 0:
                cumulative_participation = min(1.0, (prev_abs_qty + fill_qty) / cum_volume)
        # Mark-to-market
        mtm = position * float(row['Close'])
        equity = cash + mtm
        equity_values.append((date, equity))
        gross_exposure_peak = max(gross_exposure_peak, abs(position) * float(row['Close']))

    equity_series = pd.Series([v for _, v in equity_values], index=[d for d, _ in equity_values])
    returns = equity_series.pct_change().dropna()
    sharpe = _compute_sharpe(returns)
    max_dd = _compute_max_drawdown(equity_series)
    total_commission = sum(t.get('commission', 0.0) for t in trades)
    # Slippage cost per trade approximated as difference between effective and mid (here close) * qty
    total_slip_cost = 0.0
    for t in trades:
        px = t.get('price')
        epx = t.get('effective_price')
        qty = t.get('qty', 0)
        if px is not None and epx is not None:
            # For buys effective > price (cost), for sells effective < price (cost as price-epx)
            if t.get('side') == 'BUY':
                total_slip_cost += (epx - px) * qty
            else:
                total_slip_cost += (px - epx) * qty
    total_notional = sum((t.get('effective_price', 0.0) or 0.0) * t.get('qty', 0) for t in trades)
    total_trades = len(trades)
    avg_cost_bps = 0.0
    if total_notional > 0:
        avg_cost_bps = ((total_commission + total_slip_cost) / total_notional) * 10000.0
    return BacktestResult(
        equity_curve=equity_series,
        trades=trades,
        sharpe=sharpe,
        max_drawdown=max_dd,
        total_commission=total_commission,
        total_slippage_cost=total_slip_cost,
        total_notional=total_notional,
        total_trades=total_trades,
        average_cost_bps=avg_cost_bps,
        gross_exposure_peak=gross_exposure_peak,
    )


def multi_backtest(
    price_map: Mapping[str, pd.DataFrame],
    orders: List[Dict[str, Any]],
    commission_pct: float = 0.0005,
    slippage_bps: int = 5,
    participation_cap: Optional[float] = None,
    base_spread_bps: int = 2,
    impact_coef: float = 0.0,
    impact_model: str = 'linear',
    impact_power: float = 0.5,
) -> BacktestResult:
    """Multi-symbol backtest aggregating equity across symbols with optional costs.

    price_map: symbol -> DataFrame with Close column & DateTimeIndex (or 'Date' column).
    Orders must include symbol field.
    Costs: commission_pct * notional and slippage_bps modify effective execution price.
    """
    # Normalize all indices & align dates
    norm = {}
    for sym, df in price_map.items():
        if df is None or df.empty or 'Close' not in df.columns:
            continue
        local = df.copy()
        if not isinstance(local.index, pd.DatetimeIndex):
            if 'Date' in local.columns:
                local = local.set_index(pd.to_datetime(local['Date']))
            else:
                continue
        norm[sym] = local[['Close']]
    if not norm:
        raise ValueError("No valid price data provided")
    # Master calendar
    all_dates = sorted(set().union(*[df.index for df in norm.values()]))
    cash = 100000.0
    positions: Dict[str, int] = {s: 0 for s in norm.keys()}
    trades: List[Dict[str, Any]] = []
    equity_points: List[tuple] = []
    # Pre-group orders by symbol for efficiency
    sym_orders: Dict[str, List[Dict[str, Any]]] = {}
    for o in orders:
        sym = o.get('symbol')
        if not isinstance(sym, str):
            continue
        sym_orders.setdefault(sym, []).append(o)
    slip = slippage_bps / 10000.0
    gross_exposure_peak = 0.0
    cumulative_participation: Dict[str, float] = {s: 0.0 for s in norm}
    cum_volume: Dict[str, float] = {s: 0.0 for s in norm}
    for date in all_dates:
        # Execute orders with timestamp <= date
        for sym, olist in sym_orders.items():
            sym_df = norm.get(sym)
            if sym_df is None:
                continue
            mask = sym_df.index <= date
            if not mask.any():
                continue
            today_px_row = sym_df.loc[mask].tail(1)
            if today_px_row.empty:
                continue
            price = float(today_px_row.iloc[-1]['Close'])
            for o in olist:
                if o.get('_executed'):
                    continue
                ts = o.get('timestamp')
                try:
                    ts_dt = pd.to_datetime(ts) if ts is not None else None
                except Exception:
                    ts_dt = None
                if ts_dt and ts_dt <= date:
                    side = o['side']
                    original_qty = int(o['qty'])
                    remaining = int(o.get('_remaining', original_qty))
                    bar_volume = float(today_px_row.get('Volume', 1.0)) if participation_cap else None
                    if participation_cap and bar_volume and bar_volume > 0:
                        max_bar_qty = max(1, int(bar_volume * participation_cap))
                        fill_qty = min(remaining, max_bar_qty)
                    else:
                        fill_qty = remaining
                    spread_adj = 0.0
                    if participation_cap:
                        spread_adj = (base_spread_bps / 10000.0) * price * (1 if side == 'BUY' else -1)
                    effective_price = price + spread_adj
                    effective_price = effective_price * (1 + slip) if side == 'BUY' else effective_price * (1 - slip)
                    if bar_volume and bar_volume > 0:
                        cum_volume[sym] += bar_volume
                    impact = 0.0
                    prev_abs_qty = 0.0
                    if impact_coef > 0 and cum_volume[sym] > 0:
                        prev_abs_qty = cumulative_participation[sym] * cum_volume[sym]
                        prospective = (prev_abs_qty + fill_qty) / cum_volume[sym]
                        if impact_model == 'sqrt':
                            scale = prospective ** 0.5
                        elif impact_model == 'power':
                            scale = prospective ** max(1e-6, impact_power)
                        else:
                            scale = prospective
                        impact = impact_coef * scale * price
                        effective_price = effective_price + (impact if side == 'BUY' else -impact)
                    notional = fill_qty * effective_price
                    commission = notional * commission_pct
                    if side == 'BUY':
                        cash -= notional + commission
                        positions[sym] += fill_qty
                    else:
                        cash += notional - commission
                        positions[sym] -= fill_qty
                    remaining_after = remaining - fill_qty
                    if remaining_after > 0:
                        o['_remaining'] = remaining_after
                    else:
                        o['_executed'] = True
                    trades.append({
                        'date': date,
                        'symbol': sym,
                        'side': side,
                        'qty': fill_qty,
                        'price': price,
                        'effective_price': effective_price,
                        'commission': commission,
                        'slippage_bps': slippage_bps,
                        'cash_after': cash,
                        'position_after': positions[sym],
                        'remaining': max(0, remaining_after),
                        'original_qty': original_qty,
                        'impact_applied': impact,
                    })
                    if bar_volume and bar_volume > 0 and cum_volume[sym] > 0:
                        cumulative_participation[sym] = min(1.0, (prev_abs_qty + fill_qty) / cum_volume[sym])
        # Mark-to-market aggregated
        mtm = 0.0
        for sym, qty in positions.items():
            if qty == 0:
                continue
            sym_df = norm[sym]
            px_row = sym_df.loc[sym_df.index <= date].tail(1)
            if px_row.empty:
                continue
            mtm += qty * float(px_row.iloc[-1]['Close'])
        equity_value = cash + mtm
        equity_points.append((date, equity_value))
        # Gross exposure = sum |qty * price|
        gross_exp = 0.0
        for s, q in positions.items():
            if q == 0:
                continue
            px_row = norm[s].loc[norm[s].index <= date].tail(1)
            if px_row.empty:
                continue
            gross_exp += abs(q) * float(px_row.iloc[-1]['Close'])
        gross_exposure_peak = max(gross_exposure_peak, gross_exp)
    equity_series = pd.Series([v for _, v in equity_points], index=[d for d, _ in equity_points])
    returns = equity_series.pct_change().dropna()
    sharpe = _compute_sharpe(returns)
    max_dd = _compute_max_drawdown(equity_series)
    total_commission = sum(t.get('commission', 0.0) for t in trades)
    total_slip_cost = 0.0
    for t in trades:
        px = t.get('price')
        epx = t.get('effective_price')
        qty = t.get('qty', 0)
        if px is not None and epx is not None:
            if t.get('side') == 'BUY':
                total_slip_cost += (epx - px) * qty
            else:
                total_slip_cost += (px - epx) * qty
    total_notional = sum((t.get('effective_price', 0.0) or 0.0) * t.get('qty', 0) for t in trades)
    total_trades = len(trades)
    avg_cost_bps = 0.0
    if total_notional > 0:
        avg_cost_bps = ((total_commission + total_slip_cost) / total_notional) * 10000.0
    return BacktestResult(
        equity_curve=equity_series,
        trades=trades,
        sharpe=sharpe,
        max_drawdown=max_dd,
        total_commission=total_commission,
        total_slippage_cost=total_slip_cost,
        total_notional=total_notional,
        total_trades=total_trades,
        average_cost_bps=avg_cost_bps,
        gross_exposure_peak=gross_exposure_peak,
    )


__all__ = ["backtest", "multi_backtest", "BacktestResult"]
