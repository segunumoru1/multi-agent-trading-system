"""
WebSocket client for real-time market data streaming.
This is a basic implementation that can be extended with actual WebSocket connections.
"""
from typing import List, Dict, Any, Callable, Optional
import logging
import asyncio
import time
import random

logger = logging.getLogger(__name__)

class MarketDataStream:
    """WebSocket client for streaming market data."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.callbacks: List[Callable] = []
        self.is_streaming = False
        self.stream_task: Optional[asyncio.Task] = None
        self.symbols: List[str] = []
    
    def register_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for market data updates."""
        self.callbacks.append(callback)
        logger.info(f"Registered callback: {callback.__name__}")
    
    def unregister_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Unregister a callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            logger.info(f"Unregistered callback: {callback.__name__}")
    
    def start_stream(self, symbols: List[str]) -> bool:
        """Start streaming market data for specified symbols."""
        try:
            if self.is_streaming:
                logger.warning("Stream already running")
                return True
            
            self.symbols = symbols
            self.is_streaming = True
            
            # Start the streaming task
            self.stream_task = asyncio.create_task(self._stream_data())
            
            logger.info(f"Started streaming for symbols: {symbols}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start stream: {e}")
            return False
    
    def stop_stream(self):
        """Stop the streaming."""
        try:
            self.is_streaming = False
            if self.stream_task:
                self.stream_task.cancel()
                self.stream_task = None
            logger.info("Stopped streaming")
        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
    
    async def _stream_data(self):
        """Simulate streaming market data (replace with real WebSocket implementation)."""
        logger.info("Starting simulated market data stream")
        
        while self.is_streaming:
            try:
                # Simulate market data updates
                for symbol in self.symbols:
                    # Generate mock price data
                    price_change = random.uniform(-0.02, 0.02)  # -2% to +2%
                    base_price = self._get_base_price(symbol)
                    new_price = base_price * (1 + price_change)
                    
                    update = {
                        'symbol': symbol,
                        'price': round(new_price, 2),
                        'timestamp': time.time(),
                        'volume': random.randint(1000, 10000),
                        'change_percent': round(price_change * 100, 2)
                    }
                    
                    # Notify all callbacks
                    for callback in self.callbacks:
                        try:
                            callback(update)
                        except Exception as e:
                            logger.error(f"Error in callback {callback.__name__}: {e}")
                
                # Wait before next update (simulate real-time delay)
                await asyncio.sleep(1)  # 1 second delay
                
            except asyncio.CancelledError:
                logger.info("Streaming task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in streaming loop: {e}")
                await asyncio.sleep(5)  # Wait before retry
    
    def _get_base_price(self, symbol: str) -> float:
        """Get base price for a symbol (mock implementation)."""
        # Mock base prices - replace with real data source
        base_prices = {
            'AAPL': 150.0,
            'MSFT': 300.0,
            'NVDA': 400.0,
            'GOOGL': 2500.0,
            'TSLA': 200.0
        }
        return base_prices.get(symbol, 100.0)
    
    def get_latest_data(self, symbol: str) -> Dict[str, Any]:
        """Get the latest data for a symbol."""
        # Mock implementation - replace with real data retrieval
        return {
            'symbol': symbol,
            'price': self._get_base_price(symbol),
            'timestamp': time.time(),
            'volume': random.randint(1000, 10000)
        }
    
    def is_connected(self) -> bool:
        """Check if the stream is connected."""
        return self.is_streaming

# Factory function for creating stream instances
def create_market_stream(config: Dict[str, Any]) -> MarketDataStream:
    """Create a new market data stream instance."""
    return MarketDataStream(config)