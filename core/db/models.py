from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.db.connection import Base
from typing import Dict, Any

class AgentMemory(Base):
    """Model for storing agent memories."""
    __tablename__ = "agent_memories"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(255), nullable=False, index=True)
    situation = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<AgentMemory(agent_name='{self.agent_name}')>"

class TradeRecord(Base):
    """Model for storing trade records."""
    __tablename__ = "trade_records"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    ticker = Column(String(10), nullable=False)
    trade_date = Column(DateTime(timezone=True), nullable=False)
    trade_type = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    total_cost = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    portfolio = relationship("Portfolio", back_populates="trades")

    def __repr__(self):
        return f"<TradeRecord(ticker='{self.ticker}', trade_type='{self.trade_type}', quantity={self.quantity})>"

class Portfolio(Base):
    """Model for storing portfolio information."""
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    cash = Column(Float, default=100000.0)
    settings = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    trades = relationship("TradeRecord", back_populates="portfolio")
    positions = relationship("Position", back_populates="portfolio")

    def __repr__(self):
        return f"<Portfolio(name='{self.name}', cash={self.cash})>"

class Position(Base):
    """Model for storing current positions in a portfolio."""
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    ticker = Column(String(10), nullable=False)
    quantity = Column(Float, nullable=False)
    average_cost = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    market_value = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    portfolio = relationship("Portfolio", back_populates="positions")

    def __repr__(self):
        return f"<Position(ticker='{self.ticker}', quantity={self.quantity}, average_cost={self.average_cost})>"

class AnalysisResult(Base):
    """Model for storing analysis results."""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(255), unique=True, nullable=False)
    ticker = Column(String(10), nullable=False)
    trade_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), default="pending")  # pending, completed, failed
    signal = Column(String(10), nullable=True)  # BUY, SELL, HOLD
    final_decision = Column(Text, nullable=True)
    market_report = Column(Text, nullable=True)
    sentiment_report = Column(Text, nullable=True)
    news_report = Column(Text, nullable=True)
    fundamentals_report = Column(Text, nullable=True)
    execution_time = Column(Float, nullable=True)  # in seconds
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<AnalysisResult(request_id='{self.request_id}', ticker='{self.ticker}', status='{self.status}')>"

class BacktestResult(Base):
    """Model for storing backtest results."""
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(255), unique=True, nullable=False)
    ticker = Column(String(10), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    total_return = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)
    total_trades = Column(Integer, default=0)
    results_data = Column(JSON, nullable=True)  # Store detailed results as JSON
    execution_time = Column(Float, nullable=True)  # in seconds
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<BacktestResult(request_id='{self.request_id}', ticker='{self.ticker}', status='{self.status}')>"