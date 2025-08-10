from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.wallet import Wallet
from schemas import WalletCreate, WalletOut
from auth_deps import get_current_user
from models.user import User
from utils import is_valid_address, can_fetch_data_from_goldrush
from random_name import generate_name

router = APIRouter(prefix="/wallets", tags=["Wallets"])

@router.get("/", response_model=list[WalletOut])
def get_wallets(
    chain: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return db.query(Wallet).filter(Wallet.user_id == current_user.id, Wallet.chain == chain).all()

@router.post("/verify")
def verify_wallet(wallet: WalletCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not is_valid_address(wallet.address):
        return {"message": "Invalid wallet address format.", "error": True}

    if not can_fetch_data_from_goldrush(wallet.address, wallet.chain):
        return {"message": "Wallet address could not be verified on the specified chain.",  "error": True}

    return {"message": "Wallet address and chain are valid and verified via goldrush.",  "error": False}


@router.post("/", response_model=WalletOut)
def add_wallet(
    wallet: WalletCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_valid_address(wallet.address):
        raise HTTPException(status_code=400, detail="Invalid wallet address format.")
    
    if str(wallet.nickname).strip() != "":
        nickname = str(wallet.nickname).strip()
    else:
        nickname = generate_name()
    

    db_wallet = Wallet(
        address=wallet.address, chain=wallet.chain, user_id=current_user.id, nickname=nickname
    )
    db.add(db_wallet)
    db.commit()
    db.refresh(db_wallet)
    return db_wallet

@router.delete("/{wallet_id}")
def delete_wallet(
    wallet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = (
        db.query(Wallet)
        .filter(Wallet.id == wallet_id, Wallet.user_id == current_user.id)
        .first()
    )
    if not wallet:
        raise HTTPException(
            status_code=404, detail="Wallet not found or not owned by user"
        )
    db.delete(wallet)
    db.commit()
    return {"message": "Wallet deleted"}