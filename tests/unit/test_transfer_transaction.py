"""
Unit tests for the TransferTransaction class
"""

import pytest

from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction

pytestmark = pytest.mark.unit


def test_constructor_with_parameters(mock_account_ids):
    """Test constructor initialization with parameters."""
    account_id_sender, account_id_recipient, _, token_id_1, token_id_2 = mock_account_ids

    hbar_transfers = {account_id_sender: -1000, account_id_recipient: 1000}

    token_transfers = {
        token_id_1: {account_id_sender: -50, account_id_recipient: 50},
        token_id_2: {account_id_sender: -25, account_id_recipient: 25},
    }

    nft_transfers = {token_id_1: [(account_id_sender, account_id_recipient, 1, True)]}

    # Initialize with parameters
    transfer_tx = TransferTransaction(
        hbar_transfers=hbar_transfers, token_transfers=token_transfers, nft_transfers=nft_transfers
    )

    # Verify all transfers were added correctly
    # Check HBAR transfers
    hbar_amounts = {transfer.account_id: transfer.amount for transfer in transfer_tx.hbar_transfers}
    assert hbar_amounts[account_id_sender] == -1000
    assert hbar_amounts[account_id_recipient] == 1000

    # Check token transfers
    token_amounts_1 = {
        transfer.account_id: transfer.amount for transfer in transfer_tx.token_transfers[token_id_1]
    }
    assert token_amounts_1[account_id_sender] == -50
    assert token_amounts_1[account_id_recipient] == 50

    token_amounts_2 = {
        transfer.account_id: transfer.amount for transfer in transfer_tx.token_transfers[token_id_2]
    }
    assert token_amounts_2[account_id_sender] == -25
    assert token_amounts_2[account_id_recipient] == 25

    assert transfer_tx.nft_transfers[token_id_1][0].sender_id == account_id_sender
    assert transfer_tx.nft_transfers[token_id_1][0].receiver_id == account_id_recipient
    assert transfer_tx.nft_transfers[token_id_1][0].is_approved is True


def test_constructor_default_values():
    """Test that constructor sets default values correctly."""
    transfer_tx = TransferTransaction()

    assert not transfer_tx.hbar_transfers
    assert not transfer_tx.token_transfers
    assert not transfer_tx.nft_transfers
    assert transfer_tx._default_transaction_fee == 100_000_000


def test_add_token_transfer(mock_account_ids):
    """Test adding token transfers and ensure amounts are correctly added."""
    account_id_sender, account_id_recipient, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_token_transfer(token_id_1, account_id_sender, -100)
    transfer_tx.add_token_transfer(token_id_1, account_id_recipient, 100)

    # Find the transfers for each account
    sender_transfer = next(
        t for t in transfer_tx.token_transfers[token_id_1] if t.account_id == account_id_sender
    )
    recipient_transfer = next(
        t for t in transfer_tx.token_transfers[token_id_1] if t.account_id == account_id_recipient
    )

    assert sender_transfer.amount == -100
    assert recipient_transfer.amount == 100


def test_add_hbar_transfer(mock_account_ids):
    """Test adding HBAR transfers and ensure amounts are correctly added."""
    account_id_sender, account_id_recipient, _, _, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_hbar_transfer(account_id_sender, -500)
    transfer_tx.add_hbar_transfer(account_id_recipient, 500)

    # Find the transfers for each account
    sender_transfer = next(
        t for t in transfer_tx.hbar_transfers if t.account_id == account_id_sender
    )
    recipient_transfer = next(
        t for t in transfer_tx.hbar_transfers if t.account_id == account_id_recipient
    )

    assert sender_transfer.amount == -500
    assert recipient_transfer.amount == 500


def test_add_nft_transfer(mock_account_ids):
    """Test adding NFT transfers and ensure amounts are correctly added."""
    account_id_sender, account_id_recipient, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_nft_transfer(
        NftId(token_id_1, 0), account_id_sender, account_id_recipient, True
    )

    assert transfer_tx.nft_transfers[token_id_1][0].sender_id == account_id_sender
    assert transfer_tx.nft_transfers[token_id_1][0].receiver_id == account_id_recipient
    assert transfer_tx.nft_transfers[token_id_1][0].is_approved is True


def test_add_invalid_transfer(mock_account_ids):
    """Test adding invalid transfers raises the appropriate error."""
    transfer_tx = TransferTransaction()

    with pytest.raises(TypeError):
        transfer_tx.add_hbar_transfer(12345, -500)

    with pytest.raises(ValueError):
        transfer_tx.add_hbar_transfer(mock_account_ids[0], 0)

    with pytest.raises(TypeError):
        transfer_tx.add_token_transfer(12345, mock_account_ids[0], -100)

    with pytest.raises(TypeError):
        transfer_tx.add_nft_transfer(12345, mock_account_ids[0], mock_account_ids[1], True)


