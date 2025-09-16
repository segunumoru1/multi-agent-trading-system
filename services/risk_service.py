from agents.base_agent import BaseAgent
from services.risk_service import RiskService

class RiskDebateAgent(BaseAgent):
    def __init__(self, llm, risk_profile, portfolio_service, tools=None):
        super().__init__(tools)
        self.llm = llm
        self.risk_profile = risk_profile
        self.risk_service = RiskService(portfolio_service)

    def step(self, state):
        trade_proposal = state.get("trade_proposal")
        # Expose VaR calculation as a tool
        var = self.risk_service.calculate_position_var(
            symbol=trade_proposal.ticker,
            quantity=trade_proposal.quantity,
            confidence=0.95
        )
        prompt = f"""
        You are a {self.risk_profile} risk manager. Given the trade proposal:
        {trade_proposal}
        and the calculated VaR: {var}
        Debate the risk and recommend adjustments.
        """
        response = self.llm(prompt)
        return {f"{self.risk_profile}_risk_opinion": response}