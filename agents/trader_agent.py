from core.services.service_manager import get_service_manager
from typing import Dict, Any

class EnhancedTraderAgent:
    """Enhanced trader agent with position sizing and portfolio integration."""
    
    def __init__(self, llm, memory, config: Dict[str, Any]):
        self.llm = llm
        self.memory = memory
        self.config = config
        self.service_manager = get_service_manager(config)
    
    def create_trading_plan(self, investment_plan: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a trading plan with proper position sizing."""
        
        # Get current portfolio status
        portfolio_service = self.service_manager.get_service('portfolio')
        current_portfolio = portfolio_service.get_portfolio_status() if portfolio_service else {}
        
        account_balance = current_portfolio.get('cash', 100000)  # Default $100k
        
        # Calculate position size using sizing service
        position_size = self.service_manager.get_position_size(
            account_balance=account_balance,
            risk_tolerance=0.02,  # 2% risk per trade
            market_data=market_data
        )
        
        # Generate trading plan with LLM
        prompt = f"""
        Based on the investment plan: {investment_plan}
        Account balance: ${account_balance:,.2f}
        Calculated position size: ${position_size:,.2f}
        
        Create a detailed trading plan including:
        1. Entry strategy
        2. Position size details
        3. Stop-loss levels
        4. Take-profit targets
        5. Risk management rules
        
        End with: FINAL TRANSACTION PROPOSAL: **BUY/SELL/HOLD**
        """
        
        response = self.llm.invoke(prompt)
        
        return {
            'trading_plan': response.content,
            'position_size': position_size,
            'account_balance': account_balance
        }