from logging import config
from fastapi import FastAPI
from app.api.routes import router
from core.monitoring.metrics import metrics
from core.services.service_manager import get_service_manager
from agents.backtest_agent import BacktestAgent
from agents.enhanced_risk_agent import EnhancedRiskAgent
from core.streaming.streaming_manager import StreamingManager
from config.config import settings

app = FastAPI(
    title="Multi-Agent Trading System",
    version="1.0.0",
    description="A comprehensive multi-agent trading system using LangGraph"
)

app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Multi-Agent Trading System API"}

# Initialize services
service_manager = get_service_manager(settings)

# Initialize enhanced agents
backtest_agent = BacktestAgent(settings)
streaming_manager = StreamingManager(settings)

@app.on_event("startup")
async def startup_event():
    # Start streaming for key symbols
    streaming_manager.start_streaming(["NVDA", "AAPL", "MSFT", "GOOGL"])
    
    # Initialize other services
    service_manager.get_service('portfolio').initialize_portfolio() if service_manager.get_service('portfolio') else None

    metrics.start_server()