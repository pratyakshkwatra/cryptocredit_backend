from covalent import CovalentClient
import config as settings
from routes.chains import chains

covalent_client = CovalentClient(settings.COVALENT_API_KEY)

def is_supported_chain(chain_symbol: str) -> bool:
    return chain_symbol.lower() in chains

def is_valid_address(address: str) -> bool:
    from web3 import Web3

    return Web3.isAddress(address)

def can_fetch_data_from_goldrush(address: str, chain_symbol: str) -> bool:
    """
    Use Covalent SDK to check if token balances can be fetched for wallet + chain.
    """
    chain_key = chain_symbol.lower()
    chain_name = chains.get(chain_key)
    if not chain_name:
        return False

    try:
        resp = covalent_client.balance_service.get_token_balances_for_wallet_address(
            chain_name, address
        )

        if resp.error:
            return False

        if hasattr(resp.data, "items") and isinstance(resp.data.items, list):
            return True
    except Exception:
        return False

    return False