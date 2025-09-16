from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class Evaluation(BaseModel):
    reasoning_quality: int = Field(description="Score 1-10 on the coherence and logic.")
    evidence_based_score: int = Field(description="Score 1-10 on citation of evidence from reports.")
    actionability_score: int = Field(description="Score 1-10 on how clear and actionable the decision is.")
    justification: str = Field(description="A brief justification for the scores.")

class Audit(BaseModel):
    is_consistent: bool = Field(description="Whether the report is factually consistent with the data.")
    discrepancies: list[str] = Field(description="A list of any identified discrepancies.")
    justification: str = Field(description="A brief justification for the audit result.")

class SignalProcessor:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def process_signal(self, full_signal: str) -> str:
        try:
            messages = [
                ("system", "You are an assistant designed to extract the final investment decision: SELL, BUY, or HOLD from a financial report. Respond with only the single-word decision."),
                ("human", full_signal),
            ]
            result = self.llm.invoke(messages).content.strip().upper()
            if result in ["BUY", "SELL", "HOLD"]:
                return result
            return "ERROR_UNPARSABLE_SIGNAL"
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
            return "ERROR_UNPARSABLE_SIGNAL"

class Reflector:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.reflection_prompt = """You are an expert financial analyst. Review the trading decision/analysis, the market context, and the financial outcome.
        - First, determine if the decision was correct or incorrect based on the outcome.
        - Analyze the most critical factors that led to the success or failure.
        - Finally, formulate a concise, one-sentence lesson or heuristic that can be used to improve future decisions in similar situations.
        
        Market Context & Analysis: {situation}
        Outcome (Profit/Loss): {returns_losses}"""

    def reflect(self, current_state: Dict[str, Any], returns_losses: float, memory):
        try:
            situation = f"Reports: {current_state['market_report']} {current_state['sentiment_report']} {current_state['news_report']} {current_state['fundamentals_report']}\nDecision/Analysis Text: {current_state.get('investment_debate_state', {}).get('history', '')}"
            prompt = self.reflection_prompt.format(situation=situation, returns_losses=returns_losses)
            result = self.llm.invoke(prompt).content
            memory.add_situations([(situation, result)])
        except Exception as e:
            logger.error(f"Error in reflection: {e}")