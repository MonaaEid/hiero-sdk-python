"""Focused createTopic tests for TCK handlers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.exceptions import PrecheckError, ReceiptStatusError
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_id import TokenId
from tck.errors import JsonRpcError
from tck.handlers.topic import (
    _build_create_topic_transaction,
    _build_custom_fee,
    _get_auto_renew_account_state,
    create_topic,
)
from tck.param.topic import CreateTopicCustomFeeParams, CreateTopicFixedFeeParams, CreateTopicParams


pytestmark = pytest.mark.unit

TEST_KEY = "302e020100300506032b6570042204203e3e6e76b8f1ea10c1d7aaada2fcc088c08a82b65aa3299f66a1c7289ea3fcd2"


def _params(**overrides):
    base = dict(
        sessionId="test",
        memo=None,
        adminKey=None,
        submitKey=None,
        autoRenewPeriod=None,
        autoRenewAccountId=None,
        feeScheduleKey=None,
        feeExemptKeys=None,
        customFees=None,
        commonTransactionParams=None,
    )
    base.update(overrides)
    return CreateTopicParams(**base)


def _success_response(topic_num: int):
    response = MagicMock()
    receipt = MagicMock()
    receipt.status = ResponseCode.SUCCESS
    receipt.topic_id = AccountId(0, 0, topic_num)
    response.get_receipt.return_value = receipt
    return response


@pytest.fixture
def client_mock():
    client = MagicMock()
    client.operator_account_id = AccountId(0, 0, 3)
    return client


def test_parse_json_and_validation():
    assert CreateTopicParams.parse_json_params({"sessionId": "s", "memo": "Topic"}).memo == "Topic"
    with pytest.raises(ValueError, match="customFees must be a list"):
        CreateTopicParams.parse_json_params({"sessionId": "s", "customFees": "bad"})


def test_build_custom_fee_and_reject_empty_collector():
    fee = _build_custom_fee(
        CreateTopicCustomFeeParams(
            feeCollectorAccountId="0.0.98",
            feeCollectorsExempt=True,
            fixedFee=CreateTopicFixedFeeParams(amount=100, denominatingTokenId="0.0.500"),
        )
    )
    assert fee.amount == 100
    assert fee.fee_collector_account_id == AccountId(0, 0, 98)
    assert fee.denominating_token_id == TokenId(0, 0, 500)
    assert fee.all_collectors_are_exempt is True
    with pytest.raises(ValueError, match="feeCollectorAccountId cannot be empty"):
        _build_custom_fee(
            CreateTopicCustomFeeParams(feeCollectorAccountId="", fixedFee=CreateTopicFixedFeeParams(amount=1))
        )


def test_build_transaction_core_fields():
    tx = _build_create_topic_transaction(
        _params(
            memo="m",
            adminKey=TEST_KEY,
            submitKey=TEST_KEY,
            autoRenewPeriod=7776000,
            autoRenewAccountId="0.0.98",
            feeScheduleKey=TEST_KEY,
            feeExemptKeys=[TEST_KEY],
            customFees=[
                CreateTopicCustomFeeParams(
                    feeCollectorAccountId="0.0.98", fixedFee=CreateTopicFixedFeeParams(amount=100)
                )
            ],
        )
    )
    assert tx.memo == "m"
    assert getattr(tx.auto_renew_period, "seconds", tx.auto_renew_period) == 7776000
    assert len(tx.custom_fees) == 1


@pytest.mark.parametrize(
    "side_effect,account_id,expected",
    [
        (None, None, "none"),
        (None, "0.0.98", "exists"),
        (PrecheckError(status=ResponseCode.INVALID_ACCOUNT_ID), "0.0.999", "missing"),
        (
            ReceiptStatusError(
                status=ResponseCode.ACCOUNT_DELETED, transaction_id=None, transaction_receipt=MagicMock()
            ),
            "0.0.98",
            "deleted",
        ),
    ],
)
def test_auto_renew_account_state_mapping(client_mock, side_effect, account_id, expected):
    if account_id is None:
        assert _get_auto_renew_account_state(client_mock, account_id) == expected
        return
    with patch.object(AccountInfoQuery, "execute", side_effect=side_effect):
        assert _get_auto_renew_account_state(client_mock, account_id) == expected


@patch("tck.handlers.topic.get_client")
def test_create_topic_success_minimal(mock_get_client, client_mock):
    mock_get_client.return_value = client_mock
    with patch.object(TopicCreateTransaction, "execute", return_value=_success_response(1000)):
        result = create_topic(_params(memo="Test Topic"))
    assert result.status == "SUCCESS"
    assert result.topicId == "0.0.1000"


@patch("tck.handlers.topic.get_client")
@patch("tck.handlers.topic._get_auto_renew_account_state", return_value="missing")
def test_create_topic_rejects_missing_auto_renew(_, mock_get_client, client_mock):
    mock_get_client.return_value = client_mock
    with pytest.raises(JsonRpcError):
        create_topic(_params(autoRenewAccountId="0.0.999"))


@patch("tck.handlers.topic.get_client")
@patch("tck.handlers.topic._get_auto_renew_account_state", return_value="exists")
def test_create_topic_with_all_parameters(_, mock_get_client, client_mock):
    mock_get_client.return_value = client_mock
    with patch.object(TopicCreateTransaction, "execute", return_value=_success_response(2000)):
        result = create_topic(
            _params(
                memo="Full",
                adminKey=TEST_KEY,
                submitKey=TEST_KEY,
                autoRenewPeriod=7776000,
                autoRenewAccountId="0.0.98",
                feeScheduleKey=TEST_KEY,
                feeExemptKeys=[TEST_KEY],
                customFees=[
                    CreateTopicCustomFeeParams(
                        feeCollectorAccountId="0.0.98",
                        feeCollectorsExempt=True,
                        fixedFee=CreateTopicFixedFeeParams(amount=500, denominatingTokenId="0.0.500"),
                    )
                ],
            )
        )
    assert result.status == "SUCCESS"
    assert result.topicId == "0.0.2000"