def test_hbar_accumulation(mock_account_ids):
    """Test that HBAR transfers accumulate for the same account."""
    account_id_1, account_id_2, _, _, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add multiple transfers for the same account
    transfer_tx.add_hbar_transfer(account_id_1, 100)
    transfer_tx.add_hbar_transfer(account_id_1, 200)
    transfer_tx.add_hbar_transfer(account_id_2, 50)

    # Verify accumulation
    amounts = {t.account_id: t.amount for t in transfer_tx.hbar_transfers}
    assert amounts[account_id_1] == 300  # 100 + 200
    assert amounts[account_id_2] == 50
    assert len(transfer_tx.hbar_transfers) == 2


def test_token_accumulation(mock_account_ids):
    """Test that token transfers accumulate for the same token and account."""
    account_id_1, account_id_2, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add multiple transfers for the same token and account
    transfer_tx.add_token_transfer(token_id_1, account_id_1, 100)
    transfer_tx.add_token_transfer(token_id_1, account_id_1, 200)
    transfer_tx.add_token_transfer(token_id_1, account_id_2, 50)

    # Verify accumulation
    amounts = {t.account_id: t.amount for t in transfer_tx.token_transfers[token_id_1]}
    assert amounts[account_id_1] == 300  # 100 + 200
    assert amounts[account_id_2] == 50
    assert len(transfer_tx.token_transfers[token_id_1]) == 2


def test_hbar_negative_amounts(mock_account_ids):
    """Test HBAR transfers with negative amounts (subtraction)."""
    account_id_1, account_id_2, _, _, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Start with positive amounts
    transfer_tx.add_hbar_transfer(account_id_1, 1000)
    transfer_tx.add_hbar_transfer(account_id_2, 500)

    # Add negative amounts (subtraction)
    transfer_tx.add_hbar_transfer(account_id_1, -200)
    transfer_tx.add_hbar_transfer(account_id_2, -100)

    # Verify subtraction
    amounts = {t.account_id: t.amount for t in transfer_tx.hbar_transfers}
    assert amounts[account_id_1] == 800  # 1000 - 200
    assert amounts[account_id_2] == 400  # 500 - 100


def test_token_negative_amounts(mock_account_ids):
    """Test token transfers with negative amounts (subtraction)."""
    account_id_1, account_id_2, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Start with positive amounts
    transfer_tx.add_token_transfer(token_id_1, account_id_1, 1000)
    transfer_tx.add_token_transfer(token_id_1, account_id_2, 500)

    # Add negative amounts (subtraction)
    transfer_tx.add_token_transfer(token_id_1, account_id_1, -200)
    transfer_tx.add_token_transfer(token_id_1, account_id_2, -100)

    # Verify subtraction
    amounts = {t.account_id: t.amount for t in transfer_tx.token_transfers[token_id_1]}
    assert amounts[account_id_1] == 800  # 1000 - 200
    assert amounts[account_id_2] == 400  # 500 - 100


def test_zero_to_positive_transfers(mock_account_ids):
    """Test transfers that go from zero to positive."""
    account_id_1, _, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Start with negative, then add to positive
    transfer_tx.add_hbar_transfer(account_id_1, -500)
    transfer_tx.add_hbar_transfer(account_id_1, 1000)

    amounts = {t.account_id: t.amount for t in transfer_tx.hbar_transfers}
    assert amounts[account_id_1] == 500

    # Same for tokens
    transfer_tx.add_token_transfer(token_id_1, account_id_1, -200)
    transfer_tx.add_token_transfer(token_id_1, account_id_1, 500)

    token_amounts = {t.account_id: t.amount for t in transfer_tx.token_transfers[token_id_1]}
    assert token_amounts[account_id_1] == 300


def test_multiple_tokens_same_account(mock_account_ids):
    """Test multiple tokens for the same account."""
    account_id_1, _, _, token_id_1, token_id_2 = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add different amounts for different tokens to the same account
    transfer_tx.add_token_transfer(token_id_1, account_id_1, 100)
    transfer_tx.add_token_transfer(token_id_2, account_id_1, 200)
    transfer_tx.add_token_transfer(token_id_1, account_id_1, 50)  # Accumulate token1
    transfer_tx.add_token_transfer(token_id_2, account_id_1, -50)  # Subtract from token2

    # Verify each token maintains separate balance
    token1_amounts = {t.account_id: t.amount for t in transfer_tx.token_transfers[token_id_1]}
    token2_amounts = {t.account_id: t.amount for t in transfer_tx.token_transfers[token_id_2]}

    assert token1_amounts[account_id_1] == 150  # 100 + 50
    assert token2_amounts[account_id_1] == 150  # 200 - 50

    # Verify we have separate transfer objects for each token
    assert len(transfer_tx.token_transfers[token_id_1]) == 1
    assert len(transfer_tx.token_transfers[token_id_2]) == 1


