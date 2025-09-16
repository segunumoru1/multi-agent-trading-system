from agents.base_agent import BaseAgent
from core.memory import FinancialSituationMemory
from typing import Dict, Any

class ExecutionAgent(BaseAgent):
    name = "execution_agent"
    role = "create_trading_plan"

    def __init__(self, llm, memory, tools=None):
        super().__init__(tools)
        self.llm = llm
        self.memory = memory

    def step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""You are a trading agent. Based on the provided investment plan, create a concise trading proposal. 
        Your response must end with 'FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**'.
        
        Proposed Investment Plan: {state['investment_plan']}"""
        
        result = self.llm.invoke(prompt)
        return {"trader_investment_plan": result.content, "sender": "Trader"}