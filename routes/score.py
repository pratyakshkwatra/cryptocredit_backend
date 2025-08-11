import requests
from datetime import datetime, timezone
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from database import get_db
from auth_deps import get_current_user
from schemas import ScoreRequest
from sqlalchemy.orm import Session
from models.user import User
import config as settings
import statistics

router = APIRouter(tags=["Score"], prefix="/score")

GOLDRUSH_API_KEY = settings.COVALENT_API_KEY
GOLDRUSH_BASE_URL = "https://api.covalenthq.com/v1"
HEADERS = {"Authorization": f"Bearer {GOLDRUSH_API_KEY}"}

def get_goldrush_transactions(address: str, chain: str, tx_limit: int):
    url = f"{GOLDRUSH_BASE_URL}/allchains/transactions/"
    params = {
        "chains": chain,
        "addresses": address,
        "limit": tx_limit,
        "no-logs": "true"
    }
    resp = requests.get(url, headers=HEADERS, params=params)
    resp.raise_for_status()
    data = resp.json().get("data", {})
    return data.get("items", []) if data else []

def get_goldrush_token_balances(address: str, chain: str):
    url = f"{GOLDRUSH_BASE_URL}/{chain}/address/{address}/balances_v2/"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json().get("data", {})
    return data.get("items", []) if data else []

def analyze_tx_quality(txs):
    if not txs:
        return {
            "frequency_per_month": {},
            "frequency_per_year": {},
            "failure_rate": 1.0,
            "avg_tx_value_usd": 0.0,
        }

    dates = [datetime.fromisoformat(tx["block_signed_at"]) for tx in txs if tx.get("block_signed_at")]
    freq_month = defaultdict(int)
    freq_year = defaultdict(int)
    for d in dates:
        freq_month[d.strftime("%Y-%m")] += 1
        freq_year[d.year] += 1

    total_txs = len(txs)
    failures = sum(1 for tx in txs if not tx.get("successful", True))
    failure_rate = failures / total_txs if total_txs > 0 else 0

    total_value_usd = sum(tx.get("value_quote", 0) for tx in txs)
    avg_value_usd = total_value_usd / total_txs if total_txs > 0 else 0

    return {
        "frequency_per_month": dict(freq_month),
        "frequency_per_year": dict(freq_year),
        "failure_rate": failure_rate,
        "avg_tx_value_usd": avg_value_usd,
    }

def analyze_diversification(txs, balances):
    unique_to_addresses = {tx["to_address"].lower() for tx in txs if tx.get("to_address")}
    unique_tokens = {token.get("contract_address") for token in balances if token.get("contract_address")}
    return {
        "unique_tokens_held": len(unique_tokens),
        "unique_to_addresses": len(unique_to_addresses),
    }

