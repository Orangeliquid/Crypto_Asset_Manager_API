import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.models import Base, User
from app.crud import users
from app.schemas.users import UserCreate, UserUpdate, UserLogin


# Database configuration for tests (in-memory SQLite database)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


# Fixture for getting the database session and resetting the DB
@pytest.fixture(scope="function")
def db():
    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        yield db
    finally:
        # Drop tables after each test
        Base.metadata.drop_all(bind=engine)
        db.close()


# Test for creating a user
def test_create_user(db):
    user_data = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="password123"
    )

    created_user = users.crud_create_user(db, user_data)

    assert created_user.username == user_data.username
    assert created_user.email == user_data.email
    assert created_user.password_hash != user_data.password  # Assuming password is hashed


# Test for creating a user with an existing username
def test_create_user_with_existing_username(db):
    user_data = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="password123"
    )

    # First user creation should succeed
    users.crud_create_user(db, user_data)

    # Try creating another user with the same username
    duplicate_user_data = UserCreate(
        username="testuser",
        email="newuser@example.com",
        password="newpassword123"
    )

    # Check that an HTTPException is raised with a 400 status code
    with pytest.raises(HTTPException) as exc_info:
        users.crud_create_user(db, duplicate_user_data)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Username already registered"


# Test for creating a user with an existing email
def test_create_user_with_existing_email(db):
    user_data = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="password123"
    )

    # First user creation should succeed
    users.crud_create_user(db, user_data)

    # Try creating another user with the same email
    duplicate_user_data = UserCreate(
        username="testuser2",
        email="testuser@example.com",
        password="newpassword123"
    )

    # Check that an HTTPException is raised with a 400 status code
    with pytest.raises(HTTPException) as exc_info:
        users.crud_create_user(db, duplicate_user_data)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Email already registered"


# Test for retrieving a user by username
def test_get_user_by_username(db):
    user_data = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="password123"
    )
    created_user = users.crud_create_user(db, user_data)

    user = users.crud_get_user_by_username(db, "testuser")
    assert user.username == created_user.username


# Test for retrieving a user by non-existent username
def test_get_user_by_username_not_found(db):
    with pytest.raises(HTTPException):
        users.crud_get_user_by_username(db, "nonexistentuser")


def test_get_user_by_id(db):
    user_data = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="password123"
    )
    created_user = users.crud_create_user(db, user_data)

    user = users.crud_get_user_by_id(db, 1)
    assert user.username == created_user.username
    assert user.email == created_user.email


def test_get_user_by_id_not_found(db):
    with pytest.raises(HTTPException):
        users.crud_get_user_by_id(db, 1)


def test_get_all_users(db):
    user_data = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="password123"
    )

    created_user = users.crud_create_user(db, user_data)
    # Get all users
    users_list = users.crud_get_all_users(db)

    assert users_list is not None
    assert len(users_list) > 0
    assert users_list[0].username == "testuser"
    assert users_list[0].email == "testuser@example.com"


def test_get_all_users_none_in_db(db):
    users_list = users.crud_get_all_users(db)

    assert users_list == []
    assert len(users_list) == 0


# Test for updating a user
def test_update_user(db):
    user_data = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="password123"
    )
    created_user = users.crud_create_user(db, user_data)

    user_update = UserUpdate(username="newusername", email="newemail@example.com", password="password1234")
    updated_user = users.crud_update_user(db, created_user.id, user_update)

    assert updated_user.new_data.username == user_update.username
    assert updated_user.new_data.email == user_update.email
    assert updated_user.password_changed == True


def test_update_user_id_not_found(db):
    user_data = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="password123"
    )
    created_user = users.crud_create_user(db, user_data)

    user_update = UserUpdate(username="newusername", email="newemail@example.com")

    with pytest.raises(HTTPException) as exc_info:
        users.crud_update_user(db, created_user.id + 1, user_update)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == f"{created_user.id + 1} not found"


def test_update_user_password_the_same(db):
    user_data = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="password123"
    )
    created_user = users.crud_create_user(db, user_data)

    user_update = UserUpdate(password="password123")

    with pytest.raises(HTTPException) as exc_info:
        users.crud_update_user(db, created_user.id, user_update)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "New password must be different from the current password"


# Test for deleting a user
def test_delete_user(db):
    user_data = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="password123"
    )
    created_user = users.crud_create_user(db, user_data)

    delete_response = users.crud_delete_user(db, created_user.id)
    assert delete_response.user_id == created_user.id
    assert delete_response.message == "User deleted successfully"


def test_delete_user_not_found(db):
    with pytest.raises(HTTPException) as exc_info:
        users.crud_delete_user(db, 1)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == f"User: 1 not found"


# Test for user login (valid credentials)
def test_user_login(db):
    user_data = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="password123"
    )
    users.crud_create_user(db, user_data)

    user_login_data = UserLogin(username="testuser", password="password123")
    login_response = users.crud_login_user(db, user_login_data)

    assert login_response.access_token is not None


# Test for user login (invalid credentials)
def test_user_login_invalid(db):
    user_data = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="password123"
    )
    users.crud_create_user(db, user_data)

    user_login_data = UserLogin(username="testuser", password="wrongpassword")

    with pytest.raises(HTTPException):
        users.crud_login_user(db, user_login_data)
