from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)

    wallets = relationship("Wallet", back_populates="user")
    purchase_transactions = relationship("PurchaseTransaction", back_populates="user")
    sale_transactions = relationship("SaleTransaction", back_populates="user")


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="wallets")
    assets = relationship("Asset", back_populates="wallet")
    purchase_transactions = relationship("PurchaseTransaction", back_populates="wallet")
    sale_transactions = relationship("SaleTransaction", back_populates="wallet")

    @property
    def amount_of_coins(self):
        # Calculate the total number of coins (sum of all assets' quantities)
        return sum(asset.quantity for asset in self.assets)

    @property
    def total_value_usd(self):
        # Calculate the total value in USD (sum of all assets' values in USD)
        return sum(asset.purchase_value_usd for asset in self.assets)


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"))
    coin_name = Column(String, index=True)
    quantity = Column(Float, default=0.0)
    purchase_value_usd = Column(Float, default=0.0)
    initial_purchase_date = Column(DateTime, default=datetime.utcnow())

    wallet = relationship("Wallet", back_populates="assets")
    purchase_transactions = relationship("PurchaseTransaction", back_populates="asset")
    sale_transactions = relationship("SaleTransaction", back_populates="asset")


class PurchaseTransaction(Base):
    __tablename__ = "purchase_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    wallet_id = Column(Integer, ForeignKey("wallets.id"))
    asset_id = Column(Integer, ForeignKey("assets.id"))
    coin_name = Column(String)
    quantity_purchased = Column(Float)
    purchase_price = Column(Float)
    total_purchase_price = Column(Float)
    updated_coin_quantity = Column(Float)
    purchase_date = Column(DateTime, default=datetime.utcnow())

    user = relationship("User", back_populates="purchase_transactions")
    wallet = relationship("Wallet", back_populates="purchase_transactions")
    asset = relationship("Asset", back_populates="purchase_transactions")


class SaleTransaction(Base):
    __tablename__ = "sale_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    wallet_id = Column(Integer, ForeignKey("wallets.id"))
    asset_id = Column(Integer, ForeignKey("assets.id"))
    coin_name = Column(String)
    quantity_sold = Column(Float)
    sale_price = Column(Float)
    total_sale_price = Column(Float)
    remaining_coin_quantity = Column(Float)
    sale_date = Column(DateTime, default=datetime.utcnow())

    user = relationship("User", back_populates="sale_transactions")
    wallet = relationship("Wallet", back_populates="sale_transactions")
    asset = relationship("Asset", back_populates="sale_transactions")
