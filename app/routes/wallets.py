from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.schemas.wallets import WalletBase, WalletResponse, WalletDeleteResponse
from app.schemas.transactions import PurchaseTransactionResponse, SaleTransactionResponse, PaginatedTransactionsResponse
from app.schemas.transactions import Transaction
from app.crud.wallets import crud_create_wallet, crud_purchase_asset, crud_sell_asset
from app.crud.wallets import crud_get_wallet_by_id, crud_get_transactions_for_wallet, crud_delete_wallet
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


@router.get("/users/{user_id}/wallet/{wallet_id}/transactions", response_model=PaginatedTransactionsResponse)
def get_transactions_for_wallet(
        user_id: int,
        wallet_id: int,
        limit: int = Query(10, ge=1),
        page: int = Query(1, ge=1),
        db: Session = Depends(get_db)
):
    transactions, total_transactions, total_pages, current_page = crud_get_transactions_for_wallet(
        db=db,
        user_id=user_id,
        wallet_id=wallet_id,
        limit=limit,
        page=page
    )

    # Return the response directly using the response model
    return PaginatedTransactionsResponse(
        transactions=transactions,
        total_transactions=total_transactions,
        total_pages=total_pages,
        current_page=current_page
    )


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
