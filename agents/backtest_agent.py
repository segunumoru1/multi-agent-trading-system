from core.services.service_manager import get_service_manager
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class BacktestAgent:
    """Agent responsible for backtesting trading strategies."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.service_manager = get_service_manager(config)
    
    def run_backtest(self, strategy_results: List[Dict[str, Any]], 
                    start_date: str, end_date: str) -> Dict[str, Any]:
        """Run comprehensive backtest on strategy results."""
        
        try:
            backtest_service = self.service_manager.get_service('backtest')
            if not backtest_service:
                return {"error": "Backtest service not available"}
            
            # Execute backtest
            results = backtest_service.run_backtest(strategy_results, start_date, end_date)
            
            # Analyze results
            analysis = self._analyze_backtest_results(results)
            
            return {
                "backtest_results": results,
                "analysis": analysis,
                "recommendations": self._generate_recommendations(analysis)
            }
            
        except Exception as e:
            logger.error(f"Backtest execution failed: {e}")
            return {"error": str(e)}
    
    def _analyze_backtest_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze backtest results and extract key metrics."""
        
        return {
            "total_return": results.get("total_return", 0),
            "sharpe_ratio": results.get("sharpe_ratio", 0),
            "max_drawdown": results.get("max_drawdown", 0),
            "win_rate": results.get("win_rate", 0),
            "total_trades": results.get("total_trades", 0),
            "profit_factor": results.get("profit_factor", 0)
        }
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on backtest analysis."""
        
        recommendations = []
        
        if analysis["sharpe_ratio"] > 1.5:
            recommendations.append("Strategy shows good risk-adjusted returns")
        elif analysis["sharpe_ratio"] < 0.5:
            recommendations.append("Strategy has poor risk-adjusted returns - consider modifications")
        
        if analysis["max_drawdown"] > 0.20:  # 20%
            recommendations.append("High drawdown detected - implement stricter risk management")
        
        if analysis["win_rate"] > 0.60:
            recommendations.append("Good win rate - strategy has strong predictive power")
        
        return recommendations