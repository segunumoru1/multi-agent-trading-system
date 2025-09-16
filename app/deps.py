import os
import uuid
import datetime
from typing import Dict, Any
from graphs.trading_graph import run_analysis

# Simple in-memory store (replace with Redis / DB in production)
_RUN_CACHE: Dict[str, Dict[str, Any]] = {}

def get_runtime_config() -> Dict[str, Any]:
    return {
        "env": os.getenv("ENV", "dev"),
        "model_deep": os.getenv("DEEP_MODEL", "gpt-4o"),
        "model_quick": os.getenv("QUICK_MODEL", "gpt-4o-mini"),
        "max_debate_rounds": int(os.getenv("MAX_DEBATE_ROUNDS", "2")),
        "max_risk_rounds": int(os.getenv("MAX_RISK_ROUNDS", "1")),
    }

def perform_analysis(ticker: str, trade_date: str | None):
    result = run_analysis(ticker, trade_date)
    run_id = uuid.uuid4().hex
    result["run_id"] = run_id
    _RUN_CACHE[run_id] = result
    return result

def get_run(run_id: str):
    return _RUN_CACHE.get(run_id)

def backtest(ticker: str, start_date: datetime.date, end_date: datetime.date):
    cur = start_date
    results = []
    while cur <= end_date:
        daily = run_analysis(ticker, cur.isoformat())
        results.append({
            "trade_date": cur,
            "signal": daily["signal"],
            "final_trade_decision": daily["final_trade_decision"]
        })
        cur += datetime.timedelta(days=1)
    return results