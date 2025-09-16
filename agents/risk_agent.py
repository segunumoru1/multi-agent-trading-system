from agents.base_agent import BaseAgent
from core.memory import FinancialSituationMemory
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class RiskAgent(BaseAgent):
    def __init__(self, llm, risk_profile, memory, tools=None):
        super().__init__(tools)
        self.llm = llm
        self.risk_profile = risk_profile
        self.memory = memory

    def step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            risk_state = state['risk_debate_state']
            opponents_args = []
            if self.risk_profile != 'Risky Analyst' and risk_state['current_risky_response']:
                opponents_args.append(f"Risky: {risk_state['current_risky_response']}")
            if self.risk_profile != 'Safe Analyst' and risk_state['current_safe_response']:
                opponents_args.append(f"Safe: {risk_state['current_safe_response']}")
            if self.risk_profile != 'Neutral Analyst' and risk_state['current_neutral_response']:
                opponents_args.append(f"Neutral: {risk_state['current_neutral_response']}")
            
            if self.risk_profile == 'Risky Analyst':
                prompt = f"""You are the Risky Risk Analyst. You advocate for high-reward opportunities and bold strategies.
                Here is the trader's plan: {state['trader_investment_plan']}
                Debate history: {risk_state['history']}
                Your opponents' last arguments:\n{'\n'.join(opponents_args)}
                Critique or support the plan from your perspective."""
            elif self.risk_profile == 'Safe Analyst':
                prompt = f"""You are the Safe/Conservative Risk Analyst. You prioritize capital preservation and minimizing volatility.
                Here is the trader's plan: {state['trader_investment_plan']}
                Debate history: {risk_state['history']}
                Your opponents' last arguments:\n{'\n'.join(opponents_args)}
                Critique or support the plan from your perspective."""
            else:
                prompt = f"""You are the Neutral Risk Analyst. You provide a balanced perspective, weighing both benefits and risks.
                Here is the trader's plan: {state['trader_investment_plan']}
                Debate history: {risk_state['history']}
                Your opponents' last arguments:\n{'\n'.join(opponents_args)}
                Critique or support the plan from your perspective."""
            
            response = self.llm.invoke(prompt).content
            
            new_risk_state = risk_state.copy()
            new_risk_state['history'] += f"\n{self.risk_profile}: {response}"
            new_risk_state['latest_speaker'] = self.risk_profile
            if self.risk_profile == 'Risky Analyst':
                new_risk_state['current_risky_response'] = response
            elif self.risk_profile == 'Safe Analyst':
                new_risk_state['current_safe_response'] = response
            else:
                new_risk_state['current_neutral_response'] = response
            new_risk_state['count'] += 1
            
            return {"risk_debate_state": new_risk_state}
        except Exception as e:
            logger.error(f"Error in RiskAgent step: {e}")
            return {"risk_debate_state": state['risk_debate_state']}