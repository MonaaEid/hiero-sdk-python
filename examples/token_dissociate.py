"""
A full example that creates an account, two tokens, associates them,
and finally dissociates them.
"""

"""
uv run examples/token_dissociate.py
python examples/token_dissociate.py
"""
import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
    Hbar,
    AccountCreateTransaction,
    TokenCreateTransaction,
    TokenAssociateTransaction,
    TokenDissociateTransaction,
    TokenType,
    AccountInfoQuery,
)

# Load environment variables from .env file
load_dotenv()

def setup_client():
    """Setup Client"""
    print("Connecting to Hedera testnet...")
    client = Client(Network(network='testnet'))

    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
        client.set_operator(operator_id, operator_key)
        return client, operator_id, operator_key

    except (TypeError, ValueError):
        print("❌ Error: Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)

    print(f"Using operator account: {operator_id}")

def create_new_account():
    """Create a new account to associate/dissociate with tokens"""
    client, operator_id, operator_key = setup_client()
    print("\nSTEP 1: Creating a new account...")
    recipient_key = PrivateKey.generate_ed25519()

    try:
        # Build the transaction
        tx = (
            AccountCreateTransaction()
            .set_key(recipient_key.public_key()) # <-- THE FIX: Call as a method
            .set_initial_balance(Hbar.from_tinybars(100_000_000)) # 1 Hbar
        )

        # Freeze the transaction, sign with the operator, then execute
        receipt = tx.freeze_with(client).sign(operator_key).execute(client)
        recipient_id = receipt.account_id
        print(f"✅ Success! Created new account with ID: {recipient_id}")
        return client, operator_key, recipient_id, recipient_key, operator_id

    except Exception as e:
        print(f"❌ Error creating new account: {e}")
        sys.exit(1)
def create_token():
    """Create two new tokens"""
    client, operator_key, recipient_id, recipient_key, operator_id = create_new_account()
    print("\nSTEP 2: Creating two new tokens...")
    try:
        # Generate supply key for NFT
        supply_key = PrivateKey.generate_ed25519()                            
        # Create NFT Token
        nft_tx = (
            TokenCreateTransaction().set_token_name("NFT Token").set_token_symbol("NFTK").set_token_type(TokenType.NON_FUNGIBLE_UNIQUE).set_initial_supply(0).set_treasury_account_id(operator_id).set_supply_key(supply_key)
        )
        nft_receipt = nft_tx.freeze_with(client).sign(operator_key).execute(client)
        nft_token_id = nft_receipt.token_id

        # Create Fungible Token
        fungible_tx = (
            TokenCreateTransaction().set_token_name("Fungible Token").set_token_symbol("FTK").set_initial_supply(1).set_treasury_account_id(operator_id)
        )
        fungible_receipt = fungible_tx.freeze_with(client).sign(operator_key).execute(client)
        fungible_token_id = fungible_receipt.token_id

        print(f"✅ Success! Created NFT token: {nft_token_id} and fungible token: {fungible_token_id}")
        return client, nft_token_id, fungible_token_id, recipient_id, recipient_key

    except Exception as e:
        print(f"❌ Error creating tokens: {e}")
        sys.exit(1)

def token_associate():
    """
    Associate the tokens with the new account.

    Note: Tokens must be associated with an account before they can be used or dissociated.
    Association is a prerequisite for holding, transferring, or later dissociating tokens.
    """

    client, nft_token_id, fungible_token_id, recipient_id, recipient_key = create_token()

    print(f"\nSTEP 3: Associating NFT and fungible tokens with account {recipient_id}...")
    print("Note: Tokens must be associated with an account before they can be used or dissociated.")
    try:
        receipt = (
            TokenAssociateTransaction()
            .set_account_id(recipient_id)
            .add_token_id(nft_token_id)
            .add_token_id(fungible_token_id)
            .freeze_with(client)
            .sign(recipient_key)  # Recipient must sign to approve
            .execute(client)
        )
        print(f"✅ Success! Token association complete. Status: {receipt.status}")
        return client, nft_token_id, fungible_token_id, recipient_id, recipient_key
    except Exception as e:
        print(f"❌ Error associating tokens: {e}")
        sys.exit(1)

def token_dissociate():
    """
    Dissociate the tokens from the new account.

    Why dissociate?
    - To remove unwanted tokens from your account
    - To reduce account costs (some tokens may incur fees)
    - For security or privacy reasons
    - To comply with business or regulatory requirements
    """

    client, nft_token_id, fungible_token_id, recipient_id, recipient_key = token_associate()
    print(f"\nSTEP 4: Dissociating NFT and fungible tokens from account {recipient_id}...")
    try:
        receipt = (
            TokenDissociateTransaction()
            .set_account_id(recipient_id)
            .add_token_id(nft_token_id)
            .add_token_id(fungible_token_id)
            .freeze_with(client)
            .sign(recipient_key) # Recipient must sign to approve
            .execute(client)
        )
        print(f"✅ Success! Token dissociation complete for both NFT and fungible tokens.")

        # Optional: Verify dissociation
        print("\nVerifying token dissociation...") 
        info = AccountInfoQuery().set_account_id(recipient_id).execute(client)
        associated_tokens = [rel.token_id for rel in getattr(info, 'token_relationships', [])]
        if nft_token_id not in associated_tokens and fungible_token_id not in associated_tokens:
            print("✅ Verified: Both tokens are dissociated from the account.")
        else:
            print("❌ Verification failed: Some tokens are still associated.")

    except Exception as e:
        print(f"❌ Error dissociating tokens: {e}")
        sys.exit(1)


if __name__ == "__main__":
    token_dissociate()
