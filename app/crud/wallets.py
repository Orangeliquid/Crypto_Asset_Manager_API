from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import Wallet, User, Asset
from app.schemas.wallets import WalletResponse
from app.schemas.assets import AssetResponse
from app.utils.security import verify_password
from app.CoinCapAPI import valid_coin_symbols


def crud_create_wallet(db: Session, user_id: int) -> WalletResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    wallet = Wallet(user_id=user_id)
    db.add(wallet)
    db.commit()
    db.refresh(wallet)

    return WalletResponse(
        id=wallet.id,
        user_id=wallet.user_id,
        asset_symbol=None,
        quantity=0.0,
        value_usd=0.0
    )


def crud_add_asset_to_wallet(
        db: Session, user_id: int, wallet_id: int, asset_symbol: str, quantity: float, value_usd: float
):

    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

    if wallet.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This wallet does not belong to the user")

    valid_symbols = valid_coin_symbols()
    if asset_symbol not in valid_symbols:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid asset symbol"
        )

    existing_asset = db.query(Asset).filter(
        Asset.wallet_id == wallet_id, Asset.asset_symbol == asset_symbol
    ).first()

    if existing_asset:
        existing_asset.quantity += quantity
        existing_asset.value_usd = value_usd
        db.commit()
        db.refresh(existing_asset)
        return existing_asset

    new_asset = Asset(wallet_id=wallet_id, asset_symbol=asset_symbol, quantity=quantity, value_usd=value_usd)
    db.add(new_asset)
    db.commit()
    db.refresh(new_asset)

    return new_asset


def crud_get_wallet_by_id(db: Session, wallet_id: int) -> WalletResponse:
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()

    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

    assets = db.query(Asset).filter(Asset.wallet_id == wallet_id).all()

    return WalletResponse(
        id=wallet.id,
        user_id=wallet.user_id,
        assets=[
            AssetResponse(
                id=asset.id,
                asset_symbol=asset.asset_symbol,
                quantity=asset.quantity,
                value_usd=asset.value_usd
            )
            for asset in assets
        ]
    )

