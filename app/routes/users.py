from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.schemas.users import UserCreate, UserUpdate, UserResponse, UserUpdateResponse, UserDeleteResponse
from app.schemas.users import UserLogin, UserLoginResponse
from app.crud.users import crud_update_user, crud_delete_user, crud_get_user_by_username, crud_get_all_users
from app.crud.users import crud_login_user, crud_create_user
from app.database import get_db

router = APIRouter()


@router.post("/users/", response_model=UserResponse)
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    return crud_create_user(db=db, user=user)


@router.get("/users/{username}", response_model=UserResponse)
def fetch_user_by_name(username: str, db: Session = Depends(get_db)):
    return crud_get_user_by_username(db=db, username=username)


@router.get("/users/", response_model=List[UserResponse])
def fetch_all_users(db: Session = Depends(get_db)):
    return crud_get_all_users(db=db)


@router.put("/users/{user_id}", response_model=UserUpdateResponse)
def modify_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    return crud_update_user(db=db, user_id=user_id, user_update=user_update)


@router.delete("/users/{user_id}", response_model=UserDeleteResponse)
def remove_user(user_id: int, db: Session = Depends(get_db)):
    return crud_delete_user(db=db, user_id=user_id)


@router.post("/login", response_model=UserLoginResponse)
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    return crud_login_user(db=db, user_login=user_login)
