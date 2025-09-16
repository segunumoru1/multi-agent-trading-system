from agents.base_agent import BaseAgent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class NewsAnalyst(BaseAgent):
    name = "news_analyst"
    role = "analyze_news"

    def __init__(self, llm, tools=None):
        super().__init__(tools)
        self.llm = llm

    def step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system",
                 "You are a news researcher analyzing recent news and trends over the past week. Write a comprehensive report on the current state of the world relevant for trading and macroeconomics. Use your tools to be comprehensive and provide detailed analysis, including a summary table."
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
                return {"news_report": result.content, "messages": [result]}
        except Exception as e:
            logger.error(f"Error in NewsAnalyst step: {e}")
            return {"news_report": f"Error generating news report: {e}", "messages": []}