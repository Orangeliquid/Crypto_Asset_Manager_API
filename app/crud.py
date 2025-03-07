from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import bcrypt

from app.models import User
from app.schemas import UserCreate, UserUpdate, UserLogin, UserLoginResponse
from app.schemas import UserResponse, UserUpdateResponse, UserDeleteResponse
from app.utils.security import hash_password, verify_password, create_access_token


def crud_create_user(db: Session, user: UserCreate) -> UserResponse:
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_password = hash_password(user.password)

    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(id=new_user.id, username=new_user.username, email=new_user.email)


def crud_get_user_by_username(db: Session, username: str):
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail=f"{username} not found")

    return user


def crud_get_all_users(db: Session):
    users = db.query(User).all()
    return users


def crud_update_user(db: Session, user_id: int, user_update: UserUpdate):
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail=f"{user_id} not found")

    old_data = UserResponse(id=db_user.id, username=db_user.username, email=db_user.email)

    password_changed = False

    if user_update.username:
        db_user.username = user_update.username

    if user_update.email:
        db_user.email = user_update.email

    if user_update.password:
        if bcrypt.checkpw(user_update.password.encode('utf-8'), db_user.password_hash.encode('utf-8')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from the current password"
            )
        db_user.password_hash = hash_password(user_update.password)
        password_changed = True

    db.commit()
    db.refresh(db_user)

    new_data = UserResponse(id=db_user.id, username=db_user.username, email=db_user.email)

    return UserUpdateResponse(
        old_data=old_data,
        new_data=new_data,
        password_changed=password_changed
    )


def crud_delete_user(db: Session, user_id: int) -> UserDeleteResponse:
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User: {user_id} not found"
        )

    db.delete(db_user)
    db.commit()

    return UserDeleteResponse(message="User deleted successfully", user_id=user_id)


def crud_authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return user


def crud_login_user(db: Session, user_login: UserLogin):
    user = crud_authenticate_user(db, user_login.username, user_login.password)
    access_token = create_access_token(user_id=user.id)
    return UserLoginResponse(access_token=access_token, token_type="bearer")
