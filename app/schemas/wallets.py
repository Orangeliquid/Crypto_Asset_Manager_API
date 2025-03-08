from pydantic import BaseModel
from typing import Optional, List

from app.schemas.assets import AssetResponse


class WalletBase(BaseModel):
    asset_symbol: Optional[str] = None
    quantity: Optional[float] = 0.0
    value_usd: Optional[float] = 0.0

    class Config:
        from_attributes = True


class WalletCreate(WalletBase):
    user_id: int


class WalletResponse(WalletBase):
    id: int
    user_id: int
    assets: List[AssetResponse]

    class Config:
        from_attributes = True


class WalletUpdate(BaseModel):
    quantity: Optional[float] = None
    value_usd: Optional[float] = None
