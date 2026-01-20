import json
from typing import Any, Dict, Optional, Union
from hiero_sdk_python.tck.errors import JsonRpcError, PARSE_ERROR, INVALID_REQUEST

def parse_json_rpc_request(request_json: str) -> Union[Dict[str, Any], 'JsonRpcError']:
    """Parse and validate a JSON-RPC 2.0 request."""
    try:
        request = json.loads(request_json)
    except json.JSONDecodeError:
        return JsonRpcError(PARSE_ERROR, 'Parse error')

    if not isinstance(request, dict):
        return JsonRpcError(INVALID_REQUEST, 'Invalid Request')
    if request.get('jsonrpc') != '2.0':
        return JsonRpcError(INVALID_REQUEST, 'Invalid Request')

    method = request.get('method')
    if not isinstance(method, str):
        return JsonRpcError(INVALID_REQUEST, 'Invalid Request')

    if 'id' not in request:
        return JsonRpcError(INVALID_REQUEST, 'Invalid Request')

    params = request.get('params', {})
    if not (isinstance(params, (dict, list)) or params is None):
        return JsonRpcError(INVALID_REQUEST, 'Invalid Request')

    session_id = None
    if isinstance(params, dict) and 'sessionId' in params:
        session_id = params.pop('sessionId')

    return {
        'jsonrpc': '2.0',
        'method': method,
        'params': params,
        'id': request['id'],
        'sessionId': session_id
    }

def build_json_rpc_success_response(result: Any, request_id: Optional[Union[str, int]]) -> Dict[str, Any]:
    """Build a JSON-RPC 2.0 success response."""
    response = {
        'jsonrpc': '2.0',
        'id': request_id,
        'result': result,
    }
    return response

def build_json_rpc_error_response(error: JsonRpcError,
                                  request_id: Optional[Union[str, int]]) -> Dict[str, Any]:
    """Build a JSON-RPC 2.0 error response."""
    error_obj = {
        'code': error.code,
        'message': error.message
    }
    if error.data is not None:
        error_obj['data'] = error.data

    response = {
        'jsonrpc': '2.0',
        'id': request_id,
        'error': error_obj,
    }
    return response
