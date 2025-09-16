from fastapi import FastAPI
from app.api.routes import router
from core.monitoring.metrics import metrics

app = FastAPI(
    title="Multi-Agent Trading System",
    version="1.0.0",
    description="A comprehensive multi-agent trading system using LangGraph"
)

app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Multi-Agent Trading System API"}

@app.on_event("startup")
async def startup_event():
    metrics.start_server()