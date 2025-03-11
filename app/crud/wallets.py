from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import Wallet, User, Asset
from app.CoinCapAPI import valid_coin_names, get_current_coin_value


def crud_create_wallet(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    wallet = Wallet(user_id=user_id)
    db.add(wallet)
    db.commit()
    db.refresh(wallet)

    return wallet


def crud_get_wallet_by_id(db: Session, user_id: int, wallet_id: int):
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id, Wallet.user_id == user_id).first()

    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

    assets = db.query(Asset).filter(Asset.wallet_id == wallet_id).all()

    wallet.assets = assets

    return wallet


def crud_get_all_wallets(db: Session):
    return db.query(Wallet).all()


def crud_add_asset_to_wallet(
        db: Session,
        user_id: int,
        wallet_id: int,
        coin_name: str,
        quantity: float
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

    if wallet.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This wallet does not belong to the user")

    # Ensure coin_name is lowercase to standardize input and correctly query CoinCapAPI
    coin_name = coin_name.lower()

    coin_names = valid_coin_names()
    if coin_name not in coin_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid coin name '{coin_name}' - (e.g., 'bitcoin', 'ethereum', 'melania-meme')"
        )

    current_coin_value = get_current_coin_value(coin_name)
    if current_coin_value is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch coin price")

    calculated_value_of_coin_quantity = round(quantity * current_coin_value, 4)

    existing_asset = db.query(Asset).filter(
        Asset.wallet_id == wallet_id, Asset.coin_name == coin_name).first()

    if existing_asset:
        existing_asset.quantity += quantity
        existing_asset.value_usd = round(existing_asset.quantity * current_coin_value, 4)
        db.commit()
        db.refresh(existing_asset)
        return existing_asset

    new_asset = Asset(
        wallet_id=wallet_id,
        coin_name=coin_name,
        quantity=quantity,
        value_usd=calculated_value_of_coin_quantity
    )
    db.add(new_asset)
    db.commit()
    db.refresh(new_asset)

    return new_asset


def crud_delete_wallet(db: Session, wallet_id: int, user_id: int):
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()

    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    if wallet.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This wallet does not belong to the user")

    # Delete all assets associated with the wallet
    db.query(Asset).filter(Asset.wallet_id == wallet_id).delete()

    # Delete the wallet itself
    db.delete(wallet)
    db.commit()

    return "Wallet and associated assets deleted successfully"
