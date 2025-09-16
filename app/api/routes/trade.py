from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from pydantic import BaseModel
from app.api.auth import get_current_active_user
from app.api.rate_limit import limiter
from graphs.trading_graph import build_graph, run_analysis
import uuid
import asyncio

router = APIRouter(
    prefix="/trade",
    tags=["trading"],
    responses={404: {"description": "Not found"}},
)

# In-memory storage for analysis results (replace with DB in production)
analysis_results = {}

class AnalyzeRequest(BaseModel):
    ticker: str
    trade_date: Optional[date] = None

class AnalyzeResponse(BaseModel):
    request_id: str
    ticker: str
    trade_date: date
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None

class BacktestRequest(BaseModel):
    ticker: str
    start_date: date
    end_date: date
    commission_pct: float = 0.0005
    slippage_bps: int = 5

class BacktestResponse(BaseModel):
    request_id: str
    status: str = "pending"
    ticker: str
    start_date: date
    end_date: date
    days_processed: int = 0
    total_days: int = 0

# Helper function to run analysis in background
async def run_analysis_task(request_id: str, ticker: str, trade_date: date):
    try:
        # Convert date to string format
        date_str = trade_date.isoformat()
        
        # Run the analysis
        result = await asyncio.to_thread(run_analysis, ticker, date_str)
        
        # Update the stored result
        analysis_results[request_id]["status"] = "completed"
        analysis_results[request_id]["result"] = result
    except Exception as e:
        analysis_results[request_id]["status"] = "failed"
        analysis_results[request_id]["error"] = str(e)

# Helper function to run backtest in background
async def run_backtest_task(
    request_id: str, 
    ticker: str, 
    start_date: date, 
    end_date: date,
    commission_pct: float,
    slippage_bps: int
):
    try:
        current_date = start_date
        total_days = (end_date - start_date).days + 1
        days_processed = 0
        
        backtest_results = []
        
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:  # Monday=0, Sunday=6
                date_str = current_date.isoformat()
                result = run_analysis(ticker, date_str)
                backtest_results.append({
                    "date": date_str,
                    "signal": result.get("signal"),
                    "decision": result.get("final_trade_decision")
                })
                days_processed += 1
                
                # Update progress
                analysis_results[request_id]["days_processed"] = days_processed
                analysis_results[request_id]["progress"] = days_processed / total_days
            
            current_date += timedelta(days=1)
        
        # Update final result
        analysis_results[request_id]["status"] = "completed"
        analysis_results[request_id]["result"] = {
            "ticker": ticker,
            "results": backtest_results,
            "commission_pct": commission_pct,
            "slippage_bps": slippage_bps
        }
    except Exception as e:
        analysis_results[request_id]["status"] = "failed"
        analysis_results[request_id]["error"] = str(e)

@router.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit("10/minute")
async def analyze(
    background_tasks: BackgroundTasks,
    request: AnalyzeRequest,
    user = Depends(get_current_active_user)
):
    """Start an analysis for a given ticker and trade date."""
    # Use yesterday if no date provided
    trade_date = request.trade_date or date.today() - timedelta(days=1)
    
    # Generate a request ID
    request_id = str(uuid.uuid4())
    
    # Store initial result
    analysis_results[request_id] = {
        "ticker": request.ticker.upper(),
        "trade_date": trade_date,
        "status": "pending",
        "submitted_by": user.username,
        "submitted_at": datetime.utcnow()
    }
    
    # Start the task in the background
    background_tasks.add_task(run_analysis_task, request_id, request.ticker.upper(), trade_date)
    
    return AnalyzeResponse(
        request_id=request_id,
        ticker=request.ticker.upper(),
        trade_date=trade_date,
        status="pending"
    )

@router.get("/status/{request_id}", response_model=AnalyzeResponse)
async def get_analysis_status(request_id: str, user = Depends(get_current_active_user)):
    """Get the status of an analysis request."""
    if request_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    result = analysis_results[request_id]
    
    return AnalyzeResponse(
        request_id=request_id,
        ticker=result["ticker"],
        trade_date=result["trade_date"],
        status=result["status"],
        result=result.get("result")
    )

@router.post("/backtest", response_model=BacktestResponse)
@limiter.limit("3/minute")
async def backtest(
    background_tasks: BackgroundTasks,
    request: BacktestRequest,
    user = Depends(get_current_active_user)
):
    """Start a backtest for a given ticker over a date range."""
    if request.end_date < request.start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")
    
    # Generate a request ID
    request_id = str(uuid.uuid4())
    
    # Calculate total days
    total_days = (request.end_date - request.start_date).days + 1
    
    # Store initial result
    analysis_results[request_id] = {
        "ticker": request.ticker.upper(),
        "start_date": request.start_date,
        "end_date": request.end_date,
        "status": "pending",
        "days_processed": 0,
        "total_days": total_days,
        "progress": 0.0,
        "submitted_by": user.username,
        "submitted_at": datetime.utcnow(),
        "commission_pct": request.commission_pct,
        "slippage_bps": request.slippage_bps
    }
    
    # Start the task in the background
    background_tasks.add_task(
        run_backtest_task, 
        request_id, 
        request.ticker.upper(), 
        request.start_date, 
        request.end_date,
        request.commission_pct,
        request.slippage_bps
    )
    
    return BacktestResponse(
        request_id=request_id,
        status="pending",
        ticker=request.ticker.upper(),
        start_date=request.start_date,
        end_date=request.end_date,
        total_days=total_days
    )

@router.get("/backtest/{request_id}", response_model=BacktestResponse)
async def get_backtest_status(request_id: str, user = Depends(get_current_active_user)):
    """Get the status of a backtest request."""
    if request_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Backtest not found")
    
    result = analysis_results[request_id]
    
    return BacktestResponse(
        request_id=request_id,
        status=result["status"],
        ticker=result["ticker"],
        start_date=result["start_date"],
        end_date=result["end_date"],
        days_processed=result["days_processed"],
        total_days=result["total_days"]
    )