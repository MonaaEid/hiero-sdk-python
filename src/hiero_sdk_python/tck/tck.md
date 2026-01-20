# Phase 1: TCK Module Structure and Entry Point
## Set up the foundational directory structure and execution entry point for the TCK server within the SDK codebase.
    1- Created TCK module directory stracture `src/hiero_sdk_python/tck/`
    2- Created module files: `server.py`, `protocol.py`, `handlers.py`,`client_manager.py`, `errors.py` and created `__main__.py` for module execution
    3- In `__main__.py`:
        * Implemented the entry point


# Phase 2: JSON-RPC 2.0 Protocol Layer
## Implement complete JSON-RPC 2.0 specification compliance including request parsing, validation, response formatting, and standardized error handling.
    1- In `errors.py
        * Defined error code constants: PARSE_ERROR, INVALID_REQUEST,METHOD_NOT_FOUND, etc.
        * Created  JsonRpcError class to encapsulate code, message, and optional data field
        * Added `to_dict()` function to convert the error to a dictionary representation
        * Added helper functions `create_parse_error(cls, data=None)`, `create_invalid_request_error(cls, data=None)`, etc to create standard error responses for each error type
    2- In `protocol.py`
        * Created `parse_json_rpc_request(request_json: str)` function to parse and validate a JSON-RPC 2.0 request
        * Created `build_json_rpc_success_response(result: Any, request_id: Optional[Union[str, int]])`to wrap a JsonRpcError and make it JSON-serializable.
        * Created `build_json_rpc_error_response(error: JsonRpcError, request_id: Optional[Union[str, int]])`to wrap a JsonRpcError and make it JSON-serializable.


# Phase 3: Method Routing and Handler Registration System
## Build a flexible registry-based method routing system that can dispatch requests to handlers and transform exceptions into JSON-RPC errors.
    - In `handlers.py`
        * Created a global `_HANDLERS` dict to store method name => handler function mappings
        * Created `register_handler(method_name: str)` decorator that adds functions to the registry
        * Created dispatch(method_name, params, session_id) function that looks up and invokes handlers
        * Created `safe_dispatch(method_name: str, params: Any, session_id: Optional[str])`that maps SDK exceptions to JSON-RPC error responses.
        * Created `validate_request_params(params: Any, required_fields: Dict[str, type])` that validates handler parameters

# Phase 4: SDK Client Lifecycle Management
## Implement session-based client storage and lifecycle management with setup and reset handlers that control SDK client initialization and cleanup.
    1- In `client_manager.py`
        *
        *
        *
    2- In `handlers.py`
    3-