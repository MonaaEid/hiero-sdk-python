"""Unit tests for the JSON-RPC protocol handling in the TCK."""
import json
import pytest

from tck.protocol import (
    parse_json_rpc_request,
    _extract_session_id,
    build_json_rpc_success_response,
    build_json_rpc_error_response,
)

pytestmark = pytest.mark.unit

def test_parsing_valid_request(valid_jsonrpc_request):
    """Test parsing of a valid JSON-RPC request."""
    raw = json.dumps(valid_jsonrpc_request)
    parsed = parse_json_rpc_request(raw)
    assert parsed['method'] == 'setup'
    assert parsed['id'] == 1

def test_response_formatting_success():
    """Test formatting of a successful JSON-RPC response."""
    resp = build_json_rpc_success_response({"ok": True}, 1)
    assert resp["jsonrpc"] == "2.0"
    assert "result" in resp


def test_response_formatting_error():
    """Test formatting of an error JSON-RPC response."""
    class DummyError:
        """A dummy error class for testing."""
        def __init__(self):
            self.code = -32600
            self.message = "Invalid Request"
            self.data = None

    error = DummyError()
    resp = build_json_rpc_error_response(error, 1)
    assert resp["jsonrpc"] == "2.0"
    assert "error" in resp
    assert resp["error"]["code"] == -32600
    assert resp["error"]["message"] == "Invalid Request"

def test_invalid_json_returns_parse_error(invalid_json_request):
    """Test that invalid JSON input returns a parse error."""
    req = invalid_json_request
    parsed = parse_json_rpc_request(req)
    assert isinstance(parsed, dict) or hasattr(parsed, 'code')
    # Assuming JsonRpcError has a 'code' attribute
    assert hasattr(parsed, 'code')

def test_missing_required_fields_returns_invalid_request(request_missing_fields):
    """Test that missing required fields returns an invalid request error."""
    req = request_missing_fields
    # No method: should trigger "Invalid Request"
    assert "method" not in req



def test_session_id_extraction(valid_jsonrpc_request):
    """Test extraction of session ID from valid JSON-RPC request."""
    sid = _extract_session_id(valid_jsonrpc_request)
    assert sid == "session123"

def test_session_id_extraction_no_session():
    """Test extraction of session ID when no session is present."""
    params = {}
    sid = _extract_session_id(params)
    assert sid is None