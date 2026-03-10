"""TCK handlers for Consensus Service operations (Topics)."""

from typing import Any, Dict, Optional, List
from hiero_sdk_python import (
    Client, PrivateKey, PublicKey, TopicCreateTransaction, Duration,
    AccountId, ResponseCode, TopicId
)
from hiero_sdk_python.utils.key_utils import Key
from .registry import register_handler, validate_request_params
from ..client_manager import get_client
from ..errors import JsonRpcError, INTERNAL_ERROR, INVALID_PARAMS, HIERO_ERROR


def _parse_key(key_string: Optional[str]) -> Optional[Key]:
    """Parse a key from a hex string.
    
    Args:
        key_string: Hex-encoded key string
        
    Returns:
        PublicKey or PrivateKey instance, or None if key_string is None
        
    Raises:
        JsonRpcError: If the key cannot be parsed
    """
    if key_string is None:
        return None
    
    try:
        # Try to parse as a private key first
        try:
            return PrivateKey.from_string(key_string)
        except Exception:
            # If it fails, try as a public key
            return PublicKey.from_string(key_string)
    except Exception as e:
        raise JsonRpcError(INTERNAL_ERROR, f"Failed to parse key: {str(e)}")


def _get_signers(signers_list: Optional[List[str]]) -> List[PrivateKey]:
    """Parse and return list of private keys for signing.
    
    Args:
        signers_list: List of hex-encoded private key strings
        
    Returns:
        List of PrivateKey instances
    """
    if not signers_list:
        return []
    
    keys = []
    for signer_str in signers_list:
        try:
            key = PrivateKey.from_string(signer_str)
            keys.append(key)
        except Exception as e:
            raise JsonRpcError(INTERNAL_ERROR, f"Failed to parse signer key: {str(e)}")
    return keys


@register_handler("createTopic")
def create_topic_handler(params: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
    """Create a new topic using TopicCreateTransaction.
    
    Params:
        memo (str, optional): Topic memo
        adminKey (str, optional): Admin key (hex-encoded)
        submitKey (str, optional): Submit key (hex-encoded)
        autoRenewPeriod (str, optional): Auto-renew period in seconds
        autoRenewAccountId (str, optional): Account ID for auto-renewal
        commonTransactionParams (dict, optional): Common params including signers
        
    Returns:
        Dict with status and topicId
    """
    # Get client from session
    client = get_client(session_id or "default")
    if client is None:
        raise JsonRpcError(INTERNAL_ERROR, "No client initialized for this session")
    
    try:
        # Create the transaction
        tx = TopicCreateTransaction()
        
        # Set memo if provided
        if "memo" in params and params["memo"] is not None:
            memo = params["memo"]
            # Validate memo length (max 100 bytes)
            if len(memo.encode('utf-8')) > 100:
                raise JsonRpcError(HIERO_ERROR, "Hiero error", {"status": "MEMO_TOO_LONG"})
            # Check for null bytes
            if '\0' in memo:
                raise JsonRpcError(HIERO_ERROR, "Hiero error", {"status": "INVALID_ZERO_BYTE_IN_STRING"})
            tx.set_memo(memo)
        
        # Set admin key if provided
        if "adminKey" in params and params["adminKey"] is not None:
            admin_key = _parse_key(params["adminKey"])
            if admin_key:
                tx.set_admin_key(admin_key)
        
        # Set submit key if provided
        if "submitKey" in params and params["submitKey"] is not None:
            submit_key = _parse_key(params["submitKey"])
            if submit_key:
                tx.set_submit_key(submit_key)
        
        # Set auto-renew period if provided
        if "autoRenewPeriod" in params and params["autoRenewPeriod"] is not None:
            try:
                period = int(params["autoRenewPeriod"])
                # Validate auto-renew period (approximate range: 6999999 to 8000001)
                if period <= 0 or period < 6999999 or period > 8000001:
                    raise JsonRpcError(HIERO_ERROR, "Hiero error", {"status": "AUTORENEW_DURATION_NOT_IN_RANGE"})
                tx.set_auto_renew_period(period)
            except ValueError:
                raise JsonRpcError(INVALID_PARAMS, "Invalid params", "autoRenewPeriod must be a string representing an integer")
        
        # Set auto-renew account if provided
        if "autoRenewAccountId" in params and params["autoRenewAccountId"] is not None:
            try:
                auto_renew_account = AccountId.from_string(params["autoRenewAccountId"])
                tx.set_auto_renew_account(auto_renew_account)
            except Exception as e:
                raise JsonRpcError(INVALID_PARAMS, "Invalid params", f"Invalid autoRenewAccountId: {str(e)}")
        
        # Freeze the transaction with the client
        tx.freeze_with(client)
        
        # Get signers from commonTransactionParams if provided
        signers = []
        if "commonTransactionParams" in params:
            common_params = params["commonTransactionParams"]
            if "signers" in common_params and isinstance(common_params["signers"], list):
                signers = _get_signers(common_params["signers"])
        
        # Sign the transaction with any additional signers
        for signer in signers:
            tx.sign(signer)
        
        # Execute the transaction
        receipt = tx.execute(client)
        
        # Check the receipt status
        if receipt.status != ResponseCode.SUCCESS:
            status_name = ResponseCode(receipt.status).name
            raise JsonRpcError(HIERO_ERROR, "Hiero error", {"status": status_name})
        
        # Extract the topic ID
        topic_id = receipt.topic_id
        if not topic_id:
            raise JsonRpcError(INTERNAL_ERROR, "Transaction succeeded but no topic ID returned")
        
        return {
            "status": ResponseCode(receipt.status).name,
            "topicId": str(topic_id)
        }
        
    except JsonRpcError:
        raise
    except Exception as e:
        raise JsonRpcError(HIERO_ERROR, "Hiero error", str(e))
