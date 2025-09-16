from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import RemoveMessage, HumanMessage
from core.models import AgentState
from agents.market_analyst import MarketAnalyst
from agents.social_analyst import SocialAnalyst
from agents.news_analyst import NewsAnalyst
from agents.fundamentals_analyst import FundamentalsAnalyst
from agents.research_agent import ResearchAgent
from agents.execution_agent import ExecutionAgent
from agents.risk_agent import RiskAgent
from agents.portfolio_manager import PortfolioManager
from core.memory.simple_memory import SimpleMemory  # Correct import
from tools.toolkit import Toolkit
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import MessagesPlaceholder
from langchain_openai import ChatOpenAI
from core.checkpoint.postgres_checkpoint import get_postgres_checkpoint
from config import settings  # Use centralized config
import logging

logger = logging.getLogger(__name__)

def create_analyst_node(llm, toolkit, system_message, tools, output_field):
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a helpful AI assistant, collaborating with other assistants." \
         " Use the provided tools to progress towards answering the question." \
         " If you are unable to fully answer, that's OK; another assistant with different tools" \
         " will help where you left off. Execute what you can to make progress."
         " You have access to the following tools: {tool_names}.\n{system_message}" \
         " For your reference, the current date is {current_date}. The company we want to look at is {ticker}"),
        MessagesPlaceholder(variable_name="messages"),
    ])
    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
    chain = prompt | llm.bind_tools(tools)

    def analyst_node(state):
        try:
            prompt_with_data = prompt.partial(current_date=state["trade_date"], ticker=state["company_of_interest"])
            result = prompt_with_data.invoke(state["messages"])
            report = ""
            if not result.tool_calls:
                report = result.content
            return {"messages": [result], output_field: report}
        except Exception as e:
            logger.error(f"Error in analyst node: {e}")
            return {"messages": [], output_field: f"Error generating report: {e}"}
    return analyst_node

def create_research_manager(llm, memory):
    def research_manager_node(state):
        try:
            prompt = f"""As the Research Manager, your role is to critically evaluate the debate between the Bull and Bear analysts and make a definitive decision.
            Summarize the key points, then provide a clear recommendation: Buy, Sell, or Hold. Develop a detailed investment plan for the trader, including your rationale and strategic actions.
            
            Debate History:
            {state['investment_debate_state']['history']}"""
            response = llm.invoke(prompt)
            return {"investment_plan": response.content}
        except Exception as e:
            logger.error(f"Error in research manager: {e}")
            return {"investment_plan": f"Error generating investment plan: {e}"}
    return research_manager_node

