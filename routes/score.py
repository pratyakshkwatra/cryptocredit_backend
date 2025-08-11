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
    data = resp.json().get("data", {}).get("items", [])
    return data

def get_goldrush_token_balances(address: str, chain: str):
    url = f"{GOLDRUSH_BASE_URL}/{chain}/address/{address}/balances_v2/"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json().get("data", {}).get("items", [])

def get_goldrush_lending_data(address: str, chain: str):
    url = f"{GOLDRUSH_BASE_URL}/chains/{chain}/address/{address}/transactions/dex/"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        return []
    return resp.json().get("data", {}).get("items", [])

def analyze_tx_quality(txs):
    if not txs:
        return {
            "frequency_per_year": {},
            "frequency_per_month": {},
            "failure_rate": 0,
            "avg_tx_value": 0,
        }
    dates = [datetime.fromisoformat(tx["block_signed_at"]) for tx in txs if tx.get("block_signed_at")]
    freq_month = defaultdict(int)
    freq_year = defaultdict(int)
    for d in dates:
        freq_month[d.strftime("%Y-%m")] += 1
        freq_year[d.year] += 1
    total = len(txs)
    failures = sum(1 for tx in txs if not tx.get("successful", True))
    failure_rate = failures / total
    
    total_value_normalized = 0.0
    for tx in txs:
        raw_value = float(tx.get("value", 0))
        gas_metadata = tx.get("gas_metadata")
        if gas_metadata and gas_metadata.get("contract_decimals") is not None:
            decimals = gas_metadata["contract_decimals"]
        normalized_value = raw_value / (10 ** decimals) if decimals else raw_value
        total_value_normalized += normalized_value

    avg_value = total_value_normalized / total if total else 0

    return {
        "frequency_per_year": dict(freq_year),
        "frequency_per_month": dict(freq_month),
        "failure_rate": failure_rate,
        "avg_tx_value": avg_value,
    }


def analyze_diversification(txs, balances):
    unique_to_addresses = set()
    for tx in txs:
        if tx.get("to_address"):
            unique_to_addresses.add(tx["to_address"].lower())
    unique_tokens = set()
    for token in balances:
        contract = token.get("contract_address")
        if contract:
            unique_tokens.add(contract.lower())
    return {
        "unique_tokens_held": len(unique_tokens),
        "unique_to_addresses": len(unique_to_addresses),
    }

def analyze_lending(lending_data):
    total_borrowed = 0
    total_repaid = 0
    for loan in lending_data or []:
        total_borrowed += float(loan.get("borrowed_amount", 0))
        total_repaid += float(loan.get("repaid_amount", 0))
    repayment_rate = total_repaid / total_borrowed if total_borrowed > 0 else 0
    return {
        "total_borrowed": total_borrowed,
        "total_repaid": total_repaid,
        "repayment_rate": repayment_rate,
    }

def analyze_wallet_age_and_activity(txs):
    if not txs:
        return {"wallet_age_days": 0, "dormant_months": 0, "activity_burst_penalty": 0}
    dates = sorted(datetime.fromisoformat(tx["block_signed_at"]) for tx in txs if tx.get("block_signed_at"))
    now_utc = datetime.now(timezone.utc)
    first_tx_date = dates[0]
    if first_tx_date.tzinfo is None:
        first_tx_date = first_tx_date.replace(tzinfo=timezone.utc)
    wallet_age_days = (now_utc - first_tx_date).days
    tx_months = set(d.strftime("%Y-%m") for d in dates)
    first_month = dates[0].replace(day=1)
    last_month = dates[-1].replace(day=1)
    total_months = (last_month.year - first_month.year) * 12 + (last_month.month - first_month.month) + 1
    dormant_months = total_months - len(tx_months)
    from statistics import variance
    freq_per_month = defaultdict(int)
    for d in dates:
        freq_per_month[d.strftime("%Y-%m")] += 1
    counts = list(freq_per_month.values())
    var = variance(counts) if len(counts) > 1 else 0
    activity_burst_penalty = min(var * 10, 100)
    return {
        "wallet_age_days": wallet_age_days,
        "dormant_months": dormant_months,
        "activity_burst_penalty": activity_burst_penalty,
    }

