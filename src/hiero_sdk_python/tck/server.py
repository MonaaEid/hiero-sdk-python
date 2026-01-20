import json
from typing import Any, Dict
from hiero_sdk_python.tck.errors import JsonRpcError
from hiero_sdk_python.tck.handlers import safe_dispatch
from hiero_sdk_python.tck.protocol import build_json_rpc_error_response, build_json_rpc_success_response, parse_json_rpc_request
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.post("/", response_model=Dict[str, Any])
async def json_rpc_endpoint(request: Dict[str, Any]) -> Dict[str, Any]:
    """JSON-RPC 2.0 endpoint to handle requests."""
    # Parse and validate the JSON-RPC request
    parsed_request = parse_json_rpc_request(json.dumps(request))
    request_id = parsed_request['id']

    if isinstance(parsed_request, JsonRpcError):
        return build_json_rpc_error_response(parsed_request, request_id)

    method_name = parsed_request['method']
    params = parsed_request['params']
    session_id = parsed_request.get('sessionId')

    # Safely dispatch the request to the appropriate handler
    response = safe_dispatch(method_name, params, session_id)

    # If the response is already an error response, return it directly
    if isinstance(response, dict) and 'error' in response:
        return response

    # Build and return the success response
    return build_json_rpc_success_response(response, request_id)

def start_server():
    """Start the JSON-RPC server using Uvicorn."""
    host = "localhost"
    tck_port = 8544
    print(f"Starting TCK server on {host}:{tck_port}")
    uvicorn.run(app, host=host, port=tck_port)



if __name__ == "__main__":
    start_server()