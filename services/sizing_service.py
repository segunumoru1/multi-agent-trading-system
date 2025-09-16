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


class SizingService:
    """Position sizing service for the trading system."""
    
    def __init__(self, config: dict):
        self.config = config
    
    def calculate_position_size(self, account_balance: float, 
                               risk_tolerance: float, 
                               market_data: dict) -> float:
        """Calculate optimal position size based on account balance and risk tolerance."""
        try:
            # Get volatility from market data
            volatility = market_data.get('volatility', 0.2)  # Default 20% volatility
            
            # Get confidence from market data
            confidence = market_data.get('confidence', 0.5)  # Default 50% confidence
            
            # Use the existing function
            return self.compute_position_size(
                confidence=confidence,
                volatility=volatility,
                max_pct=self.config.get('max_position_pct', 0.1),
                target_risk_vol=self.config.get('target_risk_vol', 0.25),
                min_pct=self.config.get('min_position_pct', 0.01)
            )
        except Exception as e:
            return 0.0
    
    def rolling_volatility(self, price_series: pd.Series, window: int = 20) -> float:
        """Estimate annualized volatility from price history."""
        if price_series is None or price_series.empty:
            return 0.0
        returns = price_series.pct_change().dropna().tail(window)
        if returns.empty:
            return 0.0
        vol = returns.std() * math.sqrt(252)
        return float(vol) if not math.isnan(vol) else 0.0
    
    def compute_position_size(self,
                             confidence: float,
                             volatility: float,
                             max_pct: float,
                             target_risk_vol: float = 0.25,
                             min_pct: float = 0.01) -> float:
        """Convert signal confidence & volatility into position size percentage."""
        if confidence <= 0 or volatility <= 0:
            return 0.0
        
        # Base position size on confidence and inverse volatility
        base_size = confidence / volatility
        
        # Scale to target risk level
        risk_adjusted_size = base_size * target_risk_vol
        
        # Apply bounds
        position_size = max(min_pct, min(max_pct, risk_adjusted_size))
        
        return float(position_size)


# Keep standalone functions for backward compatibility
def rolling_volatility(price_series: pd.Series, window: int = 20) -> float:
    """Estimate annualized volatility from price history."""
    if price_series is None or price_series.empty:
        return 0.0
    returns = price_series.pct_change().dropna().tail(window)
    if returns.empty:
        return 0.0
    vol = returns.std() * math.sqrt(252)
    return float(vol) if not math.isnan(vol) else 0.0

def compute_position_size(confidence: float,
                         volatility: float,
                         max_pct: float,
                         target_risk_vol: float = 0.25,
                         min_pct: float = 0.01) -> float:
    """Convert signal confidence & volatility into position size percentage."""
    if confidence <= 0 or volatility <= 0:
        return 0.0
    
    # Base position size on confidence and inverse volatility
    base_size = confidence / volatility
    
    # Scale to target risk level
    risk_adjusted_size = base_size * target_risk_vol
    
    # Apply bounds
    position_size = max(min_pct, min(max_pct, risk_adjusted_size))
    
    return float(position_size)

__all__ = ["SizingService", "rolling_volatility", "compute_position_size"]
