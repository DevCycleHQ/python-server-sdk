import json
from typing import Any, Dict, Optional


class JSONUtils:
    """Centralized JSON configuration utility for consistent serialization behavior"""
    
    @staticmethod
    def serialize_config(data: Any) -> str:
        """
        Serialize configuration data with consistent settings.
        Used for config-related serialization that should be robust to API changes.
        """
        return json.dumps(data, default=str, separators=(',', ':'), sort_keys=True)
    
    @staticmethod
    def serialize_events(data: Any) -> str:
        """
        Serialize event data with consistent settings.
        Used for event-related serialization that should be robust to API changes.
        """
        return json.dumps(data, default=str, separators=(',', ':'), sort_keys=True)
    
    @staticmethod
    def deserialize_config(data: str) -> Dict[str, Any]:
        """
        Deserialize configuration data with consistent settings.
        Handles unknown properties gracefully for API compatibility.
        """
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config response: {e}")
    
    @staticmethod
    def deserialize_events(data: str) -> Dict[str, Any]:
        """
        Deserialize event data with consistent settings.
        Handles unknown properties gracefully for API compatibility.
        """
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in event response: {e}")
    
    @staticmethod
    def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """
        Safely get a value from a dictionary, handling missing keys gracefully.
        """
        return data.get(key, default)
    
    @staticmethod
    def safe_get_nested(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
        """
        Safely get a nested value from a dictionary, handling missing keys gracefully.
        """
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return default
            if current is None:
                return default
        return current if current is not None else default