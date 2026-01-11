# Implement the core routing infrastructure using a dictionary-based registry pattern.

# In handlers.py, create a global _HANDLERS dict to store method name -> handler function mappings
# Implement register_handler(method_name) decorator that adds functions to the registry
# Implement dispatch(method_name, params, session_id) function that looks up and invokes handlers
# Return METHOD_NOT_FOUND error if method doesn't exist in registry
# Pass through any exceptions raised by handlers for error transformation
# Task 2: Implement SDK exception transformation

from typing import Any, Dict, Optional, Union
import json
from hiero_sdk_python.tck.protocol import JsonRpcError, PARSE_ERROR, INVALID_REQUEST

_HANDLERS: Dict[str, Any] = {}

def register_handler(method_name: str):
    def decorator(func):
        _HANDLERS[method_name] = func
        return func
    return decorator

def dispatch(method_name: str, params: Any, session_id: Optional[str]) -> Any:
    if method_name not in _HANDLERS:
        raise JsonRpcError(-32601, 'Method not found')

    handler = _HANDLERS[method_name]
    try:
        if session_id is not None:
            return handler(params, session_id)
        else:
            return handler(params)
    except Exception as e:
        response = {
            'jsonrpc': '2.0',
            'error': {
                'code': -32603,
                'message': 'Internal error',
                'data': str(e)
            },
            'id': None
            }
        return response

    