from hiero_sdk_python.tck.handlers.registry import register_handler, validate_request_params
from hiero_sdk_python import Client, AccountId, PrivateKey, Network
from hiero_sdk_python.node import _Node
from hiero_sdk_python.tck.client_manager import store_client, remove_client
from hiero_sdk_python.tck.errors import INVALID_PARAMS
from hiero_sdk_python.tck.errors import JsonRpcError
from typing import Any, Dict, Optional

@register_handler("setup")
def setup_handler(params: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
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
            
            # Convert string nodes to _Node objects with generated AccountIds
            # Starting from AccountId 0.0.3 (common convention for network nodes)
            node_objects = []
            for idx, node_address in enumerate(nodes):
                account_id = AccountId(0, 0, 3 + idx)
                node_obj = _Node(account_id, node_address, None)
                node_objects.append(node_obj)
            
            network = Network(nodes=node_objects)
            client = Client(network)
        else:
            raise JsonRpcError(INVALID_PARAMS, 'Invalid params: unknown network specification')

    client.set_operator(operator_account_id, operator_private_key)

    # Store the initialized client in the client manager
    # Use the session_id passed by dispatcher, or generate a default one
    effective_session_id = session_id or "default"
    store_client(effective_session_id, client)

    return {"status": "success", "sessionId": effective_session_id}

@register_handler("reset")
def reset_handler(params: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
    """Reset handler to close connections and clear client state."""
    target_session_id = params.get('sessionId') or session_id
    if target_session_id is not None:
        remove_client(target_session_id)
    return {"status": "reset completed"}