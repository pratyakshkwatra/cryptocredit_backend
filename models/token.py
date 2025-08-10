from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from db_base import Base

class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    jti = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())