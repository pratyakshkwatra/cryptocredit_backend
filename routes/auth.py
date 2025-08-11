from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional
from auth_deps import get_current_user
from database import get_db
from models.user import User
from models.token import BlacklistedToken
from schemas import RefreshToken, UserCreate, UserLogin, Token
import config as settings
import uuid

router = APIRouter(prefix="/auth", tags=["Auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({
        "exp": expire,
        "jti": str(uuid.uuid4()),
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None

@router.post("/sign_up", status_code=status.HTTP_200_OK)
def sign_up(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_pw)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "User registered successfully"}

@router.post("/sign_in")
def sign_in(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": str(db_user.id)})
    refresh_token = create_access_token(
        {"sub": str(db_user.id)}, expires_delta=timedelta(days=7)
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "email": db_user.email,
            "is_active": db_user.is_active,
        },
    }

@router.post("/refresh_token")
def refresh_token(refresh: RefreshToken, db: Session = Depends(get_db)):
    refresh_token = refresh.refresh_token
    payload = decode_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    jti = payload.get("jti")
    if not jti:
        raise HTTPException(status_code=401, detail="Missing jti in token")

    token_blacklisted = (
        db.query(BlacklistedToken)
          .filter(BlacklistedToken.jti == jti)
          .first()
    )
    if token_blacklisted:
        raise HTTPException(status_code=401, detail="Refresh token blacklisted")

    user_id = payload.get("sub")
    new_access_token = create_access_token({"sub": user_id})

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "email": db_user.email,
            "is_active": db_user.is_active,
        },
    }

@router.post("/sign_out")
def sign_out(
    access_token: str,
    refresh_token: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payload = decode_token(access_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid access token")

    jti = payload.get("jti")
    if not jti:
        raise HTTPException(status_code=401, detail="Missing jti in access token")

    db.add(BlacklistedToken(jti=jti))

    if refresh_token:
        refresh_payload = decode_token(refresh_token)
        if refresh_payload and refresh_payload.get("jti"):
            db.add(BlacklistedToken(jti=refresh_payload["jti"]))

    db.commit()

    return {"message": "Signed out successfully"}
