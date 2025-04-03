from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, asc, func
from fastapi import HTTPException, status
from datetime import datetime
import time

from app.models import Wallet, User, Asset, PurchaseTransaction, SaleTransaction, WalletActivityData
from app.CoinCapAPI import valid_coin_names, get_current_coin_data, fetch_dated_coin_price


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
        "coin_cap_rank",
        "coin_cap_symbol",
        "market_cap_usd",
        "volume_usd_24hr",
        "change_percent_24hr",
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

        print(asset.id)

        coin_data = get_current_coin_data(asset.coin_name)

        if coin_data is None:
            print(f"missing {asset.coin_name}")
            continue
        print(coin_data)

        current_value = round(asset.quantity * float(coin_data.get("priceUsd", 0)), 4)
        net_gain_loss = round(current_value - asset.purchase_value_usd, 4)

        enhanced_assets.append({
            "id": asset.id,
            "coin_name": asset.coin_name,
            "quantity": asset.quantity,
            "purchase_value_usd": asset.purchase_value_usd,  # Summation of purchase price of asset
            "current_price_usd": coin_data.get("priceUsd", 0),  # Price for one coin on current date
            "current_value_usd": current_value,
            "net_gain_loss": net_gain_loss,
            "initial_purchase_date": asset.initial_purchase_date,
            "coin_cap_id": coin_data.get("id", ""),
            "coin_cap_rank": int(coin_data.get("rank", 0)),
            "coin_cap_symbol": coin_data.get("symbol", ""),
            "supply": float(coin_data.get("supply", 0)),
            "max_supply": coin_data.get("maxSupply", 0.0),
            "market_cap_usd": float(coin_data.get("marketCapUsd", 0)),
            "volume_usd_24hr": float(coin_data.get("volumeUsd24Hr", 0)),
            "change_percent_24hr": float(coin_data.get("changePercent24Hr", 0)),
            "vwap_24hr": coin_data.get("vwap24Hr", 0.0),
            "explorer_url": coin_data.get("explorer", "Missing URL from CoinCapAPI")
        })

        total_wallet_value += current_value
        time.sleep(0.5)

    reverse_sort = sort_order == "desc"
    enhanced_assets.sort(key=lambda x: x[sort_by], reverse=reverse_sort)

    total_count = len(enhanced_assets)
    total_pages = (total_count + limit - 1) // limit
    paginated_assets = enhanced_assets[offset:offset + limit]

    return total_count, total_pages, total_wallet_value, paginated_assets


def create_wallet_activity_snapshot(db: Session, user_id: int, wallet_id: int):
    total_count, total_pages, total_wallet_value, enhanced_assets = crud_get_wallet_by_id(
        db=db,
        user_id=user_id,
        wallet_id=wallet_id,
        limit=1000,
        page=1,
        sort_by="coin_name",
        sort_order="asc"
    )

    holdings = {}
    for asset in enhanced_assets:
        holdings[asset["coin_name"]] = {
            "quantity": asset["quantity"],
            "purchase_value_usd": asset["purchase_value_usd"],  # Summation of asset total purchase cost
            "value_on_date_usd": asset["current_value_usd"]  # Valuation of asset quantity on date of snapshot
        }

    snapshot = WalletActivityData(
        wallet_id=wallet_id,
        date=datetime.utcnow(),
        holdings=holdings,
        total_value_usd=total_wallet_value
    )

    db.add(snapshot)
    db.commit()


def crud_get_all_wallets(db: Session):
    wallets = db.query(Wallet).all()

    if not wallets:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No wallets found")

    return wallets


