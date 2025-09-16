from core.services.service_manager import get_service_manager
from typing import Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)

class StreamingManager:
    """Manages real-time data streaming for the trading system."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.service_manager = get_service_manager(config)
        self.callbacks = []
    
    def start_streaming(self, symbols: list):
        """Start streaming market data."""
        streaming_service = self.service_manager.get_service('streaming')
        if streaming_service:
            success = streaming_service.start_stream(symbols)
            if success:
                logger.info(f"Started streaming for symbols: {symbols}")
                # Register callback for real-time updates
                streaming_service.register_callback(self._on_market_update)
            return success
        return False
    
    def register_callback(self, callback: Callable):
        """Register a callback for market updates."""
        self.callbacks.append(callback)
    
    def _on_market_update(self, update: Dict[str, Any]):
        """Handle real-time market updates."""
        # Process the update and notify registered callbacks
        for callback in self.callbacks:
            try:
                callback(update)
            except Exception as e:
                logger.error(f"Error in callback: {e}")
    
    def get_real_time_data(self, symbol: str) -> Dict[str, Any]:
        """Get latest real-time data for a symbol."""
        streaming_service = self.service_manager.get_service('streaming')
        if streaming_service:
            return streaming_service.get_latest_data(symbol)
        return {}