def test_edge_case_amounts(mock_account_ids):
    """Test edge cases with very large and very small amounts."""
    account_id_1, account_id_2, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Test very large amounts
    large_amount = 2**63 - 1  # Max int64
    transfer_tx.add_hbar_transfer(account_id_1, large_amount)

    amounts = {t.account_id: t.amount for t in transfer_tx.hbar_transfers}
    assert amounts[account_id_1] == large_amount

    # Test very large negative amounts
    large_negative = -(2**63)  # Min int64
    transfer_tx.add_hbar_transfer(account_id_2, large_negative)

    amounts = {t.account_id: t.amount for t in transfer_tx.hbar_transfers}
    assert amounts[account_id_2] == large_negative

    # Test small amounts
    transfer_tx.add_token_transfer(token_id_1, account_id_1, 1)
    transfer_tx.add_token_transfer(token_id_1, account_id_1, 1)

    token1_amounts = {t.account_id: t.amount for t in transfer_tx.token_transfers[token_id_1]}
    assert token1_amounts[account_id_1] == 2


def test_zero_amount_validation(mock_account_ids):
    """Test that zero amounts are properly rejected."""
    account_id_1, _, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Test zero HBAR amount should raise ValueError
    with pytest.raises(ValueError, match="Amount must be a non-zero integer"):
        transfer_tx.add_hbar_transfer(account_id_1, 0)

    # Test zero token amount should raise ValueError
    with pytest.raises(ValueError, match="Amount must be a non-zero integer"):
        transfer_tx.add_token_transfer(token_id_1, account_id_1, 0)


def test_multiple_nft_transfers(mock_account_ids):
    """Test adding multiple NFT transfers for the same token."""
    account_id_sender, account_id_recipient, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add multiple NFT transfers for the same token
    transfer_tx.add_nft_transfer(
        NftId(token_id_1, 1), account_id_sender, account_id_recipient, False
    )
    transfer_tx.add_nft_transfer(
        NftId(token_id_1, 2), account_id_sender, account_id_recipient, True
    )

    # Verify all transfers were added correctly
    assert len(transfer_tx.nft_transfers[token_id_1]) == 2
    assert transfer_tx.nft_transfers[token_id_1][0].serial_number == 1
    assert transfer_tx.nft_transfers[token_id_1][0].is_approved is False
    assert transfer_tx.nft_transfers[token_id_1][1].serial_number == 2
    assert transfer_tx.nft_transfers[token_id_1][1].is_approved is True


def test_frozen_transaction(mock_account_ids, mock_client):
    """Test that operations fail when transaction is frozen."""
    account_id_sender, account_id_recipient, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Freeze the transaction
    transfer_tx.freeze_with(mock_client)

    # Test adding transfers
    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen."):
        transfer_tx.add_hbar_transfer(account_id_sender, -100)

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen."):
        transfer_tx.add_token_transfer(token_id_1, account_id_sender, -100)

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen."):
        transfer_tx.add_nft_transfer(NftId(token_id_1, 1), account_id_sender, account_id_recipient)


