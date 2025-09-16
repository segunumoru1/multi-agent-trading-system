from typing import Dict, Any
import logging
import time
import yfinance as yf
import finnhub
import os

logger = logging.getLogger(__name__)

class HealthChecker:
    def __init__(self):
        self.last_check = 0
        self.check_interval = 300  # 5 minutes
        
    def check_yfinance_api(self) -> Dict[str, Any]:
        """Check Yahoo Finance API connectivity."""
        try:
            ticker = yf.Ticker("AAPL")
            data = ticker.history(period="1d")
            return {"status": "healthy", "details": f"Retrieved {len(data)} data points"}
        except Exception as e:
            return {"status": "unhealthy", "details": str(e)}
    
    def check_finnhub_api(self) -> Dict[str, Any]:
        """Check Finnhub API connectivity."""
        try:
            api_key = os.environ.get("FINNHUB_API_KEY")
            if not api_key:
                return {"status": "unhealthy", "details": "API key not configured"}
            
            finnhub_client = finnhub.Client(api_key=api_key)
            # Simple API call to test connectivity
            news = finnhub_client.company_news("AAPL", _from="2023-01-01", to="2023-01-02")
            return {"status": "healthy", "details": f"Retrieved {len(news)} news items"}
        except Exception as e:
            return {"status": "unhealthy", "details": str(e)}
    
    def check_openai_api(self) -> Dict[str, Any]:
        """Check OpenAI API connectivity."""
        try:
            from openai import OpenAI
            client = OpenAI()
            # Simple API call to test connectivity
            response = client.models.list()
            return {"status": "healthy", "details": f"Connected to {len(response.data)} models"}
        except Exception as e:
            return {"status": "unhealthy", "details": str(e)}
    
    def check_database(self) -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            from core.db.connection import get_db
            db = next(get_db())
            db.execute("SELECT 1")
            return {"status": "healthy", "details": "Database connection successful"}
        except Exception as e:
            return {"status": "unhealthy", "details": str(e)}
    
    def check_redis_cache(self) -> Dict[str, Any]:
        """Check Redis cache connectivity."""
        try:
            from core.cache.redis_cache import cache
            cache.redis_client.ping()
            return {"status": "healthy", "details": "Redis connection successful"}
        except Exception as e:
            return {"status": "unhealthy", "details": str(e)}
    
    def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        current_time = time.time()
        if current_time - self.last_check < self.check_interval:
            return {"status": "cached", "timestamp": self.last_check}
        
        health_status = {
            "timestamp": current_time,
            "overall_status": "healthy",
            "services": {
                "yfinance_api": self.check_yfinance_api(),
                "finnhub_api": self.check_finnhub_api(),
                "openai_api": self.check_openai_api(),
                "database": self.check_database(),
                "redis_cache": self.check_redis_cache()
            }
        }
        
        # Determine overall status
        for service, status in health_status["services"].items():
            if status["status"] == "unhealthy":
                health_status["overall_status"] = "unhealthy"
                break
        
        self.last_check = current_time
        return health_status

# Global health checker instance
health_checker = HealthChecker()