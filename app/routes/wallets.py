from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.wallets import WalletBase, WalletResponse, WalletDeleteResponse
from app.schemas.assets import AssetResponse
from app.crud.wallets import crud_create_wallet, crud_add_asset_to_wallet, crud_get_wallet_by_id, crud_delete_wallet
from app.crud.wallets import crud_get_all_wallets
from app.database import get_db

router = APIRouter()


# Route to create a wallet
@router.post("/users/{user_id}/wallet/", response_model=WalletBase)
def create_wallet(user_id: int, db: Session = Depends(get_db)):
    return crud_create_wallet(db=db, user_id=user_id)


# Route to get wallet details (including assets)
@router.get("/users/{user_id}/wallet/{wallet_id}/", response_model=WalletResponse)
def fetch_wallet(user_id: int, wallet_id: int, db: Session = Depends(get_db)):
    return crud_get_wallet_by_id(db=db, user_id=user_id, wallet_id=wallet_id)


@router.get("/wallets/", response_model=List[WalletResponse])
def fetch_all_wallets(db: Session = Depends(get_db)):
    wallets = crud_get_all_wallets(db)

    if not wallets:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No wallets found")

    return wallets


# Route to add an asset to a wallet
@router.put("/users/{user_id}/wallet/{wallet_id}/add_asset", response_model=AssetResponse)
def add_asset_to_wallet(
    user_id: int,
    wallet_id: int,
    coin_name: str,
    quantity: float,
    db: Session = Depends(get_db)
):
    return crud_add_asset_to_wallet(
        db=db,
        user_id=user_id,
        wallet_id=wallet_id,
        coin_name=coin_name,
        quantity=quantity,
    )


@router.delete("/users/{user_id}/wallet/{wallet_id}/", response_model=WalletDeleteResponse)
def delete_wallet(user_id: int, wallet_id: int, db: Session = Depends(get_db)):
    delete_message = crud_delete_wallet(db=db, wallet_id=wallet_id, user_id=user_id)
    return {"message": delete_message}
