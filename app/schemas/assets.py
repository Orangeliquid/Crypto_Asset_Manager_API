from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class AssetBase(BaseModel):
    coin_name: str
    quantity: float
    purchase_value_usd: float

    class Config:
        from_attributes = True


class AssetCreate(AssetBase):
    pass


class AssetResponse(AssetBase):
    coin_cap_id: str
    coin_cap_rank: int
    coin_cap_symbol: str

    current_price_usd: float
    current_value_usd: float
    net_gain_loss: float
    initial_purchase_date: datetime
    market_cap_usd: float
    supply: float
    max_supply: Optional[float] = 0.0
    volume_usd_24hr: float
    change_percent_24hr: float
    vwap_24hr: Optional[float] = 0.0
    explorer_url: Optional[str] = "Missing URL from CoinCapAPI"
    id: int

    class Config:
        from_attributes = True


class PaginatedAssetsResponse(BaseModel):
    total_count: int
    total_pages: int
    current_page: int
    total_wallet_value_usd: float
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
