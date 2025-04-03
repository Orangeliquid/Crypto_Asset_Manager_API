import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import literal
from unittest.mock import patch
from fastapi import HTTPException
from datetime import datetime, timedelta

from app.database import Base
from app.crud import wallets
from app.models import User, WalletActivityData, Wallet, Asset

# Set up a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_create_wallet(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=1)

    assert wallet is not None
    assert wallet.user_id == 1


def test_create_wallet_no_user(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_create_wallet(db, user_id=0)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


def test_get_wallet_by_id_wallet_id_invalid(db):
    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_get_wallet_by_id(
            db, user_id=1, wallet_id=1, limit=10, page=1, sort_by="coin_name", sort_order="asc"
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Wallet not found"


def test_get_wallet_by_id_invalid_sort_by(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=1)

    sort_by = "invalid_sort"
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

    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_get_wallet_by_id(
            db, user_id=1, wallet_id=wallet.id, limit=10, page=1, sort_by=sort_by, sort_order="asc"
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == f"Invalid sort field: {sort_by}. Must be one of {valid_sort_fields}"


def test_get_wallet_by_id_no_assets_in_wallet(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=1)

    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_get_wallet_by_id(
            db, user_id=1, wallet_id=wallet.id, limit=10, page=1, sort_by="coin_name", sort_order="asc"
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "No Assets for Wallet... Try buying a coin"


def test_get_wallet_by_id(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=1)

    wallets.crud_purchase_asset(
        db=db,
        user_id=wallet.user_id,
        wallet_id=wallet.id,
        coin_name="xrp",
        quantity=1
    )

    total_count, total_pages, total_wallet_value, paginated_assets = wallets.crud_get_wallet_by_id(
        db=db,
        user_id=wallet.user_id,
        wallet_id=wallet.id,
        limit=10,
        page=1,
        sort_by="coin_name",
        sort_order="asc"
    )

    assert total_count == 1
    assert total_pages == 1
    assert type(total_wallet_value) == float
    assert total_wallet_value >= 0
    assert len(paginated_assets) == 1


def test_get_all_wallets_no_wallets(db):
    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_get_all_wallets(db)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "No wallets found"


def test_get_all_wallets(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallets.crud_create_wallet(db, user_id=1)
    wallet = wallets.crud_get_all_wallets(db)

    # Ensure one wallet is created
    assert wallet is not None
    assert wallet[0].id == 1
    assert wallet[0].user_id == 1
    assert wallet[0].amount_of_coins == 0
    assert wallet[0].total_value_usd == 0
    assert isinstance(wallet[0].assets, list)
    assert len(wallet[0].assets) == 0
    assert wallet[0].assets == []


def test_get_all_purchase_transactions_for_wallet_no_wallet_created(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_get_all_transactions_for_wallet(
            db=db,
            user_id=user.id,
            wallet_id=1,
            limit=10,
            page=1
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Wallet not found"


def test_get_all_transactions_for_wallet_no_transactions(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=1)

    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_get_all_transactions_for_wallet(
            db=db,
            user_id=wallet.user_id,
            wallet_id=wallet.id,
            limit=10,
            page=1
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "No Transactions for Wallet... Try buying a coin"


def test_get_all_purchase_and_sale_transactions_for_wallet(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=1)

    wallets.crud_purchase_asset(
        db=db,
        user_id=wallet.user_id,
        wallet_id=wallet.id,
        coin_name="xrp",
        quantity=2
    )

    time.sleep(1)  # back to back calling CoinCapAPI sometimes triggers their rate limit... even though its 200 per min

    wallets.crud_sell_asset(
        db=db,
        user_id=wallet.user_id,
        wallet_id=wallet.id,
        coin_name="xrp",
        quantity=1
    )

    all_transactions, total_transactions, total_pages = wallets.crud_get_all_transactions_for_wallet(
        db=db,
        user_id=wallet.user_id,
        wallet_id=wallet.id,
        limit=10,
        page=1
    )

    assert all_transactions is not None
    assert len(all_transactions) == 2

    purchase_transaction_data = all_transactions[1]

    assert purchase_transaction_data["type"] == "purchase"
    assert purchase_transaction_data["id"] == 1  # only one purchase transaction - thus id == 1
    assert purchase_transaction_data["coin_name"] == "xrp"
    assert purchase_transaction_data["quantity"] == 2
    assert type(purchase_transaction_data["total_price"]) == float
    assert purchase_transaction_data["total_price"] >= 0
    assert type(purchase_transaction_data["transaction_date"]) == str

    sale_transaction_data = all_transactions[0]

    assert sale_transaction_data["type"] == "sale"
    assert sale_transaction_data["id"] == 1  # Only one sale transaction - thus id == 1
    assert sale_transaction_data["coin_name"] == "xrp"
    assert sale_transaction_data["quantity"] == 1
    assert type(sale_transaction_data["total_price"]) == float
    assert sale_transaction_data["total_price"] >= 0
    assert type(sale_transaction_data["transaction_date"]) == str

    assert total_transactions == 2
    assert total_pages == 1


def test_get_wallet_valuation_current_date(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=1)

    wallets.crud_purchase_asset(
        db=db,
        user_id=wallet.user_id,
        wallet_id=wallet.id,
        coin_name="xrp",
        quantity=2
    )

    current_date = datetime.utcnow().strftime("%Y-%m-%d")

    valuation = wallets.crud_get_wallet_valuation(
        db=db,
        user_id=wallet.user_id,
        wallet_id=wallet.id,
        historical_date=current_date
    )

    assert valuation["wallet_id"] == wallet.id
    assert type(valuation["snap_shot_date"]) == str
    assert valuation["snap_shot_date_relative_to_historic_date"] == "current"
    assert next(iter(valuation["holdings"])) == "xrp"
    assert valuation["holdings"]["xrp"]["quantity"] == 2
    assert type(valuation["holdings"]["xrp"]["purchase_value_usd"]) == float
    assert valuation["holdings"]["xrp"]["purchase_value_usd"] > 0
    assert type(valuation["holdings"]["xrp"]["value_on_date_usd"]) == float
    assert valuation["holdings"]["xrp"]["value_on_date_usd"] > 0
    assert valuation["total_value_usd_on_snapshot_date"] > 0
    assert type(valuation["total_value_usd_on_snapshot_date"]) == float
    assert valuation["date_requested_total_value"] > 0
    assert type(valuation["date_requested_total_value"]) == float
    assert valuation["total_value_usd_on_snapshot_date"] == valuation["date_requested_total_value"]
    assert valuation["net_gain_loss"] == 0


def test_get_wallet_valuation_past_date(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=1)

    wallets.crud_purchase_asset(
        db=db,
        user_id=wallet.user_id,
        wallet_id=wallet.id,
        coin_name="xrp",
        quantity=2
    )

    historical_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    valuation = wallets.crud_get_wallet_valuation(
        db=db,
        user_id=wallet.user_id,
        wallet_id=wallet.id,
        historical_date=historical_date
    )

    assert valuation["wallet_id"] == wallet.id
    assert type(valuation["snap_shot_date"]) == str
    assert valuation["snap_shot_date_relative_to_historic_date"] == "future"
    assert next(iter(valuation["holdings"])) == "xrp"
    assert valuation["holdings"]["xrp"]["quantity"] == 2
    assert type(valuation["holdings"]["xrp"]["purchase_value_usd"]) == float
    assert valuation["holdings"]["xrp"]["purchase_value_usd"] > 0
    assert type(valuation["holdings"]["xrp"]["value_on_date_usd"]) == float
    assert valuation["holdings"]["xrp"]["value_on_date_usd"] > 0
    assert valuation["total_value_usd_on_snapshot_date"] > 0
    assert type(valuation["total_value_usd_on_snapshot_date"]) == float
    assert valuation["date_requested_total_value"] > 0
    assert type(valuation["date_requested_total_value"]) == float
    assert valuation["total_value_usd_on_snapshot_date"] == valuation["date_requested_total_value"]
    assert valuation["net_gain_loss"] == 0


def test_get_wallet_valuation_future_date(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=user.id)

    fake_snapshot_date = datetime.utcnow() - timedelta(days=1)

    fake_snapshot = WalletActivityData(
        wallet_id=wallet.id,
        date=fake_snapshot_date,
        holdings={"xrp": {"quantity": 1, "purchase_value_usd": 2.50, "value_on_date_usd": 2.50}},
        total_value_usd=2.50
    )

    db.add(fake_snapshot)
    db.commit()

    current_date = datetime.utcnow().strftime("%Y-%m-%d")

    valuation = wallets.crud_get_wallet_valuation(
        db=db,
        user_id=wallet.user_id,
        wallet_id=wallet.id,
        historical_date=current_date
    )

    assert valuation["wallet_id"] == wallet.id
    assert type(valuation["snap_shot_date"]) == str
    assert valuation["snap_shot_date_relative_to_historic_date"] == "past"
    assert next(iter(valuation["holdings"])) == "xrp"
    assert valuation["holdings"]["xrp"]["quantity"] == 1
    assert type(valuation["holdings"]["xrp"]["purchase_value_usd"]) == float
    assert valuation["holdings"]["xrp"]["purchase_value_usd"] > 0
    assert type(valuation["holdings"]["xrp"]["value_on_date_usd"]) == float
    assert valuation["holdings"]["xrp"]["value_on_date_usd"] > 0
    assert valuation["total_value_usd_on_snapshot_date"] > 0
    assert type(valuation["total_value_usd_on_snapshot_date"]) == float
    assert valuation["date_requested_total_value"] > 0
    assert type(valuation["date_requested_total_value"]) == float


def test_get_wallet_valuation_no_user(db):
    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_get_wallet_valuation(
            db=db,
            user_id=1,
            wallet_id=1,
            historical_date="2025-03-15"
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


def test_get_wallet_valuation_no_wallet(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_get_wallet_valuation(
            db=db,
            user_id=user.id,
            wallet_id=1,
            historical_date="2025-03-15"
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Wallet not found"


def test_get_wallet_valuation_wallet_does_not_belong_to_user(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=user.id)

    user_2 = User(id=2, username="testuser2", email="test2@example.com")
    db.add(user_2)
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_get_wallet_valuation(
            db=db,
            user_id=user_2.id,
            wallet_id=wallet.id,
            historical_date="2025-03-15"
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "This wallet does not belong to the user"


def test_get_wallet_valuation_wallet_invalid_historical_date_format(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=user.id)

    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_get_wallet_valuation(
            db=db,
            user_id=wallet.user_id,
            wallet_id=wallet.id,
            historical_date="03-15-2025"
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid date format. Expected format: YYYY-MM-DD"


def test_get_wallet_valuation_no_activity_data(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=user.id)

    current_date = datetime.utcnow().strftime("%Y-%m-%d")

    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_get_wallet_valuation(
            db=db,
            user_id=wallet.user_id,
            wallet_id=wallet.id,
            historical_date=current_date
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "No wallet activity data found for the given date or nearby dates"


def test_get_wallet_valuation_integrity_error(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=1)

    with patch("sqlalchemy.orm.Session.query", side_effect=SQLAlchemyError("Mock DB error")):
        with pytest.raises(HTTPException) as exc_info:
            wallets.crud_get_wallet_valuation(
                db=db,
                user_id=wallet.user_id,
                wallet_id=wallet.id,
                historical_date="2025-03-29"
            )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Database error: Mock DB error"


def test_purchase_asset_no_user(db):
    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_purchase_asset(
            db=db,
            user_id=1,
            wallet_id=1,
            coin_name="xrp",
            quantity=2
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


def test_purchase_asset_no_wallet(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_purchase_asset(
            db=db,
            user_id=user.id,
            wallet_id=1,
            coin_name="xrp",
            quantity=2
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Wallet not found"


def test_purchase_asset_wallet_does_not_belong_to_user(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallets.crud_create_wallet(db, user_id=user.id)

    user_2 = User(id=2, username="testuser2", email="test2@example.com")
    db.add(user_2)
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_purchase_asset(
            db=db,
            user_id=user_2.id,
            wallet_id=1,
            coin_name="xrp",
            quantity=2
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "This wallet does not belong to the user"


def test_purchase_asset_coin_name_not_in_coin_names(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=user.id)
    invalid_coin_name = "xrg"
    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_purchase_asset(
            db=db,
            user_id=wallet.user_id,
            wallet_id=wallet.id,
            coin_name=invalid_coin_name,
            quantity=2
        )

    assert exc_info.value.status_code == 400
    assert (exc_info.value.detail ==
            f"Invalid coin name '{invalid_coin_name}' - (e.g., 'bitcoin', 'ethereum', 'melania-meme')")


def test_purchase_asset_fails_when_coin_data_fetch_fails(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=user.id)

    with patch("app.crud.wallets.get_current_coin_data", return_value=None):
        with pytest.raises(HTTPException) as exc_info:
            wallets.crud_purchase_asset(
                db=db,
                user_id=wallet.user_id,
                wallet_id=wallet.id,
                coin_name="xrp",
                quantity=2
            )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to fetch coin data"


def test_purchase_asset_fails_when_coin_value_is_zero(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=user.id)

    # Patch the get_current_coin_data function to return a coin with a price of 0
    with patch("app.crud.wallets.get_current_coin_data", return_value={"priceUsd": 0}):
        with pytest.raises(HTTPException) as exc_info:
            wallets.crud_purchase_asset(
                db=db,
                user_id=user.id,
                wallet_id=wallet.id,
                coin_name="xrp",
                quantity=2
            )

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "xrp is valued at 0"


def test_purchase_asset_existing_asset(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=user.id)

    wallets.crud_purchase_asset(
        db=db,
        user_id=user.id,
        wallet_id=wallet.id,
        coin_name="xrp",
        quantity=1
    )

    second_purchase = wallets.crud_purchase_asset(
        db=db,
        user_id=user.id,
        wallet_id=wallet.id,
        coin_name="xrp",
        quantity=1
    )

    assert second_purchase.updated_coin_quantity == 2
    assert second_purchase.coin_name == "xrp"


def test_purchase_asset_integrity_error(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=1)

    with patch("sqlalchemy.orm.Session.query", side_effect=SQLAlchemyError("Mock DB error")):
        with pytest.raises(HTTPException) as exc_info:
            wallets.crud_purchase_asset(
                db=db,
                user_id=user.id,
                wallet_id=wallet.id,
                coin_name="xrp",
                quantity=1
            )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Database error: Mock DB error"


def test_sell_asset(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=user.id)

    wallets.crud_purchase_asset(
        db=db,
        user_id=user.id,
        wallet_id=wallet.id,
        coin_name="xrp",
        quantity=1
    )

    sold_asset = wallets.crud_sell_asset(
        db=db,
        user_id=user.id,
        wallet_id=wallet.id,
        coin_name="xrp",
        quantity=0.5
    )

    assert sold_asset.remaining_coin_quantity == 0.5
    assert sold_asset.coin_name == "xrp"
    assert sold_asset.quantity_sold == 0.5


def test_sell_asset_all_of_asset(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=user.id)

    wallets.crud_purchase_asset(
        db=db,
        user_id=user.id,
        wallet_id=wallet.id,
        coin_name="xrp",
        quantity=1
    )

    sold_asset = wallets.crud_sell_asset(
        db=db,
        user_id=user.id,
        wallet_id=wallet.id,
        coin_name="xrp",
        quantity=1
    )

    assert sold_asset.remaining_coin_quantity == 0.0
    assert sold_asset.coin_name == "xrp"
    assert sold_asset.quantity_sold == 1


def test_sell_asset_no_user(db):
    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_sell_asset(
            db=db,
            user_id=1,
            wallet_id=1,
            coin_name="xrp",
            quantity=0.5
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


def test_sell_asset_no_wallet_for_user(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_sell_asset(
            db=db,
            user_id=user.id,
            wallet_id=1,
            coin_name="xrp",
            quantity=0.5
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Wallet not found"


def test_sell_asset_user_does_not_own_wallet(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=user.id)

    user2 = User(id=2, username="testuser2", email="test2@example.com")

    db.add(user2)
    db.commit()

    wallets.crud_create_wallet(db, user_id=user2.id)

    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_sell_asset(
            db=db,
            user_id=wallet.user_id,
            wallet_id=2,
            coin_name="xrp",
            quantity=0.5
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "This wallet does not belong to the user"


def test_sell_asset_coin_not_in_wallet(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=user.id)

    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_sell_asset(
            db=db,
            user_id=wallet.user_id,
            wallet_id=wallet.id,
            coin_name="xrg",
            quantity=0.5
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "xrg asset not found in wallet"


def test_sell_asset_requested_sell_amount_more_than_holding(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=user.id)

    wallets.crud_purchase_asset(
        db=db,
        user_id=user.id,
        wallet_id=wallet.id,
        coin_name="xrp",
        quantity=1
    )

    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_sell_asset(
            db=db,
            user_id=wallet.user_id,
            wallet_id=wallet.id,
            coin_name="xrp",
            quantity=1.5
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Insufficient quantity to sell"


def test_sell_asset_current_coin_data_is_none(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=user.id)

    wallets.crud_purchase_asset(
        db=db,
        user_id=user.id,
        wallet_id=wallet.id,
        coin_name="xrp",
        quantity=1
    )

    with patch("app.crud.wallets.get_current_coin_data", return_value=None):
        with pytest.raises(HTTPException) as exc_info:
            wallets.crud_sell_asset(
                db=db,
                user_id=wallet.user_id,
                wallet_id=wallet.id,
                coin_name="xrp",
                quantity=0.5
            )

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Failed to fetch coin data"


def test_sell_asset_fails_when_coin_value_is_zero(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=user.id)

    wallets.crud_purchase_asset(
        db=db,
        user_id=user.id,
        wallet_id=wallet.id,
        coin_name="xrp",
        quantity=2
    )

    # Patch the get_current_coin_data function to return a coin with a price of 0
    with patch("app.crud.wallets.get_current_coin_data", return_value={"priceUsd": 0}):
        with pytest.raises(HTTPException) as exc_info:
            wallets.crud_sell_asset(
                db=db,
                user_id=user.id,
                wallet_id=wallet.id,
                coin_name="xrp",
                quantity=2
            )

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "xrp is valued at 0"


def test_sell_asset_integrity_error(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=1)

    wallets.crud_purchase_asset(
        db=db,
        user_id=user.id,
        wallet_id=wallet.id,
        coin_name="xrp",
        quantity=2
    )

    with patch("sqlalchemy.orm.Session.query", side_effect=SQLAlchemyError("Mock DB error")):
        with pytest.raises(HTTPException) as exc_info:
            wallets.crud_sell_asset(
                db=db,
                user_id=user.id,
                wallet_id=wallet.id,
                coin_name="xrp",
                quantity=1
            )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Database error: Mock DB error"


def test_delete_wallet(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=1)

    delete_wallet = wallets.crud_delete_wallet(
        db=db,
        user_id=wallet.user_id,
        wallet_id=wallet.id
    )

    assert delete_wallet == "Wallet and associated assets deleted successfully"


def test_delete_nonexistent_wallet(db):
    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_delete_wallet(db=db, user_id=1, wallet_id=999)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Wallet not found"


def test_delete_wallet_wrong_user(db):
    user1 = User(id=1, username="testuser1", email="test1@example.com")
    user2 = User(id=2, username="testuser2", email="test2@example.com")
    db.add_all([user1, user2])
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=user1.id)

    with pytest.raises(HTTPException) as exc_info:
        wallets.crud_delete_wallet(db=db, user_id=user2.id, wallet_id=wallet.id)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "This wallet does not belong to the user"


def test_wallet_deletion_removes_assets(db):
    user = User(id=1, username="testuser", email="test@example.com")
    db.add(user)
    db.commit()

    wallet = wallets.crud_create_wallet(db, user_id=user.id)

    wallets.crud_purchase_asset(
        db=db,
        user_id=user.id,
        wallet_id=wallet.id,
        coin_name="xrp",
        quantity=2
    )

    wallets.crud_delete_wallet(db=db, user_id=user.id, wallet_id=wallet.id)

    wallet_id = wallet.id

    assert db.query(Wallet).filter(Wallet.id == literal(wallet_id)).first() is None
    assert db.query(Asset).filter(Asset.wallet_id == literal(wallet_id)).count() == 0
