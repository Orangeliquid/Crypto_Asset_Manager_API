from pydantic import BaseModel


class AssetBase(BaseModel):
    asset_symbol: str
    quantity: float
    value_usd: float

    class Config:
        from_attributes = True


class AssetCreate(AssetBase):
    pass


class AssetResponse(AssetBase):
    id: int

    class Config:
        from_attributes = True
