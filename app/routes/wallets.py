from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.wallets import WalletResponse
from app.schemas.assets import AssetResponse
from app.crud.wallets import crud_create_wallet, crud_add_asset_to_wallet, crud_get_wallet_by_id
from app.database import get_db

router = APIRouter()


# Route to create a wallet
@router.post("/users/{user_id}/wallet/", response_model=WalletResponse)
def create_wallet(user_id: int, db: Session = Depends(get_db)):
    return crud_create_wallet(db=db, user_id=user_id)


# Route to add an asset to a wallet
@router.put("/users/{user_id}/wallet/{wallet_id}/add_asset", response_model=AssetResponse)
def add_asset_to_wallet(
    user_id: int,
    wallet_id: int,
    asset_symbol: str,
    quantity: float,
    value_usd: float,
    db: Session = Depends(get_db)
):
    # Call the CRUD function to add or update asset
    asset = crud_add_asset_to_wallet(
        db=db,
        user_id=user_id,
        wallet_id=wallet_id,
        asset_symbol=asset_symbol,
        quantity=quantity,
        value_usd=value_usd
    )
    return asset


# Route to get wallet details (including assets)
@router.get("/{wallet_id}", response_model=WalletResponse)
def get_wallet(wallet_id: int, db: Session = Depends(get_db)):
    return crud_get_wallet_by_id(db=db, wallet_id=wallet_id)
