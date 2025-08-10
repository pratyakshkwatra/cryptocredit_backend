from covalent import CovalentClient
import config as settings
from routes.chains import chains

covalent_client = CovalentClient(settings.COVALENT_API_KEY)

def is_supported_chain(chain_symbol: str) -> bool:
    return chain_symbol.lower() in chains

def is_valid_address(address: str) -> bool:
    from web3 import Web3

    return Web3.is_address(address)

def can_fetch_data_from_goldrush(address: str, chain: str) -> bool:
    try:
        resp = covalent_client.balance_service.get_token_balances_for_wallet_address(
            chain, address
        )

        if resp.error:
            return False

        if hasattr(resp.data, "items") and isinstance(resp.data.items, list):
            return True
    except Exception:
        return False

    return False