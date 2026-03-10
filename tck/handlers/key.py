"""TCK handlers for key generation and manipulation."""

from typing import Any, Dict, Optional, List
from hiero_sdk_python import PrivateKey, PublicKey
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.utils.key_utils import key_to_proto
from .registry import register_handler
from ..errors import JsonRpcError, INVALID_PARAMS, INTERNAL_ERROR


def _key_to_hex(key: Any) -> str:
    """Convert a key to its DER-encoded hex representation.
    
    Args:
        key: PrivateKey or PublicKey instance
        
    Returns:
        Hex string representation of the key
    """
    proto_key = key_to_proto(key)
    if proto_key is None:
        raise JsonRpcError(INTERNAL_ERROR, "Failed to convert key to protobuf")
    
    # Serialize to bytes and convert to hex
    key_bytes = proto_key.SerializeToString()
    return key_bytes.hex().upper()


@register_handler("generateKey")
def generate_key_handler(params: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
    """Generate cryptographic keys for testing.
    
    Params:
        type (str, required): Type of key to generate
            - ed25519PrivateKey: Generate a new Ed25519 private key
            - ecdsaSecp256k1PrivateKey: Generate a new ECDSA (secp256k1) private key
            - ed25519PublicKey: Get public key from private key or generate public key
            - ecdsaSecp256k1PublicKey: Get public key from private key or generate public key
            - keyList: Generate a keyList with multiple keys
            - thresholdKey: Generate a thresholdKey
        fromKey (str, optional): Private key to derive public key from (hex string)
        threshold (int, optional): Threshold for thresholdKey type
        keys (list, optional): List of key specs for keyList/thresholdKey
        
    Returns:
        Dict with key information and privateKeys list
    """
    try:
        key_type = params.get("type")
        if not key_type:
            raise JsonRpcError(INVALID_PARAMS, "Missing required parameter: type")
        
        if key_type == "ed25519PrivateKey":
            # Generate new Ed25519 private key
            private_key = PrivateKey.generate_ed25519()
            return {
                "key": _key_to_hex(private_key),
                "privateKeys": [_key_to_hex(private_key)]
            }
        
        elif key_type == "ecdsaSecp256k1PrivateKey":
            # Generate new ECDSA (secp256k1) private key
            private_key = PrivateKey.generate_ecdsa_secp256k1()
            return {
                "key": _key_to_hex(private_key),
                "privateKeys": [_key_to_hex(private_key)]
            }
        
        elif key_type == "ed25519PublicKey":
            # Get or generate Ed25519 public key
            if "fromKey" in params and params["fromKey"]:
                # Derive public key from private key
                private_key = PrivateKey.from_string(params["fromKey"])
                public_key = private_key.public_key()
            else:
                # Generate new key pair and return public key
                private_key = PrivateKey.generate_ed25519()
                public_key = private_key.public_key()
            
            return {
                "key": _key_to_hex(public_key)
            }
        
        elif key_type == "ecdsaSecp256k1PublicKey":
            # Get or generate ECDSA (secp256k1) public key
            if "fromKey" in params and params["fromKey"]:
                # Derive public key from private key
                private_key = PrivateKey.from_string(params["fromKey"])
                public_key = private_key.public_key()
            else:
                # Generate new key pair and return public key
                private_key = PrivateKey.generate_ecdsa_secp256k1()
                public_key = private_key.public_key()
            
            return {
                "key": _key_to_hex(public_key)
            }
        
        elif key_type == "keyList":
            # Generate a KeyList with multiple keys
            keys_spec = params.get("keys", [])
            if not isinstance(keys_spec, list):
                raise JsonRpcError(INVALID_PARAMS, "keys parameter must be a list")
            
            key_list_proto = basic_types_pb2.KeyList()
            private_keys_hex = []
            
            for key_spec in keys_spec:
                if not isinstance(key_spec, dict):
                    raise JsonRpcError(INVALID_PARAMS, "Each key spec must be a dict")
                
                spec_type = key_spec.get("type")
                if spec_type == "ed25519PrivateKey":
                    private_key = PrivateKey.generate_ed25519()
                    private_keys_hex.append(_key_to_hex(private_key))
                    proto_key = key_to_proto(private_key)
                elif spec_type == "ecdsaSecp256k1PrivateKey":
                    private_key = PrivateKey.generate_ecdsa_secp256k1()
                    private_keys_hex.append(_key_to_hex(private_key))
                    proto_key = key_to_proto(private_key)
                else:
                    raise JsonRpcError(INVALID_PARAMS, f"Unsupported key type in keyList: {spec_type}")
                
                if proto_key:
                    key_list_proto.keys.append(proto_key)
            
            # Serialize KeyList to bytes and convert to hex
            key_list_bytes = key_list_proto.SerializeToString()
            key_list_hex = key_list_bytes.hex().upper()
            
            return {
                "key": key_list_hex,
                "privateKeys": private_keys_hex
            }
        
        elif key_type == "thresholdKey":
            # Generate a ThresholdKey with threshold and keys
            threshold = params.get("threshold")
            if threshold is None:
                raise JsonRpcError(INVALID_PARAMS, "threshold parameter required for thresholdKey")
            
            keys_spec = params.get("keys", [])
            if not isinstance(keys_spec, list):
                raise JsonRpcError(INVALID_PARAMS, "keys parameter must be a list")
            
            threshold_key_proto = basic_types_pb2.ThresholdKey()
            threshold_key_proto.threshold = int(threshold)
            
            private_keys_hex = []
            
            for key_spec in keys_spec:
                if not isinstance(key_spec, dict):
                    raise JsonRpcError(INVALID_PARAMS, "Each key spec must be a dict")
                
                spec_type = key_spec.get("type")
                if spec_type == "ed25519PrivateKey":
                    private_key = PrivateKey.generate_ed25519()
                    private_keys_hex.append(_key_to_hex(private_key))
                    proto_key = key_to_proto(private_key)
                elif spec_type == "ecdsaSecp256k1PrivateKey":
                    private_key = PrivateKey.generate_ecdsa_secp256k1()
                    private_keys_hex.append(_key_to_hex(private_key))
                    proto_key = key_to_proto(private_key)
                else:
                    raise JsonRpcError(INVALID_PARAMS, f"Unsupported key type in thresholdKey: {spec_type}")
                
                if proto_key:
                    threshold_key_proto.keys.keys.append(proto_key)
            
            # Serialize ThresholdKey to bytes and convert to hex
            threshold_key_bytes = threshold_key_proto.SerializeToString()
            threshold_key_hex = threshold_key_bytes.hex().upper()
            
            return {
                "key": threshold_key_hex,
                "privateKeys": private_keys_hex
            }
        
        else:
            raise JsonRpcError(INVALID_PARAMS, f"Unsupported key type: {key_type}")
    
    except JsonRpcError:
        raise
    except Exception as e:
        raise JsonRpcError(INTERNAL_ERROR, f"Failed to generate key: {str(e)}")
