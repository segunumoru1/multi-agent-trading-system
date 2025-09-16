"""
Yahoo Finance data streamer using polling to simulate real-time updates.
Note: Yahoo Finance data is delayed and not true real-time.
"""
import asyncio
import logging
from typing import List, Dict, Any, Callable, Optional
import time
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class YahooFinanceStreamer:
    """Yahoo Finance data streamer using polling."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.callbacks: List[Callable] = []
        self.is_streaming = False
        self.stream_task: Optional[asyncio.Task] = None
        self.symbols: List[str] = []
        self.last_prices: Dict[str, float] = {}
        self.poll_interval = config.get('yahoo_poll_interval', 60)  # Default 60 seconds
    
    def register_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for market data updates."""
        self.callbacks.append(callback)
        logger.info(f"Registered Yahoo Finance callback: {callback.__name__}")
    
    def unregister_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Unregister a callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            logger.info(f"Unregistered callback: {callback.__name__}")
    
    def start_stream(self, symbols: List[str]) -> bool:
        """Start polling Yahoo Finance data for specified symbols."""
        try:
            if self.is_streaming:
                logger.warning("Yahoo Finance stream already running")
                return True
            
            self.symbols = symbols
            self.is_streaming = True
            
            # Start the polling task
            self.stream_task = asyncio.create_task(self._poll_data())
            
            logger.info(f"Started Yahoo Finance polling for symbols: {symbols}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Yahoo Finance stream: {e}")
            return False
    
    def stop_stream(self):
        """Stop the polling."""
        try:
            self.is_streaming = False
            if self.stream_task:
                self.stream_task.cancel()
                self.stream_task = None
            logger.info("Stopped Yahoo Finance polling")
        except Exception as e:
            logger.error(f"Error stopping Yahoo Finance stream: {e}")
    
    async def _poll_data(self):
        """Poll Yahoo Finance data periodically."""
        logger.info("Starting Yahoo Finance data polling")
        
        while self.is_streaming:
            try:
                # Fetch data for all symbols
                for symbol in self.symbols:
                    try:
                        # Get latest data from Yahoo Finance
                        ticker = yf.Ticker(symbol)
                        data = ticker.history(period="1d", interval="1m")
                        
                        if not data.empty:
                            latest = data.iloc[-1]
                            current_price = latest['Close']
                            
                            # Calculate change
                            prev_price = self.last_prices.get(symbol, current_price)
                            change_percent = ((current_price - prev_price) / prev_price) * 100 if prev_price != 0 else 0
                            
                            update = {
                                'symbol': symbol,
                                'price': round(float(current_price), 2),
                                'timestamp': time.time(),
                                'volume': int(latest.get('Volume', 0)),
                                'change_percent': round(change_percent, 2),
                                'source': 'yahoo_finance',
                                'is_realtime': False,  # Yahoo data is delayed
                                'last_updated': datetime.now().isoformat()
                            }
                            
                            # Update last price
                            self.last_prices[symbol] = current_price
                            
                            # Notify all callbacks
                            for callback in self.callbacks:
                                try:
                                    callback(update)
                                except Exception as e:
                                    logger.error(f"Error in callback {callback.__name__}: {e}")
                        
                    except Exception as e:
                        logger.error(f"Error fetching data for {symbol}: {e}")
                
                # Wait before next poll
                await asyncio.sleep(self.poll_interval)
                
            except asyncio.CancelledError:
                logger.info("Yahoo Finance polling task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in Yahoo Finance polling loop: {e}")
                await asyncio.sleep(30)  # Wait before retry
    
    def get_latest_data(self, symbol: str) -> Dict[str, Any]:
        """Get the latest cached data for a symbol."""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")
            
            if not data.empty:
                latest = data.iloc[-1]
                return {
                    'symbol': symbol,
                    'price': round(float(latest['Close']), 2),
                    'timestamp': time.time(),
                    'volume': int(latest.get('Volume', 0)),
                    'source': 'yahoo_finance',
                    'is_realtime': False
                }
        except Exception as e:
            logger.error(f"Error getting latest data for {symbol}: {e}")
        
        return {
            'symbol': symbol,
            'price': self.last_prices.get(symbol, 0),
            'timestamp': time.time(),
            'source': 'yahoo_finance',
            'is_realtime': False
        }
    
    def is_connected(self) -> bool:
        """Check if polling is active."""
        return self.is_streaming

# Factory function
def create_yahoo_stream(config: Dict[str, Any]) -> YahooFinanceStreamer:
    """Create a Yahoo Finance streamer instance."""
    return YahooFinanceStreamer(config)