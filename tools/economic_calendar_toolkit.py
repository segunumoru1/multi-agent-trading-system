import requests
from langchain_core.tools import tool
from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

@tool
def get_economic_events(start_date: str, end_date: str) -> str:
    """Retrieve economic events from Alpha Vantage or similar API."""
    try:
        # Using Alpha Vantage API (requires API key)
        api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
        if not api_key:
            return "Alpha Vantage API key not configured."
        
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&topics=financial_markets&apikey={api_key}&time_from={start_date}T00:00:00&time_to={end_date}T23:59:59"
        
        response = requests.get(url)
        data = response.json()
        
        if "feed" not in data:
            return "No economic events found."
        
        events = []
        for item in data["feed"][:10]:  # Limit to 10 events
            events.append(f"Title: {item['title']}\nSummary: {item['summary']}\nSentiment: {item['overall_sentiment_label']}")
        
        return "\n\n".join(events)
    except Exception as e:
        logger.error(f"Error fetching economic events: {e}")
        return f"Error fetching economic events: {e}"

@tool
def get_fed_speeches(start_date: str, end_date: str) -> str:
    """Retrieve recent Federal Reserve speeches and statements."""
    try:
        # Using FRED API or web scraping for Fed speeches
        # This is a simplified example - in practice, you'd use a proper API
        url = "https://www.federalreserve.gov/newsevents/speeches.htm"
        response = requests.get(url)
        
        # Parse HTML to extract recent speeches (simplified)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        speeches = []
        for item in soup.find_all('div', class_='eventlist__event')[:5]:
            title = item.find('h3').text.strip()
            date = item.find('time')['datetime']
            speeches.append(f"Date: {date}\nTitle: {title}")
        
        return "\n\n".join(speeches) if speeches else "No recent Fed speeches found."
    except Exception as e:
        logger.error(f"Error fetching Fed speeches: {e}")
        return f"Error fetching Fed speeches: {e}"

@tool
def get_economic_indicators(indicator: str, start_date: str, end_date: str) -> str:
    """Retrieve economic indicators from Alpha Vantage API."""
    try:
        api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
        if not api_key:
            return "Alpha Vantage API key not configured."
        
        # Map common indicators to Alpha Vantage functions
        indicator_map = {
            "gdp": "REAL_GDP",
            "unemployment": "UNEMPLOYMENT",
            "inflation": "CPI",  # Consumer Price Index as proxy for inflation
            "interest_rate": "FEDERAL_FUNDS_RATE"
        }
        
        function = indicator_map.get(indicator.lower())
        if not function:
            return f"Unsupported indicator: {indicator}. Supported: {', '.join(indicator_map.keys())}"
        
        url = f"https://www.alphavantage.co/query?function={function}&apikey={api_key}"
        
        response = requests.get(url)
        data = response.json()
        
        if "data" not in data:
            return f"No data found for {indicator}."
        
        indicators = []
        for item in data["data"]:
            date = item["date"]
            value = item["value"]
            if start_date <= date <= end_date:
                indicators.append(f"Date: {date}\nValue: {value}")
        
        return "\n\n".join(indicators[:10]) if indicators else f"No {indicator} data in the specified date range."
    except Exception as e:
        logger.error(f"Error fetching economic indicators: {e}")
        return f"Error fetching economic indicators: {e}"

class EconomicCalendarToolkit:
    def __init__(self, config):
        self.config = config
        self.get_economic_events = get_economic_events
        self.get_fed_speeches = get_fed_speeches
        self.get_economic_indicators = get_economic_indicators