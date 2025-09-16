import os
from langsmith import Client
from typing import Dict, Any, Optional
import logging
import datetime

logger = logging.getLogger(__name__)

class EnhancedTracer:
    def __init__(self):
        self.client = Client()
        self.project_name = os.environ.get("LANGSMITH_PROJECT", "trading-system")
    
    def log_agent_action(self, agent_name: str, action: str, inputs: Dict[str, Any], outputs: Dict[str, Any]):
        """Log agent actions to LangSmith."""
        try:
            run_data = {
                "name": f"{agent_name}_{action}",
                "inputs": inputs,
                "outputs": outputs,
                "tags": ["trading_agent", agent_name],
                "metadata": {
                    "agent": agent_name,
                    "action": action,
                    "timestamp": str(datetime.datetime.now())
                }
            }
            self.client.create_run(**run_data)
        except Exception as e:
            logger.error(f"Failed to log agent action: {e}")
    
    def log_tool_usage(self, tool_name: str, inputs: Dict[str, Any], outputs: str, duration: float):
        """Log tool usage with performance metrics."""
        try:
            run_data = {
                "name": f"tool_{tool_name}",
                "inputs": inputs,
                "outputs": {"result": outputs},
                "tags": ["tool", tool_name],
                "metadata": {
                    "tool": tool_name,
                    "duration": duration,
                    "timestamp": str(datetime.datetime.now())
                }
            }
            self.client.create_run(**run_data)
        except Exception as e:
            logger.error(f"Failed to log tool usage: {e}")
    
    def log_error(self, component: str, error: str, context: Dict[str, Any]):
        """Log errors with context."""
        try:
            run_data = {
                "name": f"error_{component}",
                "inputs": context,
                "outputs": {"error": error},
                "tags": ["error", component],
                "metadata": {
                    "component": component,
                    "error": error,
                    "timestamp": str(datetime.datetime.now())
                }
            }
            self.client.create_run(**run_data)
        except Exception as e:
            logger.error(f"Failed to log error: {e}")

# Global tracer instance
tracer = EnhancedTracer()