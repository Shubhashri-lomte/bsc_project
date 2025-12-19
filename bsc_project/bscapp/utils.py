from web3 import Web3
from eth_account import Account
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes

# Configuration Constants
BSC_TESTNET_RPC_URL = "https://data-seed-prebsc-1-s1.binance.org:8545/"
BSC_TESTNET_CHAIN_ID = 97
EXAMPLE_TOKEN_ADDRESS = "0x64544969Ed7ebF5f083679233325356EBE738930"

# We lower this to allow testing with small amounts (e.g., 0.001)
# 0.0001 is enough to cover several simple transfers
TEST_MIN_BALANCE = 0.0001

# Standard ERC-20/BEP-20 ABI
MIN_BEP20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf",
     "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
     "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
]

w3 = Web3(Web3.HTTPProvider(BSC_TESTNET_RPC_URL))


def has_minimum_balance(address, estimated_gas_limit=21000):
    """
    Checks if address has enough BNB to cover gas.
    Uses current gas price to determine the actual minimum needed.
    """
    balance_wei = w3.eth.get_balance(address)
    gas_price = w3.eth.gas_price
    # Actual cost to send = gas_limit * current_gas_price
    min_required_wei = estimated_gas_limit * gas_price

    return balance_wei >= min_required_wei, balance_wei


def generate_bsc_wallet():
    mnemonic = Bip39MnemonicGenerator().FromWordsNumber(12)
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
    bip44_acc = bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
    private_key_hex = bip44_acc.PrivateKey().Raw().ToHex()
    acct = Account.from_key(private_key_hex)
    return {
        "mnemonic": str(mnemonic),
        "private_key": f"0x{private_key_hex}",
        "public_key": f"0x{bip44_acc.PublicKey().RawCompressed().ToHex()}",
        "bsc_testnet_address": acct.address,
        "derivation_path": "m/44'/60'/0'/0/0"
    }


def send_bnb_safe(sender_private_key, recipient_address, amount_bnb):
    try:
        sender_account = Account.from_key(sender_private_key)

        # 1. Validation for Native BNB Transfer (Gas Limit: 21,000)
        is_valid, balance_wei = has_minimum_balance(sender_account.address, 21000)
        if not is_valid:
            return {"status": "error",
                    "message": f"Insufficient BNB for gas. Balance: {w3.from_wei(balance_wei, 'ether')} BNB"}

        # 2. Dynamic Value Calculation (Subtract gas if balance is tight)
        requested_wei = w3.to_wei(float(amount_bnb), 'ether')
        gas_price = w3.eth.gas_price
        total_gas_cost = 21000 * gas_price

        if requested_wei + total_gas_cost > balance_wei:
            # Send 'Maximum available' instead of failing
            send_value_wei = balance_wei - total_gas_cost
        else:
            send_value_wei = requested_wei

        if send_value_wei <= 0:
            return {"status": "error", "message": "Balance cannot cover transaction fees."}

        txn = {
            'chainId': BSC_TESTNET_CHAIN_ID,
            'to': w3.to_checksum_address(recipient_address),
            'value': send_value_wei,
            'nonce': w3.eth.get_transaction_count(sender_account.address),
            'gas': 21000,
            'gasPrice': gas_price
        }

        signed = w3.eth.account.sign_transaction(txn, sender_private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        return {"status": "success", "tx_hash": tx_hash.hex(), "amount_sent": str(w3.from_wei(send_value_wei, 'ether'))}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def send_bep20_token_safe(sender_private_key, token_address, receiver_address, amount_tokens):
    try:
        sender_account = Account.from_key(sender_private_key)

        # 1. Validation for Token Transfer (Tokens require more gas: ~65,000)
        is_valid, balance_wei = has_minimum_balance(sender_account.address, 65000)
        if not is_valid:
            readable_bal = w3.from_wei(balance_wei, 'ether')
            return {
                "status": "error",
                "message": f"Token Transfer Failed: You need more BNB for gas. Current: {readable_bal} BNB"
            }

        # 2. CONTRACT INTERACTION
        contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=MIN_BEP20_ABI)
        decimals = contract.functions.decimals().call()
        amount_raw = int(float(amount_tokens) * (10 ** decimals))

        txn = contract.functions.transfer(
            w3.to_checksum_address(receiver_address),
            amount_raw
        ).build_transaction({
            'chainId': BSC_TESTNET_CHAIN_ID,
            'from': sender_account.address,
            'nonce': w3.eth.get_transaction_count(sender_account.address),
            'gas': 65000,
            'gasPrice': w3.eth.gas_price
        })

        signed = w3.eth.account.sign_transaction(txn, sender_private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        return {"status": "success", "tx_hash": tx_hash.hex()}
    except Exception as e:
        return {"status": "error", "message": str(e)}