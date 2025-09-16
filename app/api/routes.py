from fastapi import APIRouter, HTTPException
from datetime import date
from pydantic import BaseModel
from graphs.trading_graph import build_trading_graph
from core.evaluation import SignalProcessor
from langchain_core.messages import HumanMessage
from core.models import AgentState, InvestDebateState, RiskDebateState
from config.config import config
from core.async_processing import async_analyze_multiple_stocks
from core.monitoring.health_checks import health_checker
import uuid
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter()

class AnalyzeRequest(BaseModel):
    ticker: str
    trade_date: date | None = None

class AnalyzeResponse(BaseModel):
    ticker: str
    trade_date: date
    signal: str
    final_trade_decision: str
    run_id: str

class BatchAnalyzeRequest(BaseModel):
    tickers: List[str]
    trade_date: date | None = None

class BatchAnalyzeResponse(BaseModel):
    results: List[Dict[str, Any]]

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    try:
        trade_date = req.trade_date or date.today()
        
        graph_input = AgentState(
            messages=[HumanMessage(content=f"Analyze {req.ticker} for trading on {trade_date}")],
            company_of_interest=req.ticker.upper(),
            trade_date=trade_date.isoformat(),
            investment_debate_state=InvestDebateState(
                bull_history='', bear_history='', history='', current_response='', judge_decision='', count=0
            ),
            risk_debate_state=RiskDebateState(
                risky_history='', safe_history='', neutral_history='', history='', 
                latest_speaker='', current_risky_response='', current_safe_response='', 
                current_neutral_response='', judge_decision='', count=0
            )
        )
        
        graph = build_trading_graph(config)
        final_state = graph.invoke(graph_input)
        
        signal_processor = SignalProcessor(ChatOpenAI(
            model=config["quick_think_llm"],
            base_url=config["backend_url"],
            temperature=0.1
        ))
        signal = signal_processor.process_signal(final_state.get("final_trade_decision", ""))
        
        run_id = str(uuid.uuid4())
        
        return AnalyzeResponse(
            ticker=req.ticker.upper(),
            trade_date=trade_date,
            signal=signal,
            final_trade_decision=final_state.get("final_trade_decision", ""),
            run_id=run_id
        )
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-analyze", response_model=BatchAnalyzeResponse)
async def batch_analyze(req: BatchAnalyzeRequest):
    try:
        trade_date = req.trade_date or date.today()
        results = await async_analyze_multiple_stocks(req.tickers, trade_date.isoformat(), config)
        return BatchAnalyzeResponse(results=results)
    except Exception as e:
        logger.error(f"Error in batch analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/health/detailed")
def detailed_health():
    return health_checker.perform_health_check()