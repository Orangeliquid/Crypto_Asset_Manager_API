from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class PurchaseTransactionBase(BaseModel):
    user_id: int
    wallet_id: int
    asset_id: int
    coin_name: str
    quantity_purchased: float
    purchase_price: float

    class Config:
        from_attributes = True


class PurchaseTransactionResponse(PurchaseTransactionBase):
    total_purchase_price: float
    updated_coin_quantity: float
    purchase_date: datetime
    id: int

    class Config:
        from_attributes = True


class SaleTransactionBase(BaseModel):
    user_id: int
    wallet_id: int
    asset_id: int
    coin_name: str
    quantity_sold: float
    sale_price: float

    class Config:
        from_attributes = True


class SaleTransactionResponse(SaleTransactionBase):
    total_sale_price: float
    remaining_coin_quantity: float
    id: int
    sale_date: datetime

    class Config:
        from_attributes = True


class TransactionTypeEnum(str, Enum):
    PURCHASE = "purchase"
    SALE = "sale"


class Transaction(BaseModel):
    id: int
    coin_name: str
    quantity: float
    price_per_coin: float
    total_price: float
    transaction_date: datetime
    type: TransactionTypeEnum

    class Config:
        from_attributes = True


class PaginatedTransactionsResponse(BaseModel):
    transactions: List[Transaction]
    total_transactions: int
    total_pages: int
    current_page: int

    class Config:
        from_attributes = True


class WalletValuationResponse(BaseModel):
    wallet_id: int
    start_value_usd: Optional[float] = None
    end_value_usd: float
    net_gain_loss_usd: float
    current_value_usd: float

    class Config:
        from_attributes = True
