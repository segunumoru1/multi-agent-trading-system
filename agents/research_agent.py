from agents.base_agent import BaseAgent
from core.memory import FinancialSituationMemory
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ResearchAgent(BaseAgent):
    def __init__(self, llm, role, memory, tools=None):
        super().__init__(tools)
        self.llm = llm
        self.role = role
        self.memory = memory

    def step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            situation_summary = f"""
            Market Report: {state['market_report']}
            Sentiment Report: {state['sentiment_report']}
            News Report: {state['news_report']}
            Fundamentals Report: {state['fundamentals_report']}
            """
            past_memories = self.memory.get_memories(situation_summary)
            past_memory_str = "\n".join([mem['recommendation'] for mem in past_memories])
            
            if self.role == "bull":
                prompt = f"""You are a Bull Analyst. Your goal is to argue for investing in the stock. Focus on growth potential, competitive advantages, and positive indicators from the reports. Counter the bear's arguments effectively.
                Here is the current state of the analysis: {situation_summary}
                Conversation history: {state['investment_debate_state']['history']}
                Your opponent's last argument: {state['investment_debate_state']['current_response']}
                Reflections from similar past situations: {past_memory_str or 'No past memories found.'}
                Based on all this information, present your argument conversationally."""
            else:
                prompt = f"""You are a Bear Analyst. Your goal is to argue against investing in the stock. Focus on risks, challenges, and negative indicators. Counter the bull's arguments effectively.
                Here is the current state of the analysis: {situation_summary}
                Conversation history: {state['investment_debate_state']['history']}
                Your opponent's last argument: {state['investment_debate_state']['current_response']}
                Reflections from similar past situations: {past_memory_str or 'No past memories found.'}
                Based on all this information, present your argument conversationally."""
            
            response = self.llm.invoke(prompt)
            argument = f"{self.role.title()} Analyst: {response.content}"
            
            debate_state = state['investment_debate_state'].copy()
            debate_state['history'] += "\n" + argument
            if self.role == "bull":
                debate_state['bull_history'] += "\n" + argument
            else:
                debate_state['bear_history'] += "\n" + argument
            debate_state['current_response'] = argument
            debate_state['count'] += 1
            
            return {"investment_debate_state": debate_state}
        except Exception as e:
            logger.error(f"Error in ResearchAgent step: {e}")
            return {"investment_debate_state": state['investment_debate_state']}