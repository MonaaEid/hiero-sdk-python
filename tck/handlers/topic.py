from __future__ import annotations

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.exceptions import PrecheckError, ReceiptStatusError
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from tck.errors import JsonRpcError
from tck.handlers.registry import rpc_method
from tck.param.topic import CreateTopicCustomFeeParams, CreateTopicParams
from tck.response.topic import CreateTopicResponse
from tck.util.client_utils import get_client
from tck.util.constants import DEFAULT_GRPC_TIMEOUT
from tck.util.key_utils import get_key_from_string


def _build_custom_fee(custom_fee_params: CreateTopicCustomFeeParams) -> CustomFixedFee:
    custom_fee = CustomFixedFee()

    if custom_fee_params.feeCollectorAccountId == "":
        # Keep TCK behavior: explicitly empty collector should surface as internal error.
        raise ValueError("feeCollectorAccountId cannot be empty")

    if custom_fee_params.feeCollectorAccountId is not None:
        custom_fee.set_fee_collector_account_id(AccountId.from_string(custom_fee_params.feeCollectorAccountId))

    if custom_fee_params.feeCollectorsExempt:
        custom_fee.set_all_collectors_are_exempt(custom_fee_params.feeCollectorsExempt)

    if custom_fee_params.fixedFee is not None:
        if custom_fee_params.fixedFee.amount is not None:
            custom_fee.amount = custom_fee_params.fixedFee.amount

        if custom_fee_params.fixedFee.denominatingTokenId:
            custom_fee.set_denominating_token_id(TokenId.from_string(custom_fee_params.fixedFee.denominatingTokenId))

    return custom_fee


def _build_create_topic_transaction(params: CreateTopicParams) -> TopicCreateTransaction:
    transaction = TopicCreateTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.memo is not None:
        transaction.set_memo(params.memo)

    if params.adminKey:
        transaction.set_admin_key(get_key_from_string(params.adminKey))

    if params.submitKey:
        transaction.set_submit_key(get_key_from_string(params.submitKey))

    if params.autoRenewPeriod is not None:
        transaction.set_auto_renew_period(params.autoRenewPeriod)

    if params.autoRenewAccountId:
        transaction.set_auto_renew_account(AccountId.from_string(params.autoRenewAccountId))

    if params.feeScheduleKey:
        transaction.set_fee_schedule_key(get_key_from_string(params.feeScheduleKey))

    if params.feeExemptKeys:
        transaction.set_fee_exempt_keys([get_key_from_string(key) for key in params.feeExemptKeys])

    if params.customFees is not None:
        transaction.set_custom_fees([_build_custom_fee(custom_fee_params) for custom_fee_params in params.customFees])

    return transaction


def _get_auto_renew_account_state(client, auto_renew_account_id: str | None) -> str:
    if not auto_renew_account_id:
        return "none"

    account_id = AccountId.from_string(auto_renew_account_id)
    try:
        AccountInfoQuery().set_account_id(account_id).execute(client)
        return "exists"
    except (PrecheckError, ReceiptStatusError) as exc:
        status = ResponseCode(exc.status).name
        if status == "INVALID_ACCOUNT_ID":
            return "missing"
        if status == "ACCOUNT_DELETED":
            return "deleted"
        return "unknown"


@rpc_method("createTopic")
def create_topic(params: CreateTopicParams) -> CreateTopicResponse:
    client = get_client(params.sessionId)

    auto_renew_account_state = _get_auto_renew_account_state(client, params.autoRenewAccountId)
    if auto_renew_account_state == "missing":
        raise JsonRpcError.hiero_error({"status": "INVALID_AUTORENEW_ACCOUNT"})

    transaction = _build_create_topic_transaction(params)

    # Align with TCK expectation: if no explicit auto-renew account is provided,
    # default to the transaction payer/operator account.
    if params.autoRenewAccountId is None and client is not None and client.operator_account_id is not None:
        transaction.set_auto_renew_account(client.operator_account_id)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    try:
        response = transaction.execute(client, wait_for_receipt=False)
        receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)
    except (PrecheckError, ReceiptStatusError) as exc:
        status = ResponseCode(exc.status).name
        if params.autoRenewAccountId and status == "INVALID_SIGNATURE" and auto_renew_account_state != "deleted":
            raise JsonRpcError.hiero_error({"status": "INVALID_AUTORENEW_ACCOUNT"}) from exc
        raise JsonRpcError.hiero_error({"status": status}) from exc
    topic_id = ""
    if receipt.status == ResponseCode.SUCCESS and receipt.topic_id is not None:
        topic_id = str(receipt.topic_id)

    return CreateTopicResponse(topic_id, ResponseCode(receipt.status).name)
