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


class RiskEngine:
    """Risk calculation service for the trading system."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def calculate_portfolio_risk(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive risk metrics for the portfolio."""
        try:
            positions = portfolio_data.get('positions', [])
            market_data = portfolio_data.get('market_data', {})
            
            # Calculate basic risk metrics
            total_exposure = sum(abs(pos['quantity'] * pos.get('current_price', 0)) for pos in positions)
            
            # Calculate VaR if historical data is available
            var_95 = 0.0
            if 'historical_returns' in portfolio_data:
                returns = pd.Series(portfolio_data['historical_returns'])
                var_95 = self.historical_var(returns, confidence=0.95)
            
            # Calculate volatility
            volatility = 0.0
            if 'price_series' in portfolio_data:
                price_series = pd.Series(portfolio_data['price_series'])
                volatility = self.volatility(price_series)
            
            return {
                'total_exposure': total_exposure,
                'var_95': var_95,
                'volatility': volatility,
                'sharpe_ratio': 0.0,  # Placeholder
                'max_drawdown': 0.0   # Placeholder
            }
        except Exception as e:
            return {'error': str(e)}
    
    def aggregate_exposure(self, orders: List[Dict[str, Any]]) -> Dict[str, float]:
        """Aggregate exposure by symbol from a list of orders."""
        exposure = defaultdict(float)
        for order in orders:
            symbol = order.get('symbol', '')
            quantity = order.get('quantity', 0)
            exposure[symbol] += quantity
        return dict(exposure)
    
    def apply_stop_losses(self, positions: Dict[str, Dict[str, Any]], 
                         price_map: Dict[str, float], 
                         stop_pct: float = 0.1) -> List[Dict[str, Any]]:
        """Apply stop loss logic to positions."""
        stops_triggered = []
        for symbol, position in positions.items():
            if symbol in price_map:
                current_price = price_map[symbol]
                entry_price = position.get('avg_price', current_price)
                
                # Check for stop loss
                if current_price <= entry_price * (1 - stop_pct):
                    stops_triggered.append({
                        'symbol': symbol,
                        'action': 'SELL',
                        'quantity': position.get('quantity', 0),
                        'reason': f'Stop loss triggered at {stop_pct*100}%'
                    })
        return stops_triggered
    
    def historical_var(self, price_series: pd.Series, confidence: float = 0.95) -> float:
        """Calculate historical Value at Risk."""
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
    
    def volatility(self, price_series: pd.Series, window: int = 20) -> float:
        """Calculate rolling volatility."""
        if price_series is None or price_series.empty:
            return 0.0
        returns = price_series.pct_change().dropna().tail(window)
        if returns.empty:
            return 0.0
        vol = returns.std() * math.sqrt(252)
        return float(vol) if not math.isnan(vol) else 0.0


# Keep standalone functions for backward compatibility
def aggregate_exposure(orders: List[Dict[str, Any]]) -> Dict[str, float]:
    """Aggregate exposure by symbol from a list of orders."""
    exposure = defaultdict(float)
    for order in orders:
        symbol = order.get('symbol', '')
        quantity = order.get('quantity', 0)
        exposure[symbol] += quantity
    return dict(exposure)

def apply_stop_losses(positions: Dict[str, Dict[str, Any]], 
                     price_map: Dict[str, float], 
                     stop_pct: float = 0.1) -> List[Dict[str, Any]]:
    """Apply stop loss logic to positions."""
    stops_triggered = []
    for symbol, position in positions.items():
        if symbol in price_map:
            current_price = price_map[symbol]
            entry_price = position.get('avg_price', current_price)
            
            # Check for stop loss
            if current_price <= entry_price * (1 - stop_pct):
                stops_triggered.append({
                    'symbol': symbol,
                    'action': 'SELL',
                    'quantity': position.get('quantity', 0),
                    'reason': f'Stop loss triggered at {stop_pct*100}%'
                })
    return stops_triggered

def historical_var(price_series: pd.Series, confidence: float = 0.95) -> float:
    """Calculate historical Value at Risk."""
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
    """Calculate rolling volatility."""
    if price_series is None or price_series.empty:
        return 0.0
    returns = price_series.pct_change().dropna().tail(window)
    if returns.empty:
        return 0.0
    vol = returns.std() * math.sqrt(252)
    return float(vol) if not math.isnan(vol) else 0.0

__all__ = ["RiskEngine", "aggregate_exposure", "apply_stop_losses", "historical_var", "volatility"]