def test_build_transaction_body(mock_account_ids):
    """Test building transaction body with various transfers."""
    account_id_sender, account_id_recipient, node_account_id, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add various transfers
    transfer_tx.add_hbar_transfer(account_id_sender, -500)
    transfer_tx.add_hbar_transfer(account_id_recipient, 500)
    transfer_tx.add_token_transfer(token_id_1, account_id_sender, -100)
    transfer_tx.add_token_transfer(token_id_1, account_id_recipient, 100)
    transfer_tx.add_nft_transfer(NftId(token_id_1, 1), account_id_sender, account_id_recipient)

    # Set required fields for building transaction
    transfer_tx.node_account_id = node_account_id
    transfer_tx.operator_account_id = account_id_sender

    # Build the transaction body
    result = transfer_tx.build_transaction_body()

    # Verify the transaction was built correctly
    assert result.HasField("cryptoTransfer")

    # Verify HBAR transfers
    hbar_transfers = result.cryptoTransfer.transfers.accountAmounts
    assert len(hbar_transfers) == 2

    # Check sender and recipient HBAR transfers
    for transfer in hbar_transfers:
        if transfer.accountID.accountNum == account_id_sender.num:
            assert transfer.amount == -500
        elif transfer.accountID.accountNum == account_id_recipient.num:
            assert transfer.amount == 500

    # Verify token transfers
    token_transfers = result.cryptoTransfer.tokenTransfers
    assert len(token_transfers) == 2

    # Check if token matches
    assert token_transfers[0].token == token_id_1._to_proto()
    assert token_transfers[1].token == token_id_1._to_proto()

    # Check token amounts
    token_amounts = token_transfers[1].transfers
    assert len(token_amounts) == 2

    for transfer in token_amounts:
        if transfer.accountID.accountNum == account_id_sender.num:
            assert transfer.amount == -100
        elif transfer.accountID.accountNum == account_id_recipient.num:
            assert transfer.amount == 100

    # Verify NFT transfers
    nft_transfers = result.cryptoTransfer.tokenTransfers[0].nftTransfers
    assert len(nft_transfers) == 1
    assert nft_transfers[0].senderAccountID.accountNum == account_id_sender.num
    assert nft_transfers[0].receiverAccountID.accountNum == account_id_recipient.num
    assert nft_transfers[0].serialNumber == 1


def test_build_scheduled_body(mock_account_ids):
    """Test building scheduled body with various transfers."""
    account_id_sender, account_id_recipient, node_account_id, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add various transfers
    transfer_tx.add_hbar_transfer(account_id_sender, -500)
    transfer_tx.add_hbar_transfer(account_id_recipient, 500)
    transfer_tx.add_token_transfer(token_id_1, account_id_sender, -100)
    transfer_tx.add_token_transfer(token_id_1, account_id_recipient, 100)
    transfer_tx.add_nft_transfer(NftId(token_id_1, 1), account_id_sender, account_id_recipient)

    # Build the scheduled body
    result = transfer_tx.build_scheduled_body()

    # Verify the scheduled body was built correctly
    assert result.HasField("cryptoTransfer")
    assert isinstance(result, SchedulableTransactionBody)

    # Verify HBAR transfers
    hbar_transfers = result.cryptoTransfer.transfers.accountAmounts
    assert len(hbar_transfers) == 2

    # Check sender and recipient HBAR transfers
    for transfer in hbar_transfers:
        if transfer.accountID.accountNum == account_id_sender.num:
            assert transfer.amount == -500
        elif transfer.accountID.accountNum == account_id_recipient.num:
            assert transfer.amount == 500

    # Verify token transfers
    token_transfers = result.cryptoTransfer.tokenTransfers
    assert len(token_transfers) == 2

    # Check if token matches
    assert token_transfers[0].token == token_id_1._to_proto()
    assert token_transfers[1].token == token_id_1._to_proto()

    # Check token amounts
    token_amounts = token_transfers[1].transfers
    assert len(token_amounts) == 2

    for transfer in token_amounts:
        if transfer.accountID.accountNum == account_id_sender.num:
            assert transfer.amount == -100
        elif transfer.accountID.accountNum == account_id_recipient.num:
            assert transfer.amount == 100

    # Verify NFT transfers
    nft_transfers = result.cryptoTransfer.tokenTransfers[0].nftTransfers
    assert len(nft_transfers) == 1
    assert nft_transfers[0].senderAccountID.accountNum == account_id_sender.num
    assert nft_transfers[0].receiverAccountID.accountNum == account_id_recipient.num
    assert nft_transfers[0].serialNumber == 1


def test_approved_token_transfer_with_decimals(mock_account_ids):
    """Test adding approved token transfers with decimals."""
    account_id_1, _, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add approved token transfer with decimals
    transfer_tx.add_approved_token_transfer_with_decimals(token_id_1, account_id_1, 1000, 6)

    # Verify the transfer was added correctly
    transfer = transfer_tx.token_transfers[token_id_1][0]
    assert transfer.account_id == account_id_1
    assert transfer.amount == 1000
    assert transfer.expected_decimals == 6
    assert transfer.is_approved is True


