# CryptoCredit Backend API

CryptoCredit Backend is a FastAPI powered service that calculates a transparent and trustable **crypto credit score** by aggregating on chain user data.

The protocol enables decentralized accountability, empowering fairer financial decisions across the Web3 ecosystem.

Below is a breakdown of all the parameters currently considered in generating the **Crypto Credit Score**. These factors combine to form a transparent, trustable score that reflects on chain behavior.

---

## **1. Wallet & Account Parameters**

* **Wallet Age** – Time since the first recorded on chain transaction.
* **Number of Active Wallets** – Count of wallets linked to the user.
* **Wallet Verification Status** – Whether the wallet is verified by the user.

## **2. Transaction History**

* **Total Transaction Count** – All transactions across supported chains.
* **Transaction Volume (Native & USD)** – Total transferred value.
* **Average Transaction Value** – Mean value per transaction.
* **Frequency of Transactions** – Weekly/monthly activity levels.
* **Incoming vs Outgoing Ratio** – Balance of inflow vs outflow.
* **Stablecoin Transactions** – Share of transactions in stablecoins.

## **3. Staking Habits**

* **Total Assets Staked** – Amount of assets locked in staking.
* **Staking Duration** – How long assets remain staked.
* **Number of Staking Contracts** – Diversity of staking sources.
* **Rewards Earned** – Yield or rewards generated via staking.

## **4. DeFi Interactions**

* **Number of Protocols Used** – Unique DeFi protocols interacted with.
* **Liquidity Pool Contributions** – Assets provided to LPs.
* **Yield Farming Participation** – Frequency & scale of farming activities.
* **Borrowing & Lending History** – Usage of decentralized lending platforms.

## **5. Token Portfolio Insights**

* **Token Diversity** – Number of unique tokens held.
* **Blue chip vs. High risk Ratio** – Quality assessment of holdings.
* **Portfolio Volatility** – Value fluctuations over time.

## **6. Risk Indicators**

* **Rug Pull Exposure** – Past interactions with suspicious projects.
* **High gas Transactions** – Frequency of transactions with unusually high gas.
* **Contract Approval Count** – Number of active token approvals.

## **7. Reputation & Engagement**

* **NFT Ownership & Activity** – Number and type of NFTs owned.

##### All parameters are normalized and weighted according to the scoring model, which outputs a final score between 0 and 900.

---

## Features

* **User Authentication**: Sign up, sign in, refresh, and revoke tokens.
* **Chain Management**: Retrieve supported blockchain networks (76).
* **Wallet Tracking**: Add, verify, list, and delete wallets.
* **Scoring Engine**: Compute a 0 900 crypto credit score based on aggregated behavior.
* **RESTful API**: Fully documented OpenAPI spec.

---

## Authentication

The API uses **JWT Bearer tokens** for secure access.

To authorize, click the **Authorize** button in the API docs or send an `Authorization: Bearer <token>` header with your requests.

---

## Endpoints

### Auth

| Method | Endpoint              | Description                                     |
| ------ | --------------------- | ----------------------------------------------- |
| POST   | `/auth/sign_up`       | Create a new account.                           |
| POST   | `/auth/sign_in`       | Authenticate and receive access/refresh tokens. |
| POST   | `/auth/refresh_token` | Refresh access token using refresh token.       |
| POST   | `/auth/sign_out`      | Revoke tokens and sign out.                     |

### Chains

| Method | Endpoint   | Description                        |
| ------ | ---------- | ---------------------------------- |
| GET    | `/chains/` | Retrieve list of supported chains. |

### Wallets

| Method | Endpoint               | Description                          |
| ------ | ---------------------- | ------------------------------------ |
| GET    | `/wallets/`            | Get all linked wallets for the user. |
| POST   | `/wallets/`            | Add a new wallet to track.           |
| POST   | `/wallets/verify`      | Verify ownership of a wallet.        |
| DELETE | `/wallets/{wallet_id}` | Remove a linked wallet.              |

### Score

| Method | Endpoint  | Description                                        |
| ------ | --------- | -------------------------------------------------- |
| POST   | `/score/` | Calculate the credit score for the linked wallets. |

### Default

| Method | Endpoint | Description                             |
| ------ | -------- | --------------------------------------- |
| GET    | `/`      | Root endpoint for health/status checks. |

---

## Schemas

Some key request/response models:

* **UserCreate** — Sign up payload.
* **UserLogin** — Sign in payload.
* **RefreshToken** — Refresh token payload.
* **WalletCreate** — Payload for adding wallets.
* **WalletOut** — Wallet output model.
* **ScoreRequest** — Request payload for score calculation.
* **HTTPValidationError / ValidationError** — Standardized error formats.

---

## Installation & Setup

### Requirements

* Python 3.10+
* FastAPI
* SQLAlchemy
* PostgreSQL

### Steps

```bash
# Clone repository
git clone https://github.com/pratyakshkwatra/cryptocredit_backend
cd cryptocredit_backend

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your database & secret config

# Run server
uvicorn main:app --reload 
# or
fastapi dev main.py
```

API will be available at: **`http://localhost:8000`**
Docs will be available at: **`http://localhost:8000/docs`**

---

## Problem Statement

> **Design and develop a protocol that aggregates on-chain user behavior such as transaction history, staking habits, and DeFi interactions into a transparent, trustable crypto credit score.**
>
> The system should encourage accountability and enable fairer financial decisions in the decentralized ecosystem.

---
Made with 💜 by  [**Pratyaksh Kwatra**](https://github.com/pratyakshkwatra) & [**Aarav Rai**](https://github.com/Aarav-Rai)  
Fueled by ☕, powered by 🚀, and sprinkled with a bit of ✨ magic.
