from core.services.service_manager import get_service_manager
from typing import Dict, Any

class EnhancedRiskAgent:
    """Enhanced risk agent with advanced risk calculations."""
    
    def __init__(self, llm, role, memory, config: Dict[str, Any]):
        self.llm = llm
        self.role = role
        self.memory = memory
        self.config = config
        self.service_manager = get_service_manager(config)
    
    def analyze_risk(self, trading_plan: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive risk analysis."""
        
        # Get advanced risk metrics from service
        risk_metrics = self.service_manager.calculate_risk_metrics({
            "trading_plan": trading_plan,
            "market_data": market_data
        })
        
        # Generate risk assessment using LLM
        prompt = f"""
        As a {self.role} Risk Analyst, analyze the following:
        
        Trading Plan: {trading_plan}
        
        Advanced Risk Metrics:
        - VaR (95%): {risk_metrics.get('var_95', 'N/A')}
        - CVaR (95%): {risk_metrics.get('cvar_95', 'N/A')}
        - Maximum Drawdown: {risk_metrics.get('max_drawdown', 'N/A')}
        - Portfolio Beta: {risk_metrics.get('beta', 'N/A')}
        
        Provide your assessment and recommendations.
        """
        
        response = self.llm.invoke(prompt)
        
        return {
            "risk_assessment": response.content,
            "risk_metrics": risk_metrics,
            "recommendations": self._extract_recommendations(response.content)
        }
    
    def _extract_recommendations(self, assessment: str) -> List[str]:
        """Extract actionable recommendations from risk assessment."""
        # Simple extraction - could be enhanced with LLM
        recommendations = []
        if "reduce position" in assessment.lower():
            recommendations.append("Consider reducing position size")
        if "stop loss" in assessment.lower():
            recommendations.append("Implement tighter stop-loss")
        if "diversify" in assessment.lower():
            recommendations.append("Diversify across multiple assets")
        
        return recommendations