from agents.base_agent import BaseAgent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class FundamentalsAnalyst(BaseAgent):
    name = "fundamentals_analyst"
    role = "analyze_fundamentals"

    def __init__(self, llm, tools=None):
        super().__init__(tools)
        self.llm = llm

    def step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system",
                 "You are a researcher analyzing fundamental information about a company. Write a comprehensive report on the company's financials, insider sentiment, and transactions to gain a full view of its fundamental health, including a summary table."
                 " For your reference, the current date is {current_date}. The company we want to look at is {ticker}"),
                MessagesPlaceholder(variable_name="messages"),
            ])
            
            prompt_with_data = prompt.partial(
                current_date=state["trade_date"], 
                ticker=state["company_of_interest"]
            )
            
            chain = prompt_with_data | self.llm.bind_tools(self.tools)
            result = chain.invoke(state["messages"])
            
            if result.tool_calls:
                return {"messages": [result]}
            else:
                return {"fundamentals_report": result.content, "messages": [result]}
        except Exception as e:
            logger.error(f"Error in FundamentalsAnalyst step: {e}")
            return {"fundamentals_report": f"Error generating fundamentals report: {e}", "messages": []}