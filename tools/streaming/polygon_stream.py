"""
Polygon.io WebSocket client for real-time market data.
Requires: pip install polygon-api-client websockets
"""
import asyncio
import json
import logging
from typing import List, Dict, Any, Callable, Optional
import websockets
from polygon import WebSocketClient
from polygon.websocket.models import WebSocketMessage
from polygon.enums import Feed, AssetClass

logger = logging.getLogger(__name__)

class PolygonStreamer:
    """Polygon.io WebSocket client for real-time market data."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.callbacks: List[Callable] = []
        self.is_streaming = False
        self.symbols: List[str] = []
        self.client: Optional[WebSocketClient] = None
        
        # Get API key from config or secrets
        self.api_key = config.get('polygon_api_key') or get_secret('POLYGON_API_KEY')
    
    def register_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for market data updates."""
        self.callbacks.append(callback)
        logger.info(f"Registered Polygon callback: {callback.__name__}")
    
    def unregister_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Unregister a callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            logger.info(f"Unregistered callback: {callback.__name__}")
    
    def start_stream(self, symbols: List[str]) -> bool:
        """Start Polygon WebSocket stream for specified symbols."""
        try:
            if self.is_streaming:
                logger.warning("Polygon stream already running")
                return True
            
            self.symbols = symbols
            self.is_streaming = True
            
            # Initialize Polygon client
            self.client = WebSocketClient(
                api_key=self.api_key,
                feed=Feed.RealTime,
                market=AssetClass.Stocks,
                verbose=False
            )
            
            # Register message handler
            self.client.subscribe(*symbols)
            self.client.run_async(self._handle_message)
            
            logger.info(f"Started Polygon streaming for symbols: {symbols}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Polygon stream: {e}")
            return False
    
    def stop_stream(self):
        """Stop the WebSocket stream."""
        try:
            self.is_streaming = False
            if self.client:
                self.client.close()
                self.client = None
            logger.info("Stopped Polygon streaming")
        except Exception as e:
            logger.error(f"Error stopping Polygon stream: {e}")
    
    async def _handle_message(self, message: WebSocketMessage):
        """Handle incoming WebSocket messages."""
        try:
            if not self.is_streaming:
                return
            
            # Process different message types
            if hasattr(message, 'symbol') and hasattr(message, 'price'):
                update = {
                    'symbol': message.symbol,
                    'price': float(message.price),
                    'timestamp': time.time(),
                    'volume': getattr(message, 'volume', 0),
                    'change_percent': getattr(message, 'change_percent', 0),
                    'source': 'polygon',
                    'is_realtime': True,
                    'last_updated': datetime.now().isoformat()
                }
                
                # Notify all callbacks
                for callback in self.callbacks:
                    try:
                        callback(update)
                    except Exception as e:
                        logger.error(f"Error in callback {callback.__name__}: {e}")
                        
        except Exception as e:
            logger.error(f"Error handling Polygon message: {e}")
    
    def get_latest_data(self, symbol: str) -> Dict[str, Any]:
        """Get latest data for a symbol (would need REST API call)."""
        # For now, return placeholder - implement REST API call if needed
        return {
            'symbol': symbol,
            'price': 0.0,
            'timestamp': time.time(),
            'source': 'polygon',
            'is_realtime': True
        }
    
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self.is_streaming and self.client is not None

# Factory function
def create_polygon_stream(config: Dict[str, Any]) -> PolygonStreamer:
    """Create a Polygon streamer instance."""
    return PolygonStreamer(config)