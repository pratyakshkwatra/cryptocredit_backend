from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, wallets, chains, score, api

app = FastAPI(
    title="CryptoCredit API",
    description="Backend for wallet tracking, scoring",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, tags=["Auth"])
app.include_router(chains.router, tags=["Chains"])
app.include_router(wallets.router, tags=["Wallets"])
app.include_router(score.router, tags=["Score"])
app.include_router(api.router, tags=["API"])

@app.get("/")
async def root():
    return {"message": "Welcome to the CryptoCredit API"}