def test_approved_token_transfer_accumulation(mock_account_ids):
    """Test that approved token transfers accumulate for the same account."""
    account_id_1, account_id_2, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add initial transfers
    transfer_tx.add_token_transfer(token_id_1, account_id_1, 500)
    transfer_tx.add_token_transfer(token_id_1, account_id_2, 300)

    # Verify initial state
    transfer_1 = transfer_tx.token_transfers[token_id_1][0]
    transfer_2 = transfer_tx.token_transfers[token_id_1][1]
    assert transfer_1.amount == 500
    assert transfer_1.is_approved is False
    assert transfer_1.expected_decimals is None
    assert transfer_2.amount == 300
    assert transfer_2.is_approved is False
    assert transfer_2.expected_decimals is None

    # Add approved transfer with decimals for account_1 (accumulates)
    transfer_tx.add_approved_token_transfer_with_decimals(token_id_1, account_id_1, 200, 8)

    # Verify accumulation
    transfer_1 = transfer_tx.token_transfers[token_id_1][0]
    transfer_2 = transfer_tx.token_transfers[token_id_1][1]
    assert transfer_1.amount == 700  # 500 + 200
    assert transfer_1.is_approved is False  # unchanged
    assert transfer_1.expected_decimals == 8  # updated from the accumulation
    assert transfer_2.amount == 300  # unchanged
    assert transfer_2.is_approved is False  # unchanged
    assert transfer_2.expected_decimals is None  # unchanged


def test_approved_token_transfer_validation(mock_account_ids):
    """Test validation for approved token transfers with decimals."""
    account_id_1, _, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Test invalid expected_decimals type
    with pytest.raises(TypeError, match="expected_decimals must be an integer"):
        transfer_tx.add_approved_token_transfer_with_decimals(
            token_id_1, account_id_1, 1000, "invalid"
        )

    # Test zero amount
    with pytest.raises(ValueError, match="Amount must be a non-zero integer"):
        transfer_tx.add_approved_token_transfer_with_decimals(token_id_1, account_id_1, 0, 6)


def test_add_token_transfer_with_decimals(mock_account_ids):
    """Test adding token transfers with expected decimals."""
    account_id_sender, account_id_recipient, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add token transfers with decimals
    transfer_tx.add_token_transfer_with_decimals(token_id_1, account_id_sender, -500, 6)
    transfer_tx.add_token_transfer_with_decimals(token_id_1, account_id_recipient, 500, 6)

    # Verify transfers were added with correct decimals
    sender_transfer = next(
        t for t in transfer_tx.token_transfers[token_id_1] if t.account_id == account_id_sender
    )
    recipient_transfer = next(
        t for t in transfer_tx.token_transfers[token_id_1] if t.account_id == account_id_recipient
    )

    assert sender_transfer.amount == -500
    assert sender_transfer.expected_decimals == 6
    assert sender_transfer.is_approved is False
    assert recipient_transfer.amount == 500
    assert recipient_transfer.expected_decimals == 6
    assert recipient_transfer.is_approved is False


def test_add_approved_nft_transfer(mock_account_ids):
    """Test adding approved NFT transfers."""
    account_id_sender, account_id_recipient, _, token_id_1, _ = mock_account_ids
    serial_number = 12345
    nft_id = NftId(token_id_1, serial_number)

    transfer_tx = TransferTransaction()
    transfer_tx.add_approved_nft_transfer(nft_id, account_id_sender, account_id_recipient)

    # Verify the NFT transfer was added with approval
    assert len(transfer_tx.nft_transfers[token_id_1]) == 1
    nft_transfer = transfer_tx.nft_transfers[token_id_1][0]
    assert nft_transfer.sender_id == account_id_sender
    assert nft_transfer.receiver_id == account_id_recipient
    assert nft_transfer.serial_number == serial_number
    assert nft_transfer.is_approved is True


def test_nft_transfer_with_is_approved_parameter(mock_account_ids):
    """Test add_nft_transfer with explicit is_approved parameter."""
    account_id_sender, account_id_recipient, _, token_id_1, _ = mock_account_ids
    serial_number = 999
    nft_id = NftId(token_id_1, serial_number)

    transfer_tx = TransferTransaction()

    # Add NFT transfer with is_approved=True
    transfer_tx.add_nft_transfer(nft_id, account_id_sender, account_id_recipient, is_approved=True)

    nft_transfer = transfer_tx.nft_transfers[token_id_1][0]
    assert nft_transfer.is_approved is True

    # Add another NFT transfer with is_approved=False (default)
    serial_number_2 = 1000
    nft_id_2 = NftId(token_id_1, serial_number_2)
    transfer_tx.add_nft_transfer(nft_id_2, account_id_sender, account_id_recipient, is_approved=False)

    nft_transfer_2 = transfer_tx.nft_transfers[token_id_1][1]
    assert nft_transfer_2.is_approved is False


