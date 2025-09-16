from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from datetime import datetime
from core.db.connection import get_db
from core.db.models import Portfolio, Position, TradeRecord
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np
from sqlalchemy import func

class PortfolioService:
    """Service for portfolio management and position tracking."""
    
    def __init__(self, portfolio_id: Optional[int] = None, portfolio_name: Optional[str] = None):
        """Initialize with either an existing portfolio ID or create a new one."""
        self.db = next(get_db())
        
        if portfolio_id:
            # Load existing portfolio
            self.portfolio = self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
            if not self.portfolio:
                raise ValueError(f"Portfolio with ID {portfolio_id} not found")
        elif portfolio_name:
            # Create new portfolio
            self.portfolio = Portfolio(name=portfolio_name, cash=100000.0, settings={})
            self.db.add(self.portfolio)
            self.db.commit()
            self.db.refresh(self.portfolio)
        else:
            raise ValueError("Either portfolio_id or portfolio_name must be provided")
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get current position for a symbol."""
        return self.db.query(Position).filter(
            Position.portfolio_id == self.portfolio.id,
            Position.symbol == symbol
        ).first()
    
    def get_all_positions(self) -> List[Position]:
        """Get all current positions in the portfolio."""
        return self.db.query(Position).filter(
            Position.portfolio_id == self.portfolio.id
        ).all()
    
    def execute_trade(self, 
                      symbol: str, 
                      action: str, 
                      quantity: float, 
                      price: float, 
                      commission: float = 0.0,
                      slippage: float = 0.0) -> TradeRecord:
        """Execute a trade and update portfolio state."""
        # Validate inputs
        if action.upper() not in ["BUY", "SELL"]:
            raise ValueError("Action must be either BUY or SELL")
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if price <= 0:
            raise ValueError("Price must be positive")
        
        # Calculate trade cost
        trade_value = quantity * price
        total_cost = trade_value + commission
        
        # Check if we have enough cash for buys
        if action.upper() == "BUY" and total_cost > self.portfolio.cash:
            raise ValueError(f"Insufficient cash: {self.portfolio.cash} < {total_cost}")
        
        # Check if we have enough shares for sells
        position = self.get_position(symbol)
        if action.upper() == "SELL":
            if not position or position.quantity < quantity:
                raise ValueError(f"Insufficient shares: {position.quantity if position else 0} < {quantity}")
        
        # Update cash
        if action.upper() == "BUY":
            self.portfolio.cash -= total_cost
        else:  # SELL
            self.portfolio.cash += trade_value - commission
        
        # Update position
        if action.upper() == "BUY":
            if position:
                # Update existing position with weighted average price
                new_total = position.quantity + quantity
                position.avg_price = ((position.quantity * position.avg_price) + (quantity * price)) / new_total
                position.quantity = new_total
                position.last_price = price
                position.last_updated = datetime.utcnow()
            else:
                # Create new position
                position = Position(
                    portfolio_id=self.portfolio.id,
                    symbol=symbol,
                    quantity=quantity,
                    avg_price=price,
                    last_price=price
                )
                self.db.add(position)
        else:  # SELL
            # Reduce position
            position.quantity -= quantity
            position.last_price = price
            position.last_updated = datetime.utcnow()
            
            # Remove position if quantity is zero
            if position.quantity <= 0:
                self.db.delete(position)
        
        # Create trade record
        trade = TradeRecord(
            symbol=symbol,
            trade_date=datetime.utcnow(),
            action=action.upper(),
            quantity=quantity,
            price=price,
            commission=commission,
            slippage=slippage,
            trade_id=f"{datetime.utcnow().timestamp()}-{symbol}",
            portfolio_id=self.portfolio.id
        )
        self.db.add(trade)
        
        # Commit changes
        self.portfolio.last_updated = datetime.utcnow()
        self.db.commit()
        self.db.refresh(trade)
        
        return trade
    
    def update_positions_price(self, prices: Dict[str, float]) -> None:
        """Update the last price of all positions."""
        positions = self.get_all_positions()
        for position in positions:
            if position.symbol in prices:
                position.last_price = prices[position.symbol]
                position.last_updated = datetime.utcnow()
        
        self.portfolio.last_updated = datetime.utcnow()
        self.db.commit()
    
    def get_portfolio_value(self) -> Tuple[float, float, float]:
        """Get current portfolio value (cash + positions)."""
        positions = self.get_all_positions()
        positions_value = sum(p.quantity * p.last_price for p in positions)
        total_value = self.portfolio.cash + positions_value
        return self.portfolio.cash, positions_value, total_value
    
    def get_portfolio_returns(self, days: int = 30) -> pd.DataFrame:
        """Calculate portfolio returns over the specified period."""
        # Get trades within the period
        cutoff_date = datetime.utcnow() - pd.Timedelta(days=days)
        trades = self.db.query(TradeRecord).filter(
            TradeRecord.portfolio_id == self.portfolio.id,
            TradeRecord.trade_date >= cutoff_date
        ).order_by(TradeRecord.trade_date).all()
        
        # If no trades, return empty DataFrame
        if not trades:
            return pd.DataFrame(columns=["date", "portfolio_value"])
        
        # Create daily portfolio snapshots
        dates = pd.date_range(
            start=trades[0].trade_date.date(),
            end=datetime.utcnow().date(),
            freq="B"  # Business days
        )
        
        portfolio_values = []
        current_positions = {}
        current_cash = self.portfolio.cash
        
        # Reconstruct portfolio history
        for date in dates:
            # Apply trades for this date
            day_trades = [t for t in trades if t.trade_date.date() == date.date()]
            for trade in day_trades:
                if trade.action == "BUY":
                    if trade.symbol not in current_positions:
                        current_positions[trade.symbol] = {"qty": 0, "price": 0}
                    
                    # Update position with weighted average price
                    current_qty = current_positions[trade.symbol]["qty"]
                    current_price = current_positions[trade.symbol]["price"]
                    new_qty = current_qty + trade.quantity
                    if new_qty > 0:
                        new_price = ((current_qty * current_price) + (trade.quantity * trade.price)) / new_qty
                        current_positions[trade.symbol] = {"qty": new_qty, "price": new_price}
                    
                    # Update cash
                    current_cash -= (trade.quantity * trade.price + trade.commission)
                
                elif trade.action == "SELL":
                    # Update position
                    current_positions[trade.symbol]["qty"] -= trade.quantity
                    if current_positions[trade.symbol]["qty"] <= 0:
                        del current_positions[trade.symbol]
                    
                    # Update cash
                    current_cash += (trade.quantity * trade.price - trade.commission)
            
            # Calculate portfolio value for this date
            positions_value = sum(
                pos["qty"] * pos["price"] 
                for pos in current_positions.values()
            )
            total_value = current_cash + positions_value
            
            portfolio_values.append({
                "date": date,
                "portfolio_value": total_value
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(portfolio_values)
        
        # Calculate daily returns
        if len(df) > 1:
            df["daily_return"] = df["portfolio_value"].pct_change()
            df["cumulative_return"] = (1 + df["daily_return"]).cumprod() - 1
        
        return df
    
    def get_risk_metrics(self) -> Dict[str, float]:
        """Calculate portfolio risk metrics."""
        returns = self.get_portfolio_returns(days=60)
        
        if len(returns) <= 1 or "daily_return" not in returns:
            return {
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "var_95": 0.0
            }
        
        # Calculate metrics
        daily_returns = returns["daily_return"].dropna().values
        
        # Annualized volatility
        volatility = np.std(daily_returns) * np.sqrt(252)
        
        # Sharpe ratio (assuming risk-free rate = 0 for simplicity)
        mean_daily_return = np.mean(daily_returns)
        sharpe_ratio = (mean_daily_return * 252) / volatility if volatility > 0 else 0
        
        # Maximum drawdown
        cum_returns = (1 + returns["daily_return"].fillna(0)).cumprod()
        max_return = cum_returns.cummax()
        drawdown = (cum_returns / max_return) - 1
        max_drawdown = drawdown.min()
        
        # Value at Risk (95%)
        var_95 = np.percentile(daily_returns, 5)
        
        return {
            "volatility": float(volatility),
            "sharpe_ratio": float(sharpe_ratio),
            "max_drawdown": float(max_drawdown),
            "var_95": float(var_95)
        }
    
    def allocate_positions(self, allocations: Dict[str, float], max_position_pct: float = 0.25) -> List[Dict]:
        """
        Allocate portfolio based on target weights.
        
        Args:
            allocations: Dictionary mapping symbols to target allocation percentages (0-1)
            max_position_pct: Maximum allocation for any single position (0-1)
            
        Returns:
            List of trades to execute
        """
        # Validate inputs
        if not allocations:
            return []
        
        if sum(allocations.values()) > 1.0:
            raise ValueError("Sum of allocations cannot exceed 100%")
        
        # Cap individual allocations
        capped_allocations = {
            symbol: min(alloc, max_position_pct)
            for symbol, alloc in allocations.items()
        }
        
        # Get current portfolio state
        cash, positions_value, total_value = self.get_portfolio_value()
        positions = {p.symbol: p for p in self.get_all_positions()}
        
        # Calculate target position values
        target_values = {
            symbol: total_value * alloc
            for symbol, alloc in capped_allocations.items()
        }
        
        # Calculate trades needed
        trades_to_execute = []
        
        # First, handle sells to free up cash
        for symbol, position in positions.items():
            current_value = position.quantity * position.last_price
            target_value = target_values.get(symbol, 0)
            
            if current_value > target_value:
                # Need to sell
                sell_value = current_value - target_value
                sell_quantity = sell_value / position.last_price
                
                trades_to_execute.append({
                    "symbol": symbol,
                    "action": "SELL",
                    "quantity": sell_quantity,
                    "price": position.last_price,
                    "reason": f"Rebalance: reduce {symbol} from {current_value:.2f} to {target_value:.2f}"
                })
        
        # Then, handle buys with updated cash
        updated_cash = cash + sum(
            t["quantity"] * t["price"] 
            for t in trades_to_execute
        )
        
        for symbol, target_value in target_values.items():
            current_value = 0
            current_price = 0
            
            if symbol in positions:
                position = positions[symbol]
                current_value = position.quantity * position.last_price
                current_price = position.last_price
            
            if current_value < target_value and current_price > 0:
                # Need to buy
                buy_value = min(target_value - current_value, updated_cash)
                if buy_value > 0:
                    buy_quantity = buy_value / current_price
                    
                    trades_to_execute.append({
                        "symbol": symbol,
                        "action": "BUY",
                        "quantity": buy_quantity,
                        "price": current_price,
                        "reason": f"Rebalance: increase {symbol} from {current_value:.2f} to {target_value:.2f}"
                    })
                    
                    updated_cash -= buy_value
        
        return trades_to_execute
    
    def update_position(self, trade_details: Dict[str, Any]) -> bool:
        """Update portfolio position based on trade details."""
        try:
            symbol = trade_details.get('symbol')
            action = trade_details.get('action')
            quantity = trade_details.get('quantity', 0)
            price = trade_details.get('price', 0)
            commission = trade_details.get('commission', 0)
            
            if not symbol or not action:
                return False
            
            # Execute the trade
            trade_record = self.execute_trade(
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=price,
                commission=commission
            )
            
            return trade_record is not None
        except Exception as e:
            logger.error(f"Error updating position: {e}")
            return False