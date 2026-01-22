#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:8544/"

def send_request(method, params, request_id):
    """Send a JSON-RPC request to the TCK server."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": request_id
    }

    print(f"\n{'='*60}")
    print(f"Request #{request_id}: {method}")
    print(f"{'='*60}")
    print(json.dumps(payload, indent=2))

    response = requests.post(BASE_URL, json=payload)

    print(f"\nResponse:")
    print(json.dumps(response.json(), indent=2))

    return response.json()

#Test 1: Setup with testnet
send_request("setup", {
    "operatorAccountId": "0.0.2",
    "operatorPrivateKey": "302e020100300506032b65700422042091132178e72057a1d7528025956fe39b0b847f200ab59b2fdd367017f3087137",
    "sessionId": "python-test-1"
}, 1)

#Test 2: Setup with custom nodes
send_request("setup", {
    "operatorAccountId": "0.0.2",
    "operatorPrivateKey": "302e020100300506032b65700422042091132178e72057a1d7528025956fe39b0b847f200ab59b2fdd367017f3087137",
    "network": {
        "nodes": [
            "0.testnet.hedera.com:50211",
            "1.testnet.hedera.com:50211"
        ]
    },
    "sessionId": "python-test-2"
}, 2)

#Test 3: Reset
send_request("reset", {
    "sessionId": "python-test-1"
}, 3)

#Test 4: Error case - missing parameter
send_request("setup", {
    "operatorAccountId": "0.0.2",
    "sessionId": "python-test-3"
}, 4)