from sqlalchemy import desc, asc
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from datetime import datetime

from app.models import Wallet, User, Asset, PurchaseTransaction, SaleTransaction
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


def crud_get_wallet_by_id(
        db: Session,
        user_id: int,
        wallet_id: int,
        limit: int,
        page: int,
        sort_by: str,
        sort_order: str
):
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id, Wallet.user_id == user_id).first()

    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

    offset = (page - 1) * limit

    valid_sort_fields = [
        "coin_name",
        "quantity",
        "purchase_value_usd",
        "current_price_usd",
        "current_value_usd",
        "net_gain_loss",
        "initial_purchase_date",
    ]

    if sort_by not in valid_sort_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort field: {sort_by}. Must be one of {valid_sort_fields}"
        )

    assets = db.query(Asset).filter(Asset.wallet_id == wallet_id).all()

    if not assets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No Assets for Wallet... Try buying a coin"
        )

    enhanced_assets = []
    total_wallet_value = 0

    for asset in assets:
        current_price = get_current_coin_value(asset.coin_name)
        if current_price is None:
            continue

        current_value = round(asset.quantity * current_price, 4)
        net_gain_loss = round(current_value - asset.purchase_value_usd, 4)

        enhanced_assets.append({
            "id": asset.id,
            "coin_name": asset.coin_name,
            "quantity": asset.quantity,
            "purchase_value_usd": asset.purchase_value_usd,
            "current_price_usd": current_price,
            "current_value_usd": current_value,
            "net_gain_loss": net_gain_loss,
            "initial_purchase_date": asset.initial_purchase_date
        })

        total_wallet_value += current_value

    reverse_sort = sort_order == "desc"
    enhanced_assets.sort(key=lambda x: x[sort_by], reverse=reverse_sort)

    total_count = len(enhanced_assets)
    total_pages = (total_count + limit - 1) // limit
    paginated_assets = enhanced_assets[offset:offset + limit]

    return total_count, total_pages, total_wallet_value, paginated_assets


def crud_get_all_wallets(db: Session):
    return db.query(Wallet).all()


def crud_get_transactions_for_wallet(
    db: Session,
    user_id: int,
    wallet_id: int,
    limit: int,
    page: int
):
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id, Wallet.user_id == user_id).first()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

    offset = (page - 1) * limit

    purchase_transactions = db.query(
        PurchaseTransaction).filter(PurchaseTransaction.wallet_id == wallet_id).offset(offset).limit(limit).all()

    sale_transactions = db.query(
        SaleTransaction).filter(SaleTransaction.wallet_id == wallet_id).offset(offset).limit(limit).all()

    if not purchase_transactions and not sale_transactions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No Transactions for Wallet... Try buying a coin"
        )

    all_transactions = []

    for transaction in purchase_transactions:
        all_transactions.append({
            "id": transaction.id,
            "coin_name": transaction.coin_name,
            "quantity": transaction.quantity_purchased,
            "price_per_coin": transaction.purchase_price,
            "total_price": transaction.total_purchase_price,
            "transaction_date": transaction.purchase_date.strftime('%Y-%m-%d %H:%M:%S'),
            "type": "purchase"
        })

    for transaction in sale_transactions:
        all_transactions.append({
            "id": transaction.id,
            "coin_name": transaction.coin_name,
            "quantity": transaction.quantity_sold,
            "price_per_coin": transaction.sale_price,
            "total_price": transaction.sale_price * transaction.quantity_sold,
            "transaction_date": transaction.sale_date.strftime('%Y-%m-%d %H:%M:%S'),
            "type": "sale"
        })

    all_transactions = sorted(all_transactions, key=lambda x: x['transaction_date'], reverse=True)
    total_transactions = len(all_transactions)
    total_pages = (total_transactions + limit - 1) // limit

    return all_transactions, total_transactions, total_pages


def crud_purchase_asset(
        db: Session,
        user_id: int,
        wallet_id: int,
        coin_name: str,
        quantity: float
):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
        if not wallet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

        if wallet.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This wallet does not belong to the user")

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
            existing_asset.purchase_value_usd = round(existing_asset.quantity * current_coin_value, 4)

            purchase_transaction = PurchaseTransaction(
                user_id=user_id,
                wallet_id=wallet_id,
                asset_id=existing_asset.id,
                coin_name=coin_name,
                quantity_purchased=quantity,
                purchase_price=current_coin_value,
                total_purchase_price=calculated_value_of_coin_quantity,
                purchase_date=datetime.utcnow()
            )

            db.add(purchase_transaction)
            db.commit()
            db.refresh(existing_asset)
            db.refresh(purchase_transaction)

            return purchase_transaction

        new_asset = Asset(
            wallet_id=wallet_id,
            coin_name=coin_name,
            quantity=quantity,
            purchase_value_usd=calculated_value_of_coin_quantity
        )

        db.add(new_asset)
        db.commit()
        db.refresh(new_asset)

        purchase_transaction = PurchaseTransaction(
            user_id=user_id,
            wallet_id=wallet_id,
            asset_id=new_asset.id,
            coin_name=coin_name,
            quantity_purchased=quantity,
            purchase_price=current_coin_value,
            total_purchase_price=calculated_value_of_coin_quantity,
            purchase_date=datetime.utcnow()
        )

        db.add(purchase_transaction)
        db.commit()
        db.refresh(purchase_transaction)

        return purchase_transaction

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def crud_sell_asset(
        db: Session,
        wallet_id: int,
        user_id: int,
        coin_name: str,
        quantity: float
):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
        if not wallet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

        if wallet.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This wallet does not belong to the user")

        coin_name = coin_name.lower()

        current_coin_value = get_current_coin_value(coin_name)
        if current_coin_value is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch coin price")

        asset = db.query(Asset).filter(Asset.wallet_id == wallet_id, Asset.coin_name == coin_name).first()
        if not asset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{coin_name} asset not found in wallet")

        if asset.quantity < quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient quantity to sell")

        sale_price_usd = round(quantity * current_coin_value, 4)

        sale_transaction = SaleTransaction(
            user_id=user_id,
            wallet_id=wallet_id,
            asset_id=asset.id,
            coin_name=coin_name,
            quantity_sold=quantity,
            sale_price=current_coin_value,
            total_sale_price=sale_price_usd,
            sale_date=datetime.utcnow()
        )

        asset.quantity -= quantity
        if asset.quantity == 0:
            db.delete(asset)

        db.add(sale_transaction)
        db.commit()
        db.refresh(sale_transaction)

        return sale_transaction

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def crud_delete_wallet(db: Session, wallet_id: int, user_id: int):
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()

    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    if wallet.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This wallet does not belong to the user")

    db.query(Asset).filter(Asset.wallet_id == wallet_id).delete()

    db.delete(wallet)
    db.commit()

    return "Wallet and associated assets deleted successfully"
