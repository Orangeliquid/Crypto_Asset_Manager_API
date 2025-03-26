from pydantic import BaseModel
from typing import Optional, List, Dict

from app.schemas.assets import AssetBase


class WalletBase(BaseModel):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class WalletCreate(WalletBase):
    pass


class WalletResponse(WalletBase):
    amount_of_coins: float
    total_value_usd: float
    assets: List[AssetBase]

    class Config:
        from_attributes = True


class WalletUpdate(BaseModel):
    quantity: Optional[float] = None
    value_usd: Optional[float] = None


class WalletValuationResponse(BaseModel):
    wallet_id: int
    snap_shot_date: str
    snap_shot_date_relative_to_historic_date: str
    holdings: Dict
    total_value_usd_on_snapshot_date: float
    date_requested_total_value: float
    net_gain_loss: float


class WalletDeleteResponse(BaseModel):
    message: str
