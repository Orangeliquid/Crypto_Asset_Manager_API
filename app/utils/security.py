import os
from passlib.context import CryptContext
from dotenv import load_dotenv
import jwt
from datetime import datetime, timedelta

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int):
    to_encode = {"sub": str(user_id)}
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


if __name__ == '__main__':
    password = "mysecretpassword"
    hashed_password = pwd_context.hash(password)
    print(f"Hashed password: {hashed_password}")

    # Verify the password
    is_verified = pwd_context.verify(password, hashed_password)
    print(f"Password verification: {is_verified}")

    jwt_token = create_access_token(user_id=3)
    print(jwt_token)
