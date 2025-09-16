import asyncio
from typing import Dict, List, Any, Callable
from tools.streaming.websocket_client import MarketDataStream
import os
from core.secrets import get_secret

class StreamingService:
    """Service for managing real-time data streams and dispatching updates."""
    
    def __init__(self):
        self.streams = {}  # Dictionary of active streams
        self.symbols = set()  # Set of all subscribed symbols
        self.api_key = get_secret("FINNHUB_API_KEY")
        
    async def start_stream(self, symbols: List[str]):
        """Start a market data stream for the specified symbols."""
        # Add new symbols to the master set
        self.symbols.update(symbols)
        
        # Create a new stream with all symbols
        stream = MarketDataStream(list(self.symbols), self.api_key)
        await stream.connect()
        
        # Store the stream
        stream_id = f"stream_{len(self.streams)}"
        self.streams[stream_id] = stream
        
        return stream_id
    
    def register_price_handler(self, stream_id: str, handler: Callable):
        """Register a handler function for price updates."""
        if stream_id in self.streams:
            self.streams[stream_id].register_callback(handler)
            return True
        return False
    
    async def stop_stream(self, stream_id: str):
        """Stop and clean up a market data stream."""
        if stream_id in self.streams:
            await self.streams[stream_id].disconnect()
            del self.streams[stream_id]
            return True
        return False
    
    def get_latest_prices(self) -> Dict[str, float]:
        """Get the latest prices for all subscribed symbols."""
        prices = {}
        for stream in self.streams.values():
            for symbol in self.symbols:
                price = stream.get_last_price(symbol)
                if price is not None:
                    prices[symbol] = price
        return prices