# Implement response formatting:
# - Create success response builder wrapping result in JSON-RPC 2.0 format
# - Create error response builder wrapping JsonRpcError
# - Handle null id for notifications
# - Ensure JSON-serializability
import json
from typing import Any, Dict, Optional, Union
from hiero_sdk_python.tck.errors import JsonRpcError

def parse_json_rpc_request(request_json: str) -> Union[Dict[str, Any], 'JsonRpcError']:
    PARSE_ERROR = {'code': -32700, 'message': 'Parse error'}
    INVALID_REQUEST = {'code': -32600, 'message': 'Invalid Request'}

    try:
        request = json.loads(request_json)
    except json.JSONDecodeError:
        return JsonRpcError(PARSE_ERROR['code'], PARSE_ERROR['message'])

    if not isinstance(request, dict):
        return JsonRpcError(INVALID_REQUEST['code'], INVALID_REQUEST['message'])

    if request.get('jsonrpc') != '2.0':
        return JsonRpcError(INVALID_REQUEST['code'], INVALID_REQUEST['message'])

    method = request.get('method')
    if not isinstance(method, str):
        return JsonRpcError(INVALID_REQUEST['code'], INVALID_REQUEST['message'])

    if 'id' not in request:
        return JsonRpcError(INVALID_REQUEST['code'], INVALID_REQUEST['message'])

    params = request.get('params', {})
    if not (isinstance(params, (dict, list)) or params is None):
        return JsonRpcError(INVALID_REQUEST['code'], INVALID_REQUEST['message'])

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
    response = {
        'jsonrpc': '2.0',
        'result': result,
        'id': request_id
    }
    return response
# Implement response formatting:
# - Create success response builder wrapping result in JSON-RPC 2.0 format
# - Create error response builder wrapping JsonRpcError
# - Handle null id for notifications
# - Ensure JSON-serializability
def build_json_rpc_error_response(error: JsonRpcError, request_id: Optional[Union[str, int]]) -> Dict[str, Any]:
    response = {
        'jsonrpc': '2.0',
        'error': {
            'code': error.code,
            'message': error.message,
            'data': error.data
        },
        'id': request_id
    }
    return response

