from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db_base import Base

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    key = Column(String, unique=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    total_calls = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)
    total_success = Column(Integer, default=0)

    owner = relationship("User", back_populates="api_keys")