def test_token_transfer_validation_invalid_token_id(mock_account_ids):
    """Test validation when token_id is not a TokenId instance."""
    account_id_sender, _, _, _, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    with pytest.raises(TypeError, match="token_id must be a TokenId instance"):
        transfer_tx.add_token_transfer("invalid_token_id", account_id_sender, 100)


def test_token_transfer_validation_invalid_account_id(mock_account_ids):
    """Test validation when account_id is not an AccountId instance."""
    _, _, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    with pytest.raises(TypeError, match="account_id must be an AccountId instance"):
        transfer_tx.add_token_transfer(token_id_1, "invalid_account_id", 100)


def test_token_transfer_validation_invalid_amount_type(mock_account_ids):
    """Test validation when amount is not an integer."""
    account_id_sender, _, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    with pytest.raises(ValueError, match="Amount must be a non-zero integer"):
        transfer_tx.add_token_transfer(token_id_1, account_id_sender, "100")


def test_token_transfer_validation_invalid_is_approved_type(mock_account_ids):
    """Test validation when is_approved is not a boolean."""
    account_id_sender, _, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    with pytest.raises(TypeError, match="is_approved must be a boolean"):
        transfer_tx._add_token_transfer(token_id_1, account_id_sender, 100, "true", None)


def test_nft_transfer_validation_invalid_nft_id(mock_account_ids):
    """Test validation when nft_id is not a NftId instance."""
    account_id_sender, account_id_recipient, _, _, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    with pytest.raises(TypeError, match="nft_id must be a NftId instance"):
        transfer_tx.add_nft_transfer("invalid_nft_id", account_id_sender, account_id_recipient)


def test_nft_transfer_validation_invalid_sender_id(mock_account_ids):
    """Test validation when sender_id is not an AccountId instance."""
    _, account_id_recipient, _, token_id_1, _ = mock_account_ids
    nft_id = NftId(token_id_1, 1)
    transfer_tx = TransferTransaction()

    with pytest.raises(TypeError, match="sender_id must be an AccountId instance"):
        transfer_tx.add_nft_transfer(nft_id, "invalid_sender", account_id_recipient)


def test_nft_transfer_validation_invalid_receiver_id(mock_account_ids):
    """Test validation when receiver_id is not an AccountId instance."""
    account_id_sender, _, _, token_id_1, _ = mock_account_ids
    nft_id = NftId(token_id_1, 1)
    transfer_tx = TransferTransaction()

    with pytest.raises(TypeError, match="receiver_id must be an AccountId instance"):
        transfer_tx.add_nft_transfer(nft_id, account_id_sender, "invalid_receiver")


def test_nft_transfer_validation_invalid_is_approved_type_in_nft(mock_account_ids):
    """Test validation when is_approved is not a boolean for NFT transfer."""
    account_id_sender, account_id_recipient, _, token_id_1, _ = mock_account_ids
    nft_id = NftId(token_id_1, 1)
    transfer_tx = TransferTransaction()

    with pytest.raises(TypeError, match="is_approved must be a boolean"):
        transfer_tx._add_nft_transfer(nft_id, account_id_sender, account_id_recipient, "yes")


def test_multiple_token_types_mixed_transfers(mock_account_ids):
    """Test handling multiple token types with mixed transfer types."""
    account_id_sender, account_id_recipient, _, token_id_1, token_id_2 = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add regular token transfers for token_id_1
    transfer_tx.add_token_transfer(token_id_1, account_id_sender, -100)
    transfer_tx.add_token_transfer(token_id_1, account_id_recipient, 100)

    # Add approved token transfers with decimals for token_id_2
    transfer_tx.add_approved_token_transfer_with_decimals(token_id_2, account_id_sender, -200, 8)
    transfer_tx.add_approved_token_transfer_with_decimals(token_id_2, account_id_recipient, 200, 8)

    # Verify token_id_1 transfers
    assert len(transfer_tx.token_transfers[token_id_1]) == 2
    assert all(not t.is_approved for t in transfer_tx.token_transfers[token_id_1])
    assert all(t.expected_decimals is None for t in transfer_tx.token_transfers[token_id_1])

    # Verify token_id_2 transfers
    assert len(transfer_tx.token_transfers[token_id_2]) == 2
    assert all(t.is_approved for t in transfer_tx.token_transfers[token_id_2])
    assert all(t.expected_decimals == 8 for t in transfer_tx.token_transfers[token_id_2])


