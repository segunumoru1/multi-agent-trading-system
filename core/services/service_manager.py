from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ServiceManager:
    """Manages integration of various trading services."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.services = {}
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize all available services."""
        try:
            # Import and initialize services
            from services.backtest_service import BacktestService
            from services.portfolio_service import PortfolioService
            from services.risk_engine import RiskEngine
            from services.sizing_service import SizingService
            from services.streaming_services import StreamingService
            
            self.services['backtest'] = BacktestService(self.config)
            self.services['portfolio'] = PortfolioService(self.config)
            self.services['risk'] = RiskEngine(self.config)
            self.services['sizing'] = SizingService(self.config)
            self.services['streaming'] = StreamingService(self.config)
            
            logger.info("All services initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing services: {e}")
    
    def get_service(self, service_name: str):
        """Get a specific service instance."""
        return self.services.get(service_name)
    
    def execute_backtest(self, strategy_results: Dict[str, Any], 
                        start_date: str, end_date: str) -> Dict[str, Any]:
        """Execute backtest using the backtest service."""
        backtest_service = self.get_service('backtest')
        if backtest_service:
            return backtest_service.run_backtest(strategy_results, start_date, end_date)
        return {}
    
    def update_portfolio(self, trade_details: Dict[str, Any]) -> bool:
        """Update portfolio with new trade."""
        portfolio_service = self.get_service('portfolio')
        if portfolio_service:
            return portfolio_service.update_position(trade_details)
        return False
    
    def calculate_risk_metrics(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive risk metrics."""
        risk_service = self.get_service('risk')
        if risk_service:
            return risk_service.calculate_portfolio_risk(portfolio_data)
        return {}
    
    def get_position_size(self, account_balance: float, risk_tolerance: float, 
                         market_data: Dict[str, Any]) -> float:
        """Calculate optimal position size."""
        sizing_service = self.get_service('sizing')
        if sizing_service:
            return sizing_service.calculate_position_size(
                account_balance, risk_tolerance, market_data
            )
        return 0.0
    
    def start_market_stream(self, symbols: list) -> bool:
        """Start real-time market data streaming."""
        streaming_service = self.get_service('streaming')
        if streaming_service:
            return streaming_service.start_stream(symbols)
        return False

# Global service manager instance
service_manager = None

def get_service_manager(config: Dict[str, Any]):
    """Get or create the service manager instance."""
    global service_manager
    if service_manager is None:
        service_manager = ServiceManager(config)
    return service_manager