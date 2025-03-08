from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)

    wallets = relationship("Wallet", back_populates="owner")


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="wallets")
    assets = relationship("Asset", back_populates="wallet")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"))
    asset_symbol = Column(String, index=True)
    quantity = Column(Float, default=0.0)
    value_usd = Column(Float, default=0.0)

    wallet = relationship("Wallet", back_populates="assets")
