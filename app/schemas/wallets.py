from pydantic import BaseModel
from typing import Optional, List

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


class WalletDeleteResponse(BaseModel):
    message: str
