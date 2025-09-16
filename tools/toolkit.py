import yfinance as yf
import finnhub
import pandas as pd
from datetime import datetime, timedelta
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from stockstats import wrap as stockstats_wrap
import os
import logging
from tools.options_toolkit import OptionsToolkit
from tools.economic_calendar_toolkit import EconomicCalendarToolkit
from tools.alternative_data_toolkit import AlternativeDataToolkit
from core.cache.redis_cache import cached_yfinance_data
from tools.portfolio_optimization_toolkit import PortfolioOptimizationToolkit

logger = logging.getLogger(__name__)
tavily_tool = TavilySearchResults(max_results=3)

@cached_yfinance_data
@tool
def get_yfinance_data(symbol: str, start_date: str, end_date: str) -> str:
    """Retrieve the stock price data for a given ticker symbol from Yahoo Finance."""
    try:
        ticker = yf.Ticker(symbol.upper())
        data = ticker.history(start=start_date, end=end_date)
        if data.empty:
            return f"No data found for symbol '{symbol}' between {start_date} and {end_date}"
        return data.to_csv()
    except Exception as e:
        logger.error(f"Error fetching Yahoo Finance data: {e}")
        return f"Error fetching Yahoo Finance data: {e}"

@tool
def get_technical_indicators(symbol: str, start_date: str, end_date: str) -> str:
    """Retrieve key technical indicators for a stock using stockstats library."""
    try:
        df = yf.download(symbol, start=start_date, end=end_date, progress=False)
        if df.empty:
            return "No data to calculate indicators."
        stock_df = stockstats_wrap(df)
        indicators = stock_df[['macd', 'rsi_14', 'boll', 'boll_ub', 'boll_lb', 'close_50_sma', 'close_200_sma']]
        return indicators.tail().to_csv()
    except Exception as e:
        logger.error(f"Error calculating stockstats indicators: {e}")
        return f"Error calculating stockstats indicators: {e}"

@tool
def get_finnhub_news(ticker: str, start_date: str, end_date: str) -> str:
    """Get company news from Finnhub within a date range."""
    try:
        finnhub_client = finnhub.Client(api_key=os.environ["FINNHUB_API_KEY"])
        news_list = finnhub_client.company_news(ticker, _from=start_date, to=end_date)
        news_items = []
        for news in news_list[:5]:
            news_items.append(f"Headline: {news['headline']}\nSummary: {news['summary']}")
        return "\n\n".join(news_items) if news_items else "No Finnhub news found."
    except Exception as e:
        logger.error(f"Error fetching Finnhub news: {e}")
        return f"Error fetching Finnhub news: {e}"

@tool
def get_social_media_sentiment(ticker: str, trade_date: str) -> str:
    """Performs a live web search for social media sentiment regarding a stock."""
    try:
        query = f"social media sentiment and discussions for {ticker} stock around {trade_date}"
        return tavily_tool.invoke({"query": query})
    except Exception as e:
        logger.error(f"Error fetching social media sentiment: {e}")
        return f"Error fetching social media sentiment: {e}"

@tool
def get_fundamental_analysis(ticker: str, trade_date: str) -> str:
    """Performs a live web search for recent fundamental analysis of a stock."""
    try:
        query = f"fundamental analysis and key financial metrics for {ticker} stock published around {trade_date}"
        return tavily_tool.invoke({"query": query})
    except Exception as e:
        logger.error(f"Error fetching fundamental analysis: {e}")
        return f"Error fetching fundamental analysis: {e}"

@tool
def get_macroeconomic_news(trade_date: str) -> str:
    """Performs a live web search for macroeconomic news relevant to the stock market."""
    try:
        query = f"macroeconomic news and market trends affecting the stock market on {trade_date}"
        return tavily_tool.invoke({"query": query})
    except Exception as e:
        logger.error(f"Error fetching macroeconomic news: {e}")
        return f"Error fetching macroeconomic news: {e}"

class Toolkit:
    def __init__(self, config):
        self.config = config
        self.get_yfinance_data = get_yfinance_data
        self.get_technical_indicators = get_technical_indicators
        self.get_finnhub_news = get_finnhub_news
        self.get_social_media_sentiment = get_social_media_sentiment
        self.get_fundamental_analysis = get_fundamental_analysis
        self.get_macroeconomic_news = get_macroeconomic_news
        self.options_toolkit = OptionsToolkit(config)
        self.get_options_chain = self.options_toolkit.get_options_chain
        self.analyze_options_sentiment = self.options_toolkit.analyze_options_sentiment
        self.economic_toolkit = EconomicCalendarToolkit(config)
        self.get_economic_events = self.economic_toolkit.get_economic_events
        self.get_fed_speeches = self.economic_toolkit.get_fed_speeches
        self.alternative_toolkit = AlternativeDataToolkit(config)
        self.get_satellite_imagery_data = self.alternative_toolkit.get_satellite_imagery_data
        self.get_credit_card_spending_data = self.alternative_toolkit.get_credit_card_spending_data
        self.get_web_traffic_data = self.alternative_toolkit.get_web_traffic_data
        self.portfolio_toolkit = PortfolioOptimizationToolkit(config)
        self.optimize_portfolio = self.portfolio_toolkit.optimize_portfolio
        self.calculate_portfolio_risk_metrics = self.portfolio_toolkit.calculate_portfolio_risk_metrics