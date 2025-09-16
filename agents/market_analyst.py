from agents.base_agent import BaseAgent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from typing import Dict, Any

class MarketAnalyst(BaseAgent):
    name = "market_analyst"
    role = "analyze_price_action"

    def __init__(self, llm, tools=None):
        super().__init__(tools)
        self.llm = llm

    def step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are a trading assistant specialized in analyzing financial markets. Your role is to select the most relevant technical indicators to analyze a stock's price action, momentum, and volatility. You must use your tools to get historical data and then generate a report with your findings, including a summary table."
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
            # Agent needs to use tools
            return {"messages": [result]}
        else:
            # Agent has final report
            return {"market_report": result.content, "messages": [result]}