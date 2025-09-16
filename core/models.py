from typing import Dict, List, Optional, TypedDict, Any
from langchain_core.messages import BaseMessage

class AnalystOutput(TypedDict, total=False):
    """Output from market, news, social media, or fundamentals analyst."""
    market_report: str
    news_report: str
    social_report: str
    fundamentals_report: str
    key_insights: List[str]
    sentiment_score: float  # -1.0 to 1.0

class ResearchInput(TypedDict, total=False):
    """Input to research debate from analyst layer."""
    company_of_interest: str
    trade_date: str
    market_report: str
    news_report: str
    social_report: str
    fundamentals_report: str
    key_insights: List[str]
    relevant_memories: List[Dict[str, Any]]
    sentiment_score: float

class InvestDebateState(TypedDict):
    """State for the bull vs bear investment debate."""
    bull_history: str
    bear_history: str
    history: str
    current_response: str
    judge_decision: str
    count: int

class RiskDebateState(TypedDict):
    """State for the risk debate."""
    risky_history: str
    safe_history: str
    neutral_history: str
    history: str
    latest_speaker: str
    current_risky_response: str
    current_safe_response: str
    current_neutral_response: str
    judge_decision: str
    count: int

class TradeProposal(TypedDict, total=False):
    """Trade proposal from the trader."""
    action: str  # BUY, SELL, HOLD
    ticker: str
    reasoning: str
    conviction: float  # 0.0 to 1.0
    target_price: float
    stop_loss: float
    time_horizon: str  # SHORT_TERM, MEDIUM_TERM, LONG_TERM

class AgentState(TypedDict):
    """Global shared state for the multi-agent system."""
    messages: List[BaseMessage]
    company_of_interest: str
    trade_date: str
    sender: str
    market_report: str
    sentiment_report: str
    news_report: str
    fundamentals_report: str
    investment_debate_state: InvestDebateState
    investment_plan: str
    trader_investment_plan: str
    risk_debate_state: RiskDebateState
    final_trade_decision: str