from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.schemas.wallets import WalletBase, WalletResponse, WalletDeleteResponse, WalletValuationResponse
from app.schemas.transactions import PurchaseTransactionResponse, SaleTransactionResponse, PaginatedTransactionsResponse
from app.schemas.assets import PaginatedAssetsResponse
from app.crud.wallets import crud_create_wallet, crud_purchase_asset, crud_sell_asset
from app.crud.wallets import crud_get_wallet_by_id, crud_get_all_transactions_for_wallet, crud_delete_wallet
from app.crud.wallets import crud_get_all_wallets, crud_get_wallet_valuation
from app.database import get_db

router = APIRouter()


# Route to create a wallet
@router.post("/users/{user_id}/wallet/", response_model=WalletBase)
def create_wallet(user_id: int, db: Session = Depends(get_db)):
    return crud_create_wallet(db=db, user_id=user_id)


# Route to get wallet details (including assets)
@router.get("/users/{user_id}/wallet/{wallet_id}/", response_model=PaginatedAssetsResponse)
def fetch_wallet(
        user_id: int,
        wallet_id: int,
        limit: int = Query(10, ge=1),
        page: int = Query(1, ge=1),
        sort_by: str = "coin_name",
        sort_order: str = "asc",
        db: Session = Depends(get_db)
):
    total_count, total_pages, total_wallet_value, assets = crud_get_wallet_by_id(
        db=db,
        user_id=user_id,
        wallet_id=wallet_id,
        limit=limit,
        page=page,
        sort_by=sort_by,
        sort_order=sort_order
    )

    return PaginatedAssetsResponse(
        total_count=total_count,
        total_pages=total_pages,
        current_page=page,
        total_wallet_value_usd=total_wallet_value,
        assets=assets
    )


@router.get("/wallets/", response_model=List[WalletResponse])
def fetch_all_wallets(db: Session = Depends(get_db)):
    return crud_get_all_wallets(db)


@router.get("/users/{user_id}/wallet/{wallet_id}/all-transactions", response_model=PaginatedTransactionsResponse)
def get_all_transactions_for_wallet(
        user_id: int,
        wallet_id: int,
        limit: int = Query(10, ge=1),
        page: int = Query(1, ge=1),
        db: Session = Depends(get_db)
):
    transactions, total_transactions, total_pages = crud_get_all_transactions_for_wallet(
        db=db,
        user_id=user_id,
        wallet_id=wallet_id,
        limit=limit,
        page=page
    )

    return PaginatedTransactionsResponse(
        transactions=transactions,
        total_transactions=total_transactions,
        total_pages=total_pages,
        current_page=page
    )


@router.get("/users/{user_id}/wallet/{wallet_id}/valuation-by-date", response_model=WalletValuationResponse)
def get_wallet_valuation(
    user_id: int,
    wallet_id: int,
    historical_date: str = "2025-03-25",
    db: Session = Depends(get_db)
):

    return crud_get_wallet_valuation(db, user_id, wallet_id, historical_date)


@router.put("/users/{user_id}/wallet/{wallet_id}/purchase_asset", response_model=PurchaseTransactionResponse)
def purchase_asset(
    user_id: int,
    wallet_id: int,
    coin_name: str,
    quantity: float,
    db: Session = Depends(get_db)
):
    return crud_purchase_asset(
        db=db,
        user_id=user_id,
        wallet_id=wallet_id,
        coin_name=coin_name,
        quantity=quantity,
    )


@router.put("/users/{user_id}/wallet/{wallet_id}/sell_asset", response_model=SaleTransactionResponse)
def sell_asset(
    user_id: int,
    wallet_id: int,
    coin_name: str,
    quantity: float,
    db: Session = Depends(get_db)
):
    return crud_sell_asset(
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
