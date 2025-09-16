import asyncio
import json
import websockets
import logging
from typing import Callable, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MarketDataStream:
    """Real-time market data stream using WebSockets."""
    
    def __init__(self, symbols: List[str], api_key: str):
        self.symbols = symbols
        self.api_key = api_key
        self.ws = None
        self.callbacks = []
        self.running = False
        self.last_prices = {}  # Cache of last prices for each symbol
        
    async def connect(self):
        """Connect to the WebSocket endpoint."""
        # Using Finnhub as an example - replace with your preferred data provider
        uri = f"wss://ws.finnhub.io?token={self.api_key}"
        
        try:
            self.ws = await websockets.connect(uri)
            self.running = True
            logger.info(f"Connected to market data stream")
            
            # Subscribe to ticker data for all symbols
            for symbol in self.symbols:
                await self.ws.send(json.dumps({"type": "subscribe", "symbol": symbol}))
                logger.info(f"Subscribed to {symbol}")
            
            # Start the message handler
            asyncio.create_task(self._message_handler())
            
        except Exception as e:
            logger.error(f"Error connecting to market data stream: {e}")
            self.running = False
    
    async def _message_handler(self):
        """Handle incoming messages from the WebSocket."""
        while self.running and self.ws:
            try:
                message = await self.ws.recv()
                data = json.loads(message)
                
                # Process the data
                if data.get("type") == "trade":
                    for trade in data.get("data", []):
                        symbol = trade.get("s")
                        price = trade.get("p")
                        timestamp = trade.get("t")
                        volume = trade.get("v")
                        
                        # Update last known price
                        self.last_prices[symbol] = price
                        
                        # Create a price update event
                        event = {
                            "symbol": symbol,
                            "price": price,
                            "timestamp": datetime.fromtimestamp(timestamp / 1000),
                            "volume": volume
                        }
                        
                        # Notify all callbacks
                        for callback in self.callbacks:
                            callback(event)
            
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
    
    def register_callback(self, callback: Callable):
        """Register a callback function to receive price updates."""
        self.callbacks.append(callback)
        
    def get_last_price(self, symbol: str) -> Optional[float]:
        """Get the last known price for a symbol."""
        return self.last_prices.get(symbol)
    
    async def disconnect(self):
        """Disconnect from the WebSocket."""
        self.running = False
        if self.ws:
            for symbol in self.symbols:
                await self.ws.send(json.dumps({"type": "unsubscribe", "symbol": symbol}))
            await self.ws.close()
            logger.info("Disconnected from market data stream")