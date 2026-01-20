"""Build a flexible registry-based method routing system that can dispatch 
requests to handlers and transform exceptions into JSON-RPC errors."""
from typing import Any, Dict, Optional, Union
import json
from hiero_sdk_python.tck.errors import INTERNAL_ERROR, INVALID_PARAMS, METHOD_NOT_FOUND, HIERO_ERROR, INVALID_REQUEST
from hiero_sdk_python.tck.protocol import build_json_rpc_error_response, JsonRpcError
from hiero_sdk_python.exceptions import PrecheckError, ReceiptStatusError, MaxAttemptsError
from hiero_sdk_python.tck.client_manager import store_client,remove_client
from hiero_sdk_python import Client, AccountId, PrivateKey, Network

# A global _HANDLERS dict to store method name -> handler function mappings
_HANDLERS: Dict[str, Any] = {}

def register_handler(method_name: str):
    """Register a handler function for a given method name."""
    def decorator(func):
        """Decorator to register a handler function for a given method name."""
        _HANDLERS[method_name] = func
        return func
    return decorator
    
def dispatch(method_name: str, params: Any, session_id: Optional[str]) -> Any:
    """Dispatch the request to the appropriate handler based on method_name."""
    if method_name not in _HANDLERS:
        raise JsonRpcError(METHOD_NOT_FOUND, 'Method not found')

    handler = _HANDLERS[method_name]
    try:
        if session_id is not None:
            return handler(params, session_id)
        return handler(params)
    except JsonRpcError:
        raise
    except Exception as e:
        error = JsonRpcError(INTERNAL_ERROR, 'Internal error', str(e))
        return build_json_rpc_error_response(error, None)

def safe_dispatch(method_name: str,
                  params: Any,
                  session_id: Optional[str]) -> Union[Any, Dict[str, Any]]:
    """Safely dispatch the request and handle exceptions."""
    try:
        return dispatch(method_name, params, session_id)
    except (PrecheckError, ReceiptStatusError, MaxAttemptsError) as e:
        error = JsonRpcError(HIERO_ERROR, 'Hiero error', str(e))
        return build_json_rpc_error_response(error, None)
    except Exception as e:
        error = JsonRpcError(INTERNAL_ERROR, 'Internal error', str(e))
        return build_json_rpc_error_response(error, None)

def validate_request_params(params: Any, required_fields: Dict[str, type]) -> None:
    """Validate that required fields are present in params with correct types."""
    if not isinstance(params, dict):
        raise JsonRpcError(INVALID_REQUEST, 'Invalid Request')

    for field, field_type in required_fields.items():
        if field not in params or not isinstance(params[field], field_type):
            raise JsonRpcError(INVALID_PARAMS, f'Invalid params: missing or incorrect type for {field}')


@register_handler("setup")
def setup_handler(params: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    """Setup handler to initialize SDK clients with operator credentials and network configuration."""
    # Validate required parameters
    required_fields = {
        'operatorAccountId': str,
        'operatorPrivateKey': str
    }
    validate_request_params(params, required_fields)

    operator_account_id_str = params['operatorAccountId']
    operator_private_key_str = params['operatorPrivateKey']

    operator_account_id = AccountId.from_string(operator_account_id_str)
    operator_private_key = PrivateKey.from_string(operator_private_key_str)

    # Determine network configuration
    network_param = params.get('network')
    if network_param is None:
        client = Client.for_testnet()
    else:
        if network_param == 'mainnet':
            client = Client.for_mainnet()
        elif isinstance(network_param, dict) and 'nodes' in network_param:
            nodes = network_param['nodes']
            if not isinstance(nodes, list) or not all(isinstance(node, str) for node in nodes):
                raise JsonRpcError(INVALID_PARAMS, 'Invalid params: nodes must be a list of strings')
            network = Network(nodes=nodes)
            client = Client(network)
        else:
            raise JsonRpcError(INVALID_PARAMS, 'Invalid params: unknown network specification')

    client.set_operator(operator_account_id, operator_private_key)

    # Store the initialized client in the client manager
    store_client(session_id, client)

    return {"status": "success"}

@register_handler("reset")
def reset_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """Reset handler to close connections and clear client state."""
    session_id = params.get('sessionId')
    if session_id is not None:
        remove_client(session_id)
    return {"status": "reset completed"}