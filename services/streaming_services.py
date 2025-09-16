import asyncio
from typing import Dict, List, Any, Callable
import logging

logger = logging.getLogger(__name__)

class StreamingService:
    """Service for managing real-time data streams and dispatching updates."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.callbacks: List[Callable] = []
        self.streamer = None
        self.data_source = config.get('data_source', 'yahoo')  # 'yahoo' or 'polygon'
        
        # Initialize the appropriate streamer
        self._init_streamer()
    
    def _init_streamer(self):
        """Initialize the data streamer based on configuration."""
        try:
            if self.data_source == 'polygon':
                from tools.streaming.polygon_stream import create_polygon_stream
                self.streamer = create_polygon_stream(self.config)
            elif self.data_source == 'yahoo':
                from tools.streaming.yahoo_stream import create_yahoo_stream
                self.streamer = create_yahoo_stream(self.config)
            else:
                from tools.streaming.websocket_client import create_market_stream
                self.streamer = create_market_stream(self.config)
                
            logger.info(f"Initialized {self.data_source} streamer")
        except Exception as e:
            logger.error(f"Failed to initialize streamer: {e}")
            # Fallback to mock streamer
            from tools.streaming.websocket_client import create_market_stream
            self.streamer = create_market_stream(self.config)
    
    def start_stream(self, symbols: List[str]) -> bool:
        """Start a market data stream for the specified symbols."""
        try:
            if not self.streamer:
                return False
            
            # Register our internal callback
            self.streamer.register_callback(self._on_market_update)
            
            # Start the stream
            success = self.streamer.start_stream(symbols)
            if success:
                logger.info(f"Started {self.data_source} streaming for {symbols}")
            return success
            
        except Exception as e:
            logger.error(f"Error starting {self.data_source} stream: {e}")
            return False
    
    def stop_stream(self):
        """Stop the streaming."""
        try:
            if self.streamer:
                self.streamer.stop_stream()
        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
    
    def register_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for market updates."""
        self.callbacks.append(callback)
    
    def _on_market_update(self, update: Dict[str, Any]):
        """Handle market data updates and forward to registered callbacks."""
        # Add source information
        update['data_source'] = self.data_source
        
        # Process the update and notify registered callbacks
        for callback in self.callbacks:
            try:
                callback(update)
            except Exception as e:
                logger.error(f"Error in callback: {e}")
    
    def get_latest_data(self, symbol: str) -> Dict[str, Any]:
        """Get latest data for a symbol."""
        if self.streamer:
            return self.streamer.get_latest_data(symbol)
        return {}
    
    def is_streaming(self) -> bool:
        """Check if streaming is active."""
        return self.streamer and self.streamer.is_connected()
    
    def switch_data_source(self, source: str):
        """Switch data source (yahoo, polygon, or mock)."""
        if source != self.data_source:
            # Stop current stream
            self.stop_stream()
            
            # Update source and reinitialize
            self.data_source = source
            self._init_streamer()
            
            logger.info(f"Switched to {source} data source")