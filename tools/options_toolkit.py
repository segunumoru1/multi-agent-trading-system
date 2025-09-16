import yfinance as yf
from langchain_core.tools import tool
from typing import Dict, Any, List
import pandas as pd
import logging

logger = logging.getLogger(__name__)

@tool
def get_options_chain(ticker: str, expiration_date: str) -> str:
    """Retrieve the options chain for a given ticker and expiration date."""
    try:
        stock = yf.Ticker(ticker.upper())
        options = stock.option_chain(expiration_date)
        
        calls_df = options.calls.head(10)  # Top 10 calls
        puts_df = options.puts.head(10)   # Top 10 puts
        
        result = f"Options Chain for {ticker.upper()} - Expiration: {expiration_date}\n\n"
        result += "CALLS:\n" + calls_df.to_csv() + "\n\n"
        result += "PUTS:\n" + puts_df.to_csv()
        
        return result
    except Exception as e:
        logger.error(f"Error fetching options chain: {e}")
        return f"Error fetching options chain: {e}"

@tool
def analyze_options_sentiment(ticker: str, expiration_date: str) -> str:
    """Analyze options sentiment by comparing open interest and volume."""
    try:
        stock = yf.Ticker(ticker.upper())
        options = stock.option_chain(expiration_date)
        
        calls = options.calls
        puts = options.puts
        
        total_call_oi = calls['openInterest'].sum()
        total_put_oi = puts['openInterest'].sum()
        total_call_vol = calls['volume'].sum()
        total_put_vol = puts['volume'].sum()
        
        put_call_ratio = total_put_oi / total_call_oi if total_call_oi > 0 else float('inf')
        
        sentiment = "Bullish" if put_call_ratio < 0.7 else "Bearish" if put_call_ratio > 1.3 else "Neutral"
        
        result = f"Options Sentiment Analysis for {ticker.upper()}:\n"
        result += f"Put/Call Ratio: {put_call_ratio:.2f}\n"
        result += f"Overall Sentiment: {sentiment}\n"
        result += f"Total Call OI: {total_call_oi}\n"
        result += f"Total Put OI: {total_put_oi}\n"
        result += f"Total Call Volume: {total_call_vol}\n"
        result += f"Total Put Volume: {total_put_vol}"
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing options sentiment: {e}")
        return f"Error analyzing options sentiment: {e}"

class OptionsToolkit:
    def __init__(self, config):
        self.config = config
        self.get_options_chain = get_options_chain
        self.analyze_options_sentiment = analyze_options_sentiment