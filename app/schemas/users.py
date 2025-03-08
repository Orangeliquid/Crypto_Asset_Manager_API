from pydantic import BaseModel
from typing import Optional


class UserBase(BaseModel):
    username: str
    email: str

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class UserUpdateResponse(BaseModel):
    old_data: UserResponse
    new_data: UserResponse
    password_changed: Optional[bool] = None


class UserDeleteResponse(BaseModel):
    message: str
    user_id: int


class UserLogin(BaseModel):
    username: str
    password: str


class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str
