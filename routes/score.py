from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from database import get_db
from auth_deps import get_current_user
from schemas import ScoreRequest
from models.user import User
from covalent import CovalentClient
import config as settings
from routes.chains import chains

router = APIRouter(prefix="/score", tags=["Score"])

COVALENT_API_KEY = settings.COVALENT_API_KEY
covalent_client = CovalentClient(COVALENT_API_KEY)

# def analyze_diversification(transactions: list) -> dict:
#     if not transactions:
#         return {
#             "unique_contracts_interacted": 0,
#             "diversification_score": 0,
#             "interacted_protocols": [],
#         }
#     interacted_addresses = {tx.to_address for tx in transactions if tx.to_address}
#     interacted_reputable_protocols = {
#         REPUTABLE_PROTOCOLS[addr]
#         for addr in interacted_addresses
#         if addr in REPUTABLE_PROTOCOLS
#     }
#     score = min(len(interacted_reputable_protocols), 10) * 10
#     return {
#         "unique_contracts_interacted": len(interacted_addresses),
#         "diversification_score": score,
#         "interacted_protocols": list(interacted_reputable_protocols),
#     }

def analyze_staking_habits(transactions: list) -> dict:
    staking_keywords = {"stake", "delegate", "deposit"}
    unstaking_keywords = {"unstake", "withdraw", "redeem", "unbond"}
    stake_count = 0
    unstake_count = 0
    for tx in transactions:
        if tx.log_events:
            for log in tx.log_events:
                if log.decoded and log.decoded.name:
                    log_name = log.decoded.name.lower()
                    if any(keyword in log_name for keyword in staking_keywords):
                        stake_count += 1
                        break
                    if any(keyword in log_name for keyword in unstaking_keywords):
                        unstake_count += 1
                        break
    total_actions = stake_count + unstake_count
    commitment_score = (
        round((stake_count / total_actions) * 100) if total_actions > 0 else 0
    )
    return {
        "staking_events": stake_count,
        "unstaking_events": unstake_count,
        "staking_commitment_score": commitment_score,
    }

class CovalentFetcher:
    def __init__(self, api_key):
        self.client = CovalentClient(api_key)

    def get_transactions(self, address, chain_name, tx_limit=10):
        if not chain_name:
            return []
        resp = self.client.transaction_service.get_transactions_for_address_v3(
            chain_name, address, page_size=tx_limit
        )
        return resp.data.items if not resp.error else []

    def get_token_balances(self, address, chain_name):
        if not chain_name:
            return []
        resp = self.client.balance_service.get_token_balances_for_wallet_address(
            chain_name, address
        )
        return resp.data.items if not resp.error else []

    def get_nft_transfers(self, address, chain_name):
        if not chain_name:
            return []
        resp = self.client.nft_service.get_nfts_for_address(chain_name, address)
        return resp.data.items if not resp.error else []

class CreditScoreCalculator:
    def __init__(self, txs, balances, nfts, staking_analysis):
        self.txs = txs
        self.balances = balances
        self.nfts = nfts
        self.staking_analysis = staking_analysis

    @staticmethod
    def score_metric(value, min_val, avg_val, max_val, max_score):
        if value <= min_val:
            return 0
        if value >= max_val:
            return max_score
        half_score = max_score / 2
        if value <= avg_val:
            denom = avg_val - min_val
            return (
                ((value - min_val) / denom) * half_score if denom != 0 else half_score
            )
        else:
            denom = max_val - avg_val
            return (
                half_score + ((value - avg_val) / denom) * half_score
                if denom != 0
                else max_score
            )

    def calculate_score(self):
        balance_stats = {
            "min_val": 0,
            "avg_val": 1000,
            "max_val": 25000,
            "max_score": 30,
        }
        total_balance = sum(float(token.quote or 0) for token in self.balances)
        balance_score = round(self.score_metric(total_balance, **balance_stats))

        diversification_score_raw = self.diversification_analysis.get(
            "diversification_score", 0
        )
        diversification_score = round((diversification_score_raw / 100) * 25)

        staking_score_raw = self.staking_analysis.get("staking_commitment_score", 0)
        staking_score = round((staking_score_raw / 100) * 20)

        tx_stats = {"min_val": 0, "avg_val": 50, "max_val": 300, "max_score": 15}
        tx_count = len(self.txs)
        tx_score = round(self.score_metric(tx_count, **tx_stats))

        nft_stats = {"min_val": 0, "avg_val": 5, "max_val": 50, "max_score": 10}
        nft_count = len(self.nfts)
        nft_score = round(self.score_metric(nft_count, **nft_stats))

        total_score = (
            balance_score + diversification_score + staking_score + tx_score + nft_score
        )
        return min(total_score, 100)

@router.post("/", tags=["Score"])
def score_endpoint(
    req: ScoreRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    chain_name = chains.get(req.chain.lower())
    if not chain_name:
        raise HTTPException(
            status_code=400, detail="Unsupported or invalid chain specified."
        )

    fetcher = CovalentFetcher(COVALENT_API_KEY)

    txs = fetcher.get_transactions(req.address, chain_name, req.tx_limit)
    balances = fetcher.get_token_balances(req.address, chain_name)
    nfts = fetcher.get_nft_transfers(req.address, chain_name)

    # diversification_analysis = analyze_diversification(txs)
    staking_analysis = analyze_staking_habits(txs)

    calc = CreditScoreCalculator(
        txs, balances, nfts, staking_analysis
    )
    score = calc.calculate_score()

    return {
        "credit_score": score,
        "transactions": txs,
        # "details": {
        #     "transactions_count": len(txs),
        #     "total_balance_usd": sum(float(token.quote or 0) for token in balances),
        #     "nft_count": len(nfts),
        #     "staking": staking_analysis,
        # },
    }