def analyze_gas_usage(txs):
    print(txs[0])
    gas_prices = [float(tx.get("gas_price", 0)) for tx in txs if tx.get("gas_price")]
    if not gas_prices:
        return {"avg_gas_price": 0, "median_gas_price": 0, "gas_price_ratio": 0}
    gas_prices.sort()
    n = len(gas_prices)
    median_gas = gas_prices[n // 2] if n % 2 == 1 else (gas_prices[n // 2 - 1] + gas_prices[n // 2]) / 2
    avg_gas = sum(gas_prices) / n
    gas_price_ratio = avg_gas / median_gas if median_gas > 0 else 0
    return {
        "avg_gas_price": avg_gas,
        "median_gas_price": median_gas,
        "gas_price_ratio": gas_price_ratio,
    }

def analyze_liquidity_lockup(balances):
    total_balance = 0.0
    for token in balances:
        quote_value = token.get("quote", 0) or 0
        quote_float = float(quote_value)
        total_balance += quote_float

    return {
        "total_balance": total_balance,
        "liquid_balance": total_balance,
        "locked_up_balance": 0,
        "lockup_ratio": 0,
    }

def analyze_incoming_outgoing(txs, address):
    address = address.lower()
    incoming_count = 0
    outgoing_count = 0
    incoming_value = 0.0
    outgoing_value = 0.0
    for tx in txs:
        from_addr = tx.get("from_address", "").lower()
        to_addr = tx.get("to_address", "").lower()
        value = float(tx.get("value", 0))
        if to_addr == address:
            incoming_count += 1
            incoming_value += value
        if from_addr == address:
            outgoing_count += 1
            outgoing_value += value
    return {
        "incoming_count": incoming_count,
        "outgoing_count": outgoing_count,
        "incoming_value": incoming_value,
        "outgoing_value": outgoing_value,
        "incoming_outgoing_count_ratio": (incoming_count / outgoing_count) if outgoing_count > 0 else None,
        "incoming_outgoing_value_ratio": (incoming_value / outgoing_value) if outgoing_value > 0 else None,
    }

def analyze_inter_tx_time(txs):
    if len(txs) < 2:
        return {"avg_inter_tx_seconds": None, "std_inter_tx_seconds": None}
    dates = sorted(datetime.fromisoformat(tx["block_signed_at"]) for tx in txs if tx.get("block_signed_at"))
    diffs = [(dates[i+1] - dates[i]).total_seconds() for i in range(len(dates)-1)]
    from statistics import mean, stdev
    avg_diff = mean(diffs)
    std_diff = stdev(diffs) if len(diffs) > 1 else 0
    return {"avg_inter_tx_seconds": avg_diff, "std_inter_tx_seconds": std_diff}

def analyze_avg_tx_fee(txs):
    fees = []
    for tx in txs:
        gas_price = float(tx.get("gas_price", 0))
        gas_used = float(tx.get("gas_used", 0))
        if gas_price > 0 and gas_used > 0:
            fees.append(gas_price * gas_used)
    if not fees:
        return {"avg_tx_fee": 0, "median_tx_fee": 0}
    fees.sort()
    n = len(fees)
    median_fee = fees[n // 2] if n % 2 == 1 else (fees[n // 2 - 1] + fees[n // 2]) / 2
    avg_fee = sum(fees) / n
    return {"avg_tx_fee": avg_fee, "median_tx_fee": median_fee}

class CreditScoreCalculator:
    def __init__(self, analyses: dict):
        self.analyses = analyses

    def score_metric(self, value, min_val, avg_val, max_val, max_score):
        if value is None:
            return 0
        if value <= min_val:
            return 0
        if value >= max_val:
            return max_score
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
            "balance": 20,
            "liquidity_lockup": 10,
            "tx_frequency": 15,
            "tx_value": 10,
            "failure_penalty": 10,
            "diversification_tokens": 10,
            "diversification_addresses": 5,
            "lending": 10,
            "wallet_age": 10,
            "dormancy_penalty": 5,
            "activity_burst_penalty": 5,
            "gas_efficiency": 10,
        }
        max_raw_score = sum(max_scores.values())

        total_balance = a["liquidity_lockup"]["total_balance"]
        lockup_ratio = a["liquidity_lockup"]["lockup_ratio"]

        balance_score = self.score_metric(total_balance, 0, 1000, 25000, max_scores["balance"])
        liquidity_lockup_score = self.score_metric(lockup_ratio, 0.0, 0.0, 0.0, max_scores["liquidity_lockup"])
        tx_frequency_score = self.score_metric(sum(a["tx_quality"]["frequency_per_year"].values()), 0, 50, 300, max_scores["tx_frequency"])
        tx_value_score = self.score_metric(a["tx_quality"]["avg_tx_value"], 0, 50, 500, max_scores["tx_value"])
        failure_penalty = (1 - a["tx_quality"]["failure_rate"]) * max_scores["failure_penalty"]
        diversification_tokens_score = self.score_metric(a["diversification"]["unique_tokens_held"], 0, 5, 20, max_scores["diversification_tokens"])
        diversification_addresses_score = self.score_metric(a["diversification"]["unique_to_addresses"], 0, 10, 50, max_scores["diversification_addresses"])
        lending_score = self.score_metric(a["lending"]["repayment_rate"], 0, 0.5, 1.0, max_scores["lending"])
        wallet_age_score = self.score_metric(a["wallet_age"]["wallet_age_days"], 0, 180, 1095, max_scores["wallet_age"])
        dormancy_penalty = max(0, max_scores["dormancy_penalty"] - (a["wallet_age"]["dormant_months"] / 2))
        activity_burst_penalty = max(0, max_scores["activity_burst_penalty"] - (a["wallet_age"]["activity_burst_penalty"] / 10))
        gas_efficiency_score = max(0, max_scores["gas_efficiency"] - (a["gas_usage"]["gas_price_ratio"] - 1) * 10)

        raw_total = (
            balance_score + liquidity_lockup_score + tx_frequency_score + tx_value_score +
            failure_penalty + diversification_tokens_score + diversification_addresses_score + lending_score +
            wallet_age_score + dormancy_penalty + activity_burst_penalty + gas_efficiency_score
        )

        scaled_score = (raw_total / max_raw_score) * 900
        final_score = max(0, min(scaled_score, 900))
        return round(final_score)

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
        lending_data = get_goldrush_lending_data(address, chain_name)
    except requests.HTTPError as e:
        print(e)
        raise HTTPException(status_code=503, detail=f"Goldrush API error: {str(e)}")

    tx_quality = analyze_tx_quality(txs)
    diversification = analyze_diversification(txs, balances)
    lending = analyze_lending(lending_data)
    wallet_age = analyze_wallet_age_and_activity(txs)
    gas_usage = analyze_gas_usage(txs)
    liquidity_lockup = analyze_liquidity_lockup(balances)
    incoming_outgoing = analyze_incoming_outgoing(txs, address)
    inter_tx_time = analyze_inter_tx_time(txs)
    avg_tx_fee = analyze_avg_tx_fee(txs)

    analyses = {
        "tx_quality": tx_quality,
        "diversification": diversification,
        "lending": lending,
        "wallet_age": wallet_age,
        "gas_usage": gas_usage,
        "liquidity_lockup": liquidity_lockup,
        "incoming_outgoing": incoming_outgoing,
        "inter_transaction_time": inter_tx_time,
        "average_transaction_fee": avg_tx_fee,
    }

    calc = CreditScoreCalculator(analyses)
    score = calc.calculate_score()

    with open(f"data/{datetime.now()}.json", "w") as f:
        import json
        json.dump({
            "credit_score": score,
            "details": analyses,
            "transactions": txs,
        }, f, indent=4)

    return {
        "credit_score": score,
        "details": analyses,
        "transactions": txs,
    }
