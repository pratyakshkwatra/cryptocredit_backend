from typing import Optional, List
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class RefreshToken(BaseModel):
    refresh_token: str

class UserOut(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    sub: Optional[str] = None

class WalletBase(BaseModel):
    address: str
    chain: str
    nickname: str

class WalletCreate(WalletBase):
    pass

class WalletOut(WalletBase):
    id: int
    address: str
    chain: str
    nickname: str

    class Config:
        orm_mode = True

class ChainResponse(BaseModel):
    name: str
    chain_id: str
    rpc_url: str

class ScoreRequest(BaseModel):
    address: str
    chain: str
    tx_limit: int

class ScoreResponse(BaseModel):
    score: int

class LLMRequest(BaseModel):
    prompt: str

class LLMResponse(BaseModel):
    output: str

class BlacklistedTokenResponse(BaseModel):
    jti: str
    created_at: str

    class Config:
        orm_mode = True