def test_transaction_body_with_nft_and_token_transfers(mock_account_ids):
    """Test building transaction body with both NFT and token transfers."""
    account_id_sender, account_id_recipient, node_account_id, token_id_1, token_id_2 = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add token transfer
    transfer_tx.add_token_transfer(token_id_1, account_id_sender, -100)
    transfer_tx.add_token_transfer(token_id_1, account_id_recipient, 100)

    # Add NFT transfer
    nft_id = NftId(token_id_2, 555)
    transfer_tx.add_nft_transfer(nft_id, account_id_sender, account_id_recipient)

    # Set required transaction properties
    from hiero_sdk_python.transaction.transaction_id import TransactionId
    transfer_tx.transaction_id = TransactionId.generate(account_id_sender)
    transfer_tx.node_account_id = node_account_id

    # Build transaction body
    transaction_body = transfer_tx.build_transaction_body()

    # Verify token transfers list contains both types
    assert len(transaction_body.cryptoTransfer.tokenTransfers) == 2

    # Find the token transfer and NFT transfer in the list
    token_transfer_proto = None
    nft_transfer_proto = None
    for tt in transaction_body.cryptoTransfer.tokenTransfers:
        if len(tt.transfers) > 0:
            token_transfer_proto = tt
        if len(tt.nftTransfers) > 0:
            nft_transfer_proto = tt

    # Verify token transfer
    assert token_transfer_proto is not None
    assert len(token_transfer_proto.transfers) == 2

    # Verify NFT transfer
    assert nft_transfer_proto is not None
    assert len(nft_transfer_proto.nftTransfers) == 1
    assert nft_transfer_proto.nftTransfers[0].serialNumber == 555


def test_token_transfer_with_large_amounts(mock_account_ids):
    """Test token transfers with very large amounts."""
    account_id_sender, account_id_recipient, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Use large amounts (within int64 range)
    large_amount = 9_223_372_036_854_775_000  # Close to max int64

    transfer_tx.add_token_transfer(token_id_1, account_id_sender, -large_amount)
    transfer_tx.add_token_transfer(token_id_1, account_id_recipient, large_amount)

    sender_transfer = next(
        t for t in transfer_tx.token_transfers[token_id_1] if t.account_id == account_id_sender
    )
    recipient_transfer = next(
        t for t in transfer_tx.token_transfers[token_id_1] if t.account_id == account_id_recipient
    )

    assert sender_transfer.amount == -large_amount
    assert recipient_transfer.amount == large_amount


def test_decimals_update_on_accumulation(mock_account_ids):
    """Test that expected_decimals gets updated when accumulating transfers."""
    account_id_1, _, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add transfer without decimals
    transfer_tx.add_token_transfer(token_id_1, account_id_1, 100)
    transfer_1 = transfer_tx.token_transfers[token_id_1][0]
    assert transfer_1.expected_decimals is None

    # Add another transfer to same account with decimals
    transfer_tx.add_token_transfer_with_decimals(token_id_1, account_id_1, 200, 6)

    # Verify accumulation and decimals update
    assert len(transfer_tx.token_transfers[token_id_1]) == 1
    transfer_1 = transfer_tx.token_transfers[token_id_1][0]
    assert transfer_1.amount == 300  # 100 + 200
    assert transfer_1.expected_decimals == 6  # Updated


def test_approved_token_transfer_does_not_accumulate_with_regular(mock_account_ids):
    """Test that approved and regular transfers don't accumulate together."""
    account_id_1, _, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add regular transfer
    transfer_tx.add_token_transfer(token_id_1, account_id_1, 100)

    # Add approved transfer to same account - should accumulate because they track by account_id
    transfer_tx.add_approved_token_transfer(token_id_1, account_id_1, 200)

    # Verify they accumulated (based on the implementation in _add_token_transfer)
    assert len(transfer_tx.token_transfers[token_id_1]) == 1
    transfer = transfer_tx.token_transfers[token_id_1][0]
    assert transfer.amount == 300  # 100 + 200


def test_multiple_nft_transfers_same_token(mock_account_ids):
    """Test multiple NFT transfers for the same token ID."""
    account_id_sender, account_id_recipient, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add multiple NFT transfers for the same token
    for serial in range(1, 6):
        nft_id = NftId(token_id_1, serial)
        transfer_tx.add_nft_transfer(nft_id, account_id_sender, account_id_recipient)

    # Verify all transfers were added
    assert len(transfer_tx.nft_transfers[token_id_1]) == 5
    for i, nft_transfer in enumerate(transfer_tx.nft_transfers[token_id_1], start=1):
        assert nft_transfer.serial_number == i


def test_transaction_freeze_prevents_token_transfer(mock_account_ids, mock_client):
    """Test that frozen transaction prevents adding token transfers."""
    account_id_sender, _, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()
    transfer_tx.freeze_with(mock_client)

    with pytest.raises(Exception):  # Should raise an exception when frozen
        transfer_tx.add_token_transfer(token_id_1, account_id_sender, 100)