def analyze_wallet_age_and_activity(chain_name, wallet_address):
    url = f"https://api.covalenthq.com/v1/{chain_name}/address/{wallet_address}/transactions_summary/"
    headers = {"Authorization": f"Bearer {GOLDRUSH_API_KEY}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"API request failed: {response.status_code} {response.text}")

    data = response.json()

    if not data.get("data") or not data["data"].get("items") or not data["data"]["items"][0].get("earliest_transaction"):
        today_str = datetime.now().strftime("%d-%m-%Y")
        return {
            "wallet_age_days": 0,
            "first_tx_date": today_str,
            "last_tx_date": today_str
        }

    item = data["data"]["items"][0]

    first_tx_str = item["earliest_transaction"]["block_signed_at"]
    last_tx_str = item.get("latest_transaction", {}).get("block_signed_at", first_tx_str)

    first_tx_date = datetime.fromisoformat(first_tx_str.replace("Z", "+00:00"))
    last_tx_date = datetime.fromisoformat(last_tx_str.replace("Z", "+00:00"))

    now_utc = datetime.now(timezone.utc)
    wallet_age_days = (now_utc - first_tx_date).days

    return {
        "wallet_age_days": wallet_age_days,
        "first_tx_date": first_tx_date.strftime("%d-%m-%Y"),
        "last_tx_date": last_tx_date.strftime("%d-%m-%Y"),
    }

def analyze_gas_usage(txs):
    gas_prices = [float(tx.get("gas_price", 0)) for tx in txs if tx.get("gas_price")]
    if not gas_prices:
        return {"avg_gas_price": 0, "median_gas_price": 0, "gas_price_ratio": 0}
    
    gas_prices.sort()
    n = len(gas_prices)
    avg_gas = statistics.mean(gas_prices)
    median_gas = statistics.median(gas_prices)
    gas_price_ratio = avg_gas / median_gas if median_gas > 0 else 0
    
    return {
        "avg_gas_price": avg_gas,
        "median_gas_price": median_gas,
        "gas_price_ratio": gas_price_ratio,
    }

def analyze_total_balance(balances):
    total_balance_usd = sum(token.get("quote", 0.0) or 0.0 for token in balances)
    return {"total_balance_usd": total_balance_usd}

def analyze_incoming_outgoing(txs, address):
    address = address.lower()
    incoming_count, outgoing_count = 0, 0
    incoming_value, outgoing_value = 0.0, 0.0

    for tx in txs:
        value = tx.get("value_quote", 0.0)
        if tx.get("to_address", "").lower() == address:
            incoming_count += 1
            incoming_value += value
        if tx.get("from_address", "").lower() == address:
            outgoing_count += 1
            outgoing_value += value
            
    return {
        "incoming_count": incoming_count,
        "outgoing_count": outgoing_count,
        "incoming_value_usd": incoming_value,
        "outgoing_value_usd": outgoing_value,
        "io_count_ratio": (incoming_count / outgoing_count) if outgoing_count > 0 else None,
        "io_value_ratio": (incoming_value / outgoing_value) if outgoing_value > 0 else None,
    }

def analyze_inter_tx_time(txs):
    if len(txs) < 2:
        return {"avg_inter_tx_seconds": None, "std_inter_tx_seconds": None}

    dates = sorted([datetime.fromisoformat(tx["block_signed_at"]) for tx in txs if tx.get("block_signed_at")])
    if len(dates) < 2:
        return {"avg_inter_tx_seconds": None, "std_inter_tx_seconds": None}

    diffs_seconds = [(dates[i+1] - dates[i]).total_seconds() for i in range(len(dates)-1)]
    
    return {
        "avg_inter_tx_seconds": statistics.mean(diffs_seconds),
        "std_inter_tx_seconds": statistics.stdev(diffs_seconds) if len(diffs_seconds) > 1 else 0,
    }

class CreditScoreCalculator:
    def __init__(self, analyses: dict):
        self.analyses = analyses

    def score_metric(self, value, min_val, avg_val, max_val, max_score):
        if value is None or value <= min_val: return 0
        if value >= max_val: return max_score
        half_score = max_score / 2
        if value <= avg_val:
            denom = avg_val - min_val
            return ((value - min_val) / denom) * half_score if denom != 0 else half_score
        else:
            denom = max_val - avg_val
            return half_score + ((value - avg_val) / denom) * half_score if denom != 0 else max_score

    def calculate_score(self):
        a = self.analyses
        max_scores = {
            "balance": 35,
            "tx_frequency": 20,
            "tx_value": 20,
            "failure_penalty": 10,
            "diversification_tokens": 10,
            "diversification_addresses": 5,
            "wallet_age": 15,
            "gas_efficiency": 10,
        }
        max_raw_score = sum(max_scores.values())

        balance_score = self.score_metric(a["total_balance"]["total_balance_usd"], 0, 1000, 25000, max_scores["balance"])
        tx_frequency_score = self.score_metric(sum(a["tx_quality"]["frequency_per_year"].values()), 0, 50, 300, max_scores["tx_frequency"])
        tx_value_score = self.score_metric(a["tx_quality"]["avg_tx_value_usd"], 0, 100, 2000, max_scores["tx_value"])
        failure_penalty = (1 - a["tx_quality"]["failure_rate"]) * max_scores["failure_penalty"]
        diversification_tokens_score = self.score_metric(a["diversification"]["unique_tokens_held"], 0, 5, 20, max_scores["diversification_tokens"])
        diversification_addresses_score = self.score_metric(a["diversification"]["unique_to_addresses"], 0, 10, 50, max_scores["diversification_addresses"])
        wallet_age_score = self.score_metric(a["wallet_age"]["wallet_age_days"], 0, 180, 1095, max_scores["wallet_age"])
        gas_efficiency_score = max(0, max_scores["gas_efficiency"] * (2 - a["gas_usage"]["gas_price_ratio"]))

        raw_total = (
            balance_score + tx_frequency_score + tx_value_score +
            failure_penalty + diversification_tokens_score + diversification_addresses_score +
            wallet_age_score + gas_efficiency_score
        )

        final_score = (raw_total / max_raw_score) * 1.15 * 900 if max_raw_score > 0 else 0
        return round(max(0, min(final_score, 900)))

@router.post("/", tags=["Score"])
def score_endpoint(
    req: ScoreRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    chain_name = req.chain.lower()
    address = req.address.lower()
    tx_limit = req.tx_limit or 100

    try:
        txs = get_goldrush_transactions(address, chain_name, tx_limit)
        balances = get_goldrush_token_balances(address, chain_name)
    except requests.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"External API Error: {str(e)}")

    analyses = {
        "tx_quality": analyze_tx_quality(txs),
        "diversification": analyze_diversification(txs, balances),
        "wallet_age": analyze_wallet_age_and_activity(chain_name, address),
        "gas_usage": analyze_gas_usage(txs),
        "total_balance": analyze_total_balance(balances),
        "incoming_outgoing": analyze_incoming_outgoing(txs, address),
        "inter_transaction_time": analyze_inter_tx_time(txs),
    }

    calc = CreditScoreCalculator(analyses)
    score = calc.calculate_score()

    return {
        "credit_score": score,
        "details": analyses,
        "txs": txs
    }