def build_trading_graph():
    try:
        # Use centralized settings instead of config parameter
        config = settings
        
        # Initialize LLMs using settings
        deep_thinking_llm = ChatOpenAI(
            model=config.deep_think_llm,
            base_url=config.backend_url,
            temperature=0.1,
            api_key=config.openai_api_key
        )
        
        quick_thinking_llm = ChatOpenAI(
            model=config.quick_think_llm,
            base_url=config.backend_url,
            temperature=0.1,
            api_key=config.openai_api_key
        )
        
        # Initialize toolkit with settings
        toolkit = Toolkit(config.__dict__)
        
        # Initialize memories using SimpleMemory (correct class)
        bull_memory = SimpleMemory("bull_memory")
        bear_memory = SimpleMemory("bear_memory")
        trader_memory = SimpleMemory("trader_memory")
        invest_judge_memory = SimpleMemory("invest_judge_memory")
        risk_manager_memory = SimpleMemory("risk_manager_memory")
        
        # Create analyst nodes
        market_analyst_system_message = "You are a trading assistant specialized in analyzing financial markets. Your role is to select the most relevant technical indicators to analyze a stock's price action, momentum, and volatility. You must use your tools to get historical data and then generate a report with your findings, including a summary table."
        market_analyst_node = create_analyst_node(quick_thinking_llm, toolkit, market_analyst_system_message, [toolkit.get_yfinance_data, toolkit.get_technical_indicators], "market_report")
        
        social_analyst_system_message = "You are a social media analyst. Your job is to analyze social media posts and public sentiment for a specific company over the past week. Use your tools to find relevant discussions and write a comprehensive report detailing your analysis, insights, and implications for traders, including a summary table."
        social_analyst_node = create_analyst_node(quick_thinking_llm, toolkit, social_analyst_system_message, [toolkit.get_social_media_sentiment], "sentiment_report")
        
        news_analyst_system_message = "You are a news researcher analyzing recent news and trends over the past week. Write a comprehensive report on the current state of the world relevant for trading and macroeconomics. Use your tools to be comprehensive and provide detailed analysis, including a summary table."
        news_analyst_node = create_analyst_node(quick_thinking_llm, toolkit, news_analyst_system_message, [toolkit.get_finnhub_news, toolkit.get_macroeconomic_news], "news_report")
        
        fundamentals_analyst_system_message = "You are a researcher analyzing fundamental information about a company. Write a comprehensive report on the company's financials, insider sentiment, and transactions to gain a full view of its fundamental health, including a summary table."
        fundamentals_analyst_node = create_analyst_node(quick_thinking_llm, toolkit, fundamentals_analyst_system_message, [toolkit.get_fundamental_analysis], "fundamentals_report")
        
        # Create research nodes
        bull_researcher_node = ResearchAgent(quick_thinking_llm, "bull", bull_memory)
        bear_researcher_node = ResearchAgent(quick_thinking_llm, "bear", bear_memory)
        research_manager_node = create_research_manager(deep_thinking_llm, invest_judge_memory)
        
        # Create execution and risk nodes
        trader_node = ExecutionAgent(quick_thinking_llm, trader_memory)
        
        risky_node = RiskAgent(quick_thinking_llm, "Risky Analyst", risk_manager_memory)
        safe_node = RiskAgent(quick_thinking_llm, "Safe Analyst", risk_manager_memory)
        neutral_node = RiskAgent(quick_thinking_llm, "Neutral Analyst", risk_manager_memory)
        risk_manager_node = PortfolioManager(deep_thinking_llm, risk_manager_memory)
        
        # Create tool node
        all_tools = [
            toolkit.get_yfinance_data,
            toolkit.get_technical_indicators,
            toolkit.get_finnhub_news,
            toolkit.get_social_media_sentiment,
            toolkit.get_fundamental_analysis,
            toolkit.get_macroeconomic_news
        ]
        tool_node = ToolNode(all_tools)
        
        # Message clearing helper
        def delete_messages(state):
            return {"messages": [RemoveMessage(id=m.id) for m in state["messages"]] + [HumanMessage(content="Continue")]}
        msg_clear_node = delete_messages
        
        # Build the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("Market Analyst", market_analyst_node)
        workflow.add_node("Social Analyst", social_analyst_node)
        workflow.add_node("News Analyst", news_analyst_node)
        workflow.add_node("Fundamentals Analyst", fundamentals_analyst_node)
        workflow.add_node("tools", tool_node)
        workflow.add_node("Msg Clear", msg_clear_node)
        workflow.add_node("Bull Researcher", bull_researcher_node.step)
        workflow.add_node("Bear Researcher", bear_researcher_node.step)
        workflow.add_node("Research Manager", research_manager_node)
        workflow.add_node("Trader", trader_node.step)
        workflow.add_node("Risky Analyst", risky_node.step)
        workflow.add_node("Safe Analyst", safe_node.step)
        workflow.add_node("Neutral Analyst", neutral_node.step)
        workflow.add_node("Risk Judge", risk_manager_node.step)
        
        # Add edges (simplified - you'll need to add conditional logic)
        workflow.set_entry_point("Market Analyst")
        workflow.add_edge("Market Analyst", "Msg Clear")
        workflow.add_edge("Msg Clear", "Social Analyst")
        workflow.add_edge("Social Analyst", "News Analyst")
        workflow.add_edge("News Analyst", "Fundamentals Analyst")
        workflow.add_edge("Fundamentals Analyst", "Bull Researcher")
        workflow.add_edge("Bull Researcher", "Bear Researcher")
        workflow.add_edge("Bear Researcher", "Research Manager")
        workflow.add_edge("Research Manager", "Trader")
        workflow.add_edge("Trader", "Risky Analyst")
        workflow.add_edge("Risky Analyst", "Safe Analyst")
        workflow.add_edge("Safe Analyst", "Neutral Analyst")
        workflow.add_edge("Neutral Analyst", "Risk Judge")
        workflow.add_edge("Risk Judge", END)
        
        # Add tool edges
        workflow.add_edge("tools", "Market Analyst")
        workflow.add_edge("tools", "Social Analyst")
        workflow.add_edge("tools", "News Analyst")
        workflow.add_edge("tools", "Fundamentals Analyst")
        
        # Compile with checkpointing
        checkpointer = get_postgres_checkpoint()
        compiled_graph = workflow.compile(checkpointer=checkpointer)
        
        return compiled_graph
    except Exception as e:
        logger.error(f"Error building trading graph: {e}")
        raise