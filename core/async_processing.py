import asyncio
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

async def async_analyze_multiple_stocks(tickers: List[str], trade_date: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Asynchronously analyze multiple stocks."""
    from graphs.trading_graph import build_trading_graph
    from core.evaluation import SignalProcessor
    from langchain_core.messages import HumanMessage
    from core.models import AgentState, InvestDebateState, RiskDebateState
    from langchain_openai import ChatOpenAI
    
    async def analyze_single_stock(ticker: str):
        try:
            graph_input = AgentState(
                messages=[HumanMessage(content=f"Analyze {ticker} for trading on {trade_date}")],
                company_of_interest=ticker.upper(),
                trade_date=trade_date,
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
            
            return {
                "ticker": ticker.upper(),
                "trade_date": trade_date,
                "signal": signal,
                "final_trade_decision": final_state.get("final_trade_decision", ""),
                "success": True
            }
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}")
            return {
                "ticker": ticker.upper(),
                "trade_date": trade_date,
                "signal": "ERROR",
                "final_trade_decision": f"Error: {e}",
                "success": False
            }
    
    tasks = [analyze_single_stock(ticker) for ticker in tickers]
    results = await asyncio.gather(*tasks)
    return results