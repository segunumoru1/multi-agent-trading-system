from agents.base_agent import BaseAgent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class SocialAnalyst(BaseAgent):
    name = "social_analyst"
    role = "analyze_sentiment"

    def __init__(self, llm, tools=None):
        super().__init__(tools)
        self.llm = llm

    def step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system",
                 "You are a social media analyst. Your job is to analyze social media posts and public sentiment for a specific company over the past week. Use your tools to find relevant discussions and write a comprehensive report detailing your analysis, insights, and implications for traders, including a summary table."
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
                return {"sentiment_report": result.content, "messages": [result]}
        except Exception as e:
            logger.error(f"Error in SocialAnalyst step: {e}")
            return {"sentiment_report": f"Error generating sentiment report: {e}", "messages": []}