def test_transaction_freeze_prevents_nft_transfer(mock_account_ids, mock_client):
    """Test that frozen transaction prevents adding NFT transfers."""
    account_id_sender, account_id_recipient, _, token_id_1, _ = mock_account_ids
    nft_id = NftId(token_id_1, 1)
    transfer_tx = TransferTransaction()
    transfer_tx.freeze_with(mock_client)

    with pytest.raises(Exception):  # Should raise an exception when frozen
        transfer_tx.add_nft_transfer(nft_id, account_id_sender, account_id_recipient)


def test_build_transaction_body_with_expected_decimals(mock_account_ids):
    """Test that build_transaction_body correctly includes expected_decimals in protobuf."""
    account_id_sender, account_id_recipient, node_account_id, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add token transfers with decimals
    transfer_tx.add_token_transfer_with_decimals(token_id_1, account_id_sender, -100, 6)
    transfer_tx.add_token_transfer_with_decimals(token_id_1, account_id_recipient, 100, 6)

    # Set required transaction properties
    from hiero_sdk_python.transaction.transaction_id import TransactionId
    transfer_tx.transaction_id = TransactionId.generate(account_id_sender)
    transfer_tx.node_account_id = node_account_id

    # Build transaction body
    transaction_body = transfer_tx.build_transaction_body()

    # Find the token transfer in the protobuf
    token_transfer_proto = transaction_body.cryptoTransfer.tokenTransfers[0]

    # Verify expected_decimals is set
    assert token_transfer_proto.expected_decimals.value == 6


def test_init_with_empty_dictionaries(mock_account_ids):
    """Test initialization with empty dictionaries doesn't cause errors."""
    transfer_tx = TransferTransaction(
        hbar_transfers={},
        token_transfers={},
        nft_transfers={}
    )

    assert len(transfer_tx.hbar_transfers) == 0
    assert len(transfer_tx.token_transfers) == 0
    assert len(transfer_tx.nft_transfers) == 0


def test_chaining_token_transfer_methods(mock_account_ids):
    """Test that transfer methods support method chaining."""
    account_id_sender, account_id_recipient, _, token_id_1, _ = mock_account_ids
    nft_id = NftId(token_id_1, 1)

    # Test method chaining
    transfer_tx = (
        TransferTransaction()
        .add_token_transfer(token_id_1, account_id_sender, -100)
        .add_token_transfer(token_id_1, account_id_recipient, 100)
        .add_approved_token_transfer(token_id_1, account_id_sender, -50)
        .add_token_transfer_with_decimals(token_id_1, account_id_recipient, 50, 6)
        .add_nft_transfer(nft_id, account_id_sender, account_id_recipient)
    )

    # Verify all transfers were added
    assert len(transfer_tx.token_transfers[token_id_1]) >= 2
    assert len(transfer_tx.nft_transfers[token_id_1]) == 1


def test_negative_decimals_validation(mock_account_ids):
    """Test that negative decimals are handled correctly."""
    account_id_sender, _, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Negative decimals should still be accepted as integers (validation is type-based)
    transfer_tx.add_token_transfer_with_decimals(token_id_1, account_id_sender, 100, -1)

    transfer = transfer_tx.token_transfers[token_id_1][0]
    assert transfer.expected_decimals == -1


def test_mixed_approval_and_decimals(mock_account_ids):
    """Test combinations of approved transfers with decimals."""
    account_id_1, account_id_2, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Various combinations
    transfer_tx.add_token_transfer(token_id_1, account_id_1, 100)
    transfer_tx.add_approved_token_transfer(token_id_1, account_id_2, 200)
    transfer_tx.add_token_transfer_with_decimals(token_id_1, account_id_1, 300, 6)
    transfer_tx.add_approved_token_transfer_with_decimals(token_id_1, account_id_2, 400, 8)

    # Verify account_1 transfer (accumulated from first and third call)
    transfer_1 = next(
        t for t in transfer_tx.token_transfers[token_id_1] if t.account_id == account_id_1
    )
    assert transfer_1.amount == 400  # 100 + 300
    assert transfer_1.expected_decimals == 6  # Updated from third call

    # Verify account_2 transfer (accumulated from second and fourth call)
    transfer_2 = next(
        t for t in transfer_tx.token_transfers[token_id_1] if t.account_id == account_id_2
    )
    assert transfer_2.amount == 600  # 200 + 400
    assert transfer_2.expected_decimals == 8  # Updated from fourth call
