from sqlalchemy import Column, Integer, String
from app.db import Base


class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
