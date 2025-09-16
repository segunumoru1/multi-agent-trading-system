from agents.base_agent import BaseAgent
from core.memory import FinancialSituationMemory
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class PortfolioManager(BaseAgent):
    name = "portfolio_manager"
    role = "final_decision"

    def __init__(self, llm, memory, tools=None):
        super().__init__(tools)
        self.llm = llm
        self.memory = memory

    def step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            prompt = f"""As the Portfolio Manager, your decision is final. Review the trader's plan and the risk debate.
            Provide a final, binding decision: Buy, Sell, or Hold, and a brief justification.
            
            Trader's Plan: {state['trader_investment_plan']}
            Risk Debate: {state['risk_debate_state']['history']}"""
            
            response = self.llm.invoke(prompt).content
            return {"final_trade_decision": response}
        except Exception as e:
            logger.error(f"Error in PortfolioManager step: {e}")
            return {"final_trade_decision": f"Error generating final decision: {e}"}