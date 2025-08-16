from covalent import CovalentClient
import requests
import config as settings
from routes.chains import chains
from routes.score import GOLDRUSH_BASE_URL, HEADERS
import secrets
import string

covalent_client = CovalentClient(settings.COVALENT_API_KEY)

def is_supported_chain(chain_symbol: str) -> bool:
    return chain_symbol.lower() in chains

def is_valid_address(address: str) -> bool:
    from web3 import Web3

    return Web3.is_address(address)

def can_fetch_data_from_goldrush(address: str, chain: str) -> bool:
    try:
        url = f"{GOLDRUSH_BASE_URL}/allchains/transactions/"
        params = {
            "chains": chain,
            "addresses": address,
            "limit": 1,
            "no-logs": "true"
        }
        resp = requests.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        data = resp.json().get("data", {})

        if "items" in data and isinstance(data["items"], list):
            return True
    except Exception:
        return False

    return False

def generate_api_key(length: int = 24) -> str:
    alphabet = string.ascii_letters + string.digits
    return "cck_" + ''.join(secrets.choice(alphabet) for _ in range(length))