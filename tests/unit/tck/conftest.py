"""Fixtures for JSON-RPC request tests."""
import pytest

@pytest.fixture
def valid_jsonrpc_request():
    """Returns a valid JSON-RPC request."""
    return {
        "jsonrpc": "2.0",
        "method": "setup",
        "params": {},
        "id": 1,
        "sessionId": "session123"
    }

@pytest.fixture
def invalid_json_request():
    """Returns a malformed JSON-RPC request."""
    return '{"id": malformed}'

@pytest.fixture
def request_missing_fields():
    """Returns a JSON-RPC request missing the 'method' field."""
    return {
        "jsonrpc": "2.0",
        "params": {},
        "id": 1
    }
