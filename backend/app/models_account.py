from sqlalchemy import Column, Integer, String
from app.db import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    balance = Column(Integer, nullable=False)
    type = Column(String, nullable=False)
