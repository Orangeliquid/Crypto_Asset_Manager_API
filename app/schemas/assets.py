from pydantic import BaseModel
from datetime import datetime
from typing import List


class AssetBase(BaseModel):
    coin_name: str
    quantity: float
    purchase_value_usd: float

    class Config:
        from_attributes = True


class AssetCreate(AssetBase):
    pass


class AssetResponse(AssetBase):
    initial_purchase_date: datetime
    id: int

    class Config:
        from_attributes = True


class PaginatedAssetsResponse(BaseModel):
    total_count: int
    total_pages: int
    current_page: int
    total_wallet_value: float
    assets: List[AssetResponse]

    class Config:
        from_attributes = True


class AssetSellRequest(BaseModel):
    coin_name: str
    quantity: float


class AssetSellResponse(AssetSellRequest):
    sale_price_usd: float
    remaining_quantity: float
    message: str