def crud_get_all_transactions_for_wallet(
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


def crud_get_wallet_valuation(db: Session, user_id: int, wallet_id: int, historical_date: str):

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
        if not wallet:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

        if wallet.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This wallet does not belong to the user"
            )

        try:
            historical_date_dt = datetime.strptime(historical_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Expected format: YYYY-MM-DD"
            )

        snap_shot_date_relative_to_historic_date = ""
        date_requested_total_value = 0

        # Step 1: Try to find the latest snapshot from the exact date
        activity = (
            db.query(WalletActivityData)
            .filter(
                WalletActivityData.wallet_id == wallet_id,
                func.date(WalletActivityData.date) == historical_date_dt  # Ensure exact date match
            )
            .order_by(desc(WalletActivityData.date))  # Get the most recent snapshot from that day
            .first()
        )

        if activity:
            print("found exact date requested")
            snap_shot_date_relative_to_historic_date = "current"
            date_requested_total_value = activity.total_value_usd

        # Step 2: If no exact match, find the closest past snapshot
        if not activity:
            print("No exact match, checking closest past snapshot")
            activity = (
                db.query(WalletActivityData)
                .filter(
                    WalletActivityData.wallet_id == wallet_id,
                    WalletActivityData.date < historical_date_dt  # Any date before the requested date
                )
                .order_by(desc(WalletActivityData.date))  # Get the most recent past snapshot
                .first()
            )

            if activity:
                print("Found past snapshot")
                snap_shot_date_relative_to_historic_date = "past"

                """
                If snap shot is from the past then the user is requesting the value of assets from a future date.
                Now we query CoinCapAPI for the price of each asset on the date requested and add this value to the data
                for each of the coins within holding. These added up are used for date_requested_total_value
                """

                date_in_seconds = int(time.mktime(time.strptime(historical_date, "%Y-%m-%d")))

                for coin in activity.holdings:
                    data = fetch_dated_coin_price(
                        coin_name=coin,
                        start_timestamp=date_in_seconds,
                        end_timestamp=date_in_seconds
                    )
                    data_price_per_coin = data[-1]["priceUsd"]
                    asset_quantity = activity.holdings[coin]["quantity"]
                    value_on_date_requested = float(data_price_per_coin) * asset_quantity
                    date_requested_total_value += value_on_date_requested
                    activity.holdings[coin]["value_on_date_requested"] = date_requested_total_value

        # Step 3: If no past snapshot exists, get the closest future snapshot
        if not activity:
            print("No exact match, checking closest future snapshot")

            # Step 1: Find the nearest future date with activity
            nearest_future_date = (
                db.query(func.date(WalletActivityData.date))  # Extract only the date
                .filter(
                    WalletActivityData.wallet_id == wallet_id,
                    WalletActivityData.date > historical_date_dt  # Any date after the requested date
                )
                .order_by(asc(WalletActivityData.date))  # Get the nearest future date
                .limit(1)
                .scalar()  # Fetch the single value (earliest future date)
            )

            # Step 2: If we found nearest future date, get the last snapshot of that date
            if nearest_future_date:
                nearest_future_date = str(nearest_future_date)
                activity = (
                    db.query(WalletActivityData)
                    .filter(
                        WalletActivityData.wallet_id == wallet_id,
                        func.date(WalletActivityData.date) == nearest_future_date
                    )
                    .order_by(desc(WalletActivityData.date))
                    .first()
                )
                if activity:
                    print("Found future snapshot")
                    snap_shot_date_relative_to_historic_date = "future"
                    date_requested_total_value = activity.total_value_usd

        # If no activity data found at all, raise an error
        if not activity:
            print("No nearest match - raising error")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No wallet activity data found for the given date or nearby dates"
            )

        return {
            "wallet_id": activity.wallet_id,
            "snap_shot_date": activity.date.strftime("%Y-%m-%d %H:%M:%S"),
            "snap_shot_date_relative_to_historic_date": snap_shot_date_relative_to_historic_date,
            "holdings": activity.holdings,
            "total_value_usd_on_snapshot_date": activity.total_value_usd,
            "date_requested_total_value": date_requested_total_value,
            "net_gain_loss": date_requested_total_value - activity.total_value_usd
        }

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error: " + str(e)
        )


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

        current_coin_data = get_current_coin_data(coin_name)
        if current_coin_data is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch coin data")

        current_coin_value = float(current_coin_data.get("priceUsd", 0))
        if current_coin_value == 0:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{coin_name} is valued at 0")

        calculated_value_of_coin_quantity = round(quantity * current_coin_value, 4)

        existing_asset = db.query(Asset).filter(
            Asset.wallet_id == wallet_id, Asset.coin_name == coin_name).first()

        if existing_asset:
            updated_coin_quantity = existing_asset.quantity + quantity
            existing_asset.quantity += quantity
            existing_asset.purchase_value_usd += calculated_value_of_coin_quantity

            purchase_transaction = PurchaseTransaction(
                user_id=user_id,
                wallet_id=wallet_id,
                asset_id=existing_asset.id,
                coin_name=coin_name,
                quantity_purchased=quantity,
                purchase_price=current_coin_value,
                total_purchase_price=calculated_value_of_coin_quantity,
                updated_coin_quantity=updated_coin_quantity,
                purchase_date=datetime.utcnow()
            )

            db.add(purchase_transaction)
            db.commit()
            db.refresh(existing_asset)
            db.refresh(purchase_transaction)

            create_wallet_activity_snapshot(db=db, user_id=user_id, wallet_id=wallet_id)
            print("Snapshot created for purchase")

            return purchase_transaction

        else:
            new_asset = Asset(
                wallet_id=wallet_id,
                coin_name=coin_name,
                quantity=quantity,
                purchase_value_usd=calculated_value_of_coin_quantity
            )
            db.add(new_asset)
            db.flush()

            purchase_transaction = PurchaseTransaction(
                user_id=user_id,
                wallet_id=wallet_id,
                asset_id=new_asset.id,
                coin_name=coin_name,
                quantity_purchased=quantity,
                purchase_price=current_coin_value,
                total_purchase_price=calculated_value_of_coin_quantity,
                updated_coin_quantity=quantity,
                purchase_date=datetime.utcnow()
            )

            db.add(purchase_transaction)
            db.commit()
            db.refresh(new_asset)
            db.refresh(purchase_transaction)

            create_wallet_activity_snapshot(db=db, user_id=user_id, wallet_id=wallet_id)
            print("Snapshot created for purchase")

            return purchase_transaction

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error: " + str(e))


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

        asset = db.query(Asset).filter(Asset.wallet_id == wallet_id, Asset.coin_name == coin_name).first()
        if not asset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{coin_name} asset not found in wallet")

        if asset.quantity < quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient quantity to sell")

        current_coin_data = get_current_coin_data(coin_name)
        if current_coin_data is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch coin data")

        current_coin_value = float(current_coin_data.get("priceUsd", 0))
        if current_coin_value == 0:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{coin_name} is valued at 0")

        sale_price_usd = round(quantity * current_coin_value, 4)
        coins_remaining_after_sale = asset.quantity - quantity

        sale_transaction = SaleTransaction(
            user_id=user_id,
            wallet_id=wallet_id,
            asset_id=asset.id,
            coin_name=coin_name,
            quantity_sold=quantity,
            sale_price=current_coin_value,
            total_sale_price=sale_price_usd,
            remaining_coin_quantity=coins_remaining_after_sale,
            sale_date=datetime.utcnow()
        )

        db.add(sale_transaction)

        asset.quantity = coins_remaining_after_sale

        db.commit()
        db.refresh(sale_transaction)

        create_wallet_activity_snapshot(db=db, user_id=user_id, wallet_id=wallet_id)
        print("Snapshot created for sale")

        if asset.quantity == 0:
            db.delete(asset)
            db.commit()

        return sale_transaction

    except SQLAlchemyError as e:
        db.rollback()
        print(f"Database error during sale: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error: " + str(e))


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
