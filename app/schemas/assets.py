from pydantic import BaseModel


class AssetBase(BaseModel):
    coin_name: str
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


class AssetSellRequest(BaseModel):
    coin_name: str
    quantity: float


class AssetSellResponse(AssetSellRequest):
    sale_price_usd: float
    remaining_quantity: float
    message: str
