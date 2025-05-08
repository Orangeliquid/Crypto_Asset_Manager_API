# Crypto Asset Manager API

The Crypto Asset Manager API is a RESTful API built with FastAPI that allows users to manage their cryptocurrency holdings. It provides functionality for creating users, wallets associated with users, adding assets, tracking transactions, and calculating portfolio value and performance. The API uses SQLAlchemy for database persistence and Pydantic models for request validation and response serialization. Asset prices are fetched in real-time using the CoinCap API.

## UPDATE: CoinCap API has migrated from 2.0 to 3.0

CoinCap API documentation can be found here:
https://docs.coincap.io/

Changes:
- API key required
- limit of 2,500 calls per month for free tier

This means that the integration of CoinCap API 2.0 in this project no longer works. Valuation of assets when purchasing, selling, and quering assets no longer works. I will look into refactoring and implementing CoinCap API 3.0 in the future.


## Table of Contents

- [Installation](#installation)
- [Usage](#usage-api-overview)
- [API-Endpoints](#api-endpoints)
  - [Users](#users)
  - [Wallets](#wallets)
  - [Transactions-and-Valuations](#transactions-and-valuations)
- [License](#license)

## Installation

To run the Crypto Asset Manager API locally, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/Orangeliquid/Crypto-Asset-Manager-API.git
   cd Crypto-Asset-Manager-API
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a .env file in Crypto_Wallet_API
   ```bash
   echo -e "SECRET_KEY=your_secret_key_here\nALGORITHM=HS256\nACCESS_TOKEN_EXPIRE_MINUTES=30" > .env
   ```
   These variables are used for authentication and token generation:

   - SECRET_KEY: A secret string used to sign and verify JWT tokens. Change this to a secure, random value. Example: SECRET_KEY=aGsdg12A1sd32f2SD1vS0dseghhas2

   - ALGORITHM: The hashing algorithm used for encoding the JWT (default is HS256).
     Example: ALGORITHM=HS256

   - ACCESS_TOKEN_EXPIRE_MINUTES: Defines how long an access token remains valid (default is 30 minutes).
     Example: ACCESS_TOKEN_EXPIRE_MINUTES=30

   Adjust these values as needed for your security and expiration preferences.
   

## Usage API Overview

1. **Ensure all packages from `requirements.txt` are installed**  
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure .env is created and variables are set

3. Start the application:
   ```bash
   python main.py
   ```
   
4. Navigate to the interactive documentation
   - http://127.0.0.1:8000/docs
   
5. Create a user
   - POST /users/

6. Create a wallet for the user
   - POST /users/{user_id}/wallet/

7. Purchase assets for user wallet
   - PUT /users/{user_id}/wallet/{wallet_id}/purchase_asset
  
8. Sell assets for user wallet
   - PUT /users/{user_id}/wallet/{wallet_id}/sell_asset
     
9. Additional endpoints for user and wallet management:

    ### Users Endpoints
   - GET /users/ - Fetch All Users
   - GET /users/{username} - Fetch User By Name
   - PUT /users/{user_id} - Modify User
   - DELETE /users/{user_id} - Remove User
   - POST /login Login - User Login (returns JWT)

   ### Wallets Endpoints
   - GET /users/{user_id}/wallet/{wallet_id}/ - Fetch Wallet
   - GET /wallets/ Fetch All Wallets – Fetch All Wallets
   - DELETE /users/{user_id}/wallet/{wallet_id}/ - Delete Wallet

   ### Transactions & Valuations Endpoints
   - GET /users/{user_id}/wallet/{wallet_id}/all-transactions - Get All Transactions For Wallet
   - GET /users/{user_id}/wallet/{wallet_id}/valuation-by-date - Get Wallet Valuation

## API Endpoints

### Users

- **GET /users/**
- **Description**: Fetch all users in database.
- **Successful Response**:
  ```json
  [
    {
      "username": "string",
      "email": "string",
      "id": 0
    }
  ]
  ```
---

- **POST /users/**
- **Description**: Creates a new user in the database.
- **Request Body**:
  ```json
  {
    "username": "string",
    "email": "string",
    "password": "string"
  }
  ```
- **200 Successful Response**:
  ```json
  {
    "username": "string",
    "email": "string",
    "id": 0
  }
  ```
- **422 Validation Error**:
  ```json
  {
    "detail": [
      {
        "loc": [
          "string",
          0
        ],
        "msg": "string",
        "type": "string"
      }
    ]
  }
  ```
---

- **GET /users/{username}**
- **Description**: Fetch user by username in database.
- **Request Body**:
  ```json
  {
    "username": "string",
  }
  ```
- **200 Successful Response**:
  ```json
  {
    "username": "string",
    "email": "string",
    "id": 0
  }
  ```
- **422 Validation Error**:
  ```json
  {
    "detail": [
      {
        "loc": [
          "string",
          0
        ],
        "msg": "string",
        "type": "string"
      }
    ]
  }
  ```
---

- **PUT /users/{user_id}**
- **Description**: Modify user in database.
- **Request Body**:
  ```json
  {
    "user_id": 0,
  }
  ```
- **200 Successful Response**:
  ```json
  {
    "old_data": {
      "username": "string",
      "email": "string",
      "id": 0
    },
    "new_data": {
      "username": "string",
      "email": "string",
      "id": 0
    },
    "password_changed": true
  }
  ```
- **422 Validation Error**:
  ```json
  {
    "detail": [
      {
        "loc": [
          "string",
          0
        ],
        "msg": "string",
        "type": "string"
      }
    ]
  }
  ```
---

- **DELETE /users/{user_id}**
- **Description**: Remove user from database.
- **Request Body**:
  ```json
  {
    "user_id": 0,
  }
  ```
- **200 Successful Response**:
  ```json
  {
    "message": "string",
    "user_id": 0
  }
  ```
- **422 Validation Error**:
  ```json
  {
    "detail": [
      {
        "loc": [
          "string",
          0
        ],
        "msg": "string",
        "type": "string"
      }
    ]
  }
  ```

- **POST /login**
- **Description**: Login user.
- **Request Body**:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **200 Successful Response**:
  ```json
  {
    "access_token": "string",
    "token_type": "string"
  }
  ```
- **422 Validation Error**:
  ```json
  {
    "detail": [
      {
        "loc": [
          "string",
          0
        ],
        "msg": "string",
        "type": "string"
      }
    ]
  }
  ```
---

### Wallets

- **POST /users/{user_id}/wallet/**
- **Description**: Create wallet in database.
- **Request Body**:
  ```json
  {
    "user_id": 0,
  }
  ```
- **200 Successful Response**:
  ```json
  {
    "id": 0,
    "user_id": 0
  }
  ```
- **422 Validation Error**:
  ```json
  {
    "detail": [
      {
        "loc": [
          "string",
          0
        ],
        "msg": "string",
        "type": "string"
      }
    ]
  }
  ```
---

- **GET /users/{user_id}/wallet/{wallet_id}/**
- **Description**: Fetch wallet in database.
- **Request Body**:
  ```json
  {
    "user_id": 0,
    "wallet_id": 0,
    "limit": {
        "value": 1
        "min": 1,
        "default": 10,
     }
    "page": {
        "value": 1,
        "min": 1,
        "default": 1
     }
    "sort_by": {
      "default": "coin_name",
      "others": [
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
        "change_percent_24hr"
      ]
    }
    "sort_order": {
        "default": "asc",
        "other": "desc"
  }
  ```
- **200 Successful Response**:
  ```json
  {
    "total_count": 0,
    "total_pages": 0,
    "current_page": 0,
    "total_wallet_value_usd": 0,
    "assets": [
      {
        "coin_name": "string",
        "quantity": 0,
        "purchase_value_usd": 0,
        "coin_cap_id": "string",
        "coin_cap_rank": 0,
        "coin_cap_symbol": "string",
        "current_price_usd": 0,
        "current_value_usd": 0,
        "net_gain_loss": 0,
        "initial_purchase_date": "2025-04-04T06:03:21.865Z",
        "market_cap_usd": 0,
        "supply": 0,
        "max_supply": 0,
        "volume_usd_24hr": 0,
        "change_percent_24hr": 0,
        "vwap_24hr": 0,
        "explorer_url": "Missing URL from CoinCapAPI",
        "id": 0
      }
    ]
  }
  ```
- **422 Validation Error**:
  ```json
  {
    "detail": [
      {
        "loc": [
          "string",
          0
        ],
        "msg": "string",
        "type": "string"
      }
    ]
  }
  ```
---

- **Delete /users/{user_id}/wallet/{wallet_id}/**
- **Description**: Remove a wallet from the database.
- **Request Body**:
  ```json
  {
    "user_id": 0,
    "wallet_id": 0
  }
  ```
- **200 Successful Response**:
  ```json
  {
    "message": "string"
  }
  ```
- **422 Validation Error**:
  ```json
  {
    "detail": [
      {
        "loc": [
          "string",
          0
        ],
        "msg": "string",
        "type": "string"
      }
    ]
  }
  ```
---

- **GET /wallets/**
- **Description**: Fetch all wallets in database.
- **200 Successful Response**:
  ```json
  [
    {
      "id": 0,
      "user_id": 0,
      "amount_of_coins": 0,
      "total_value_usd": 0,
      "assets": [
        {
          "coin_name": "string",
          "quantity": 0,
          "purchase_value_usd": 0
        }
      ]
    }
  ]
  ```
---

### Transactions and Valuations

- **GET /users/{user_id}/wallet/{wallet_id}/all-transactions**
- **Description**: Get all transactions for a wallet.
- **Request Body**:
  ```json
  {
    "user_id": 0,
    "wallet_id": 0,
    "limit": {
        "default": 10,
        "minimum": 1
      }
    "page": {
        "default": 1,
        "minimum": 1
      }
  }
  ```
- **200 Successful Response**:
  ```json
  {
    "transactions": [
      {
        "id": 0,
        "coin_name": "string",
        "quantity": 0,
        "price_per_coin": 0,
        "total_price": 0,
        "transaction_date": "2025-04-04T06:25:59.891Z",
        "type": "purchase"
      }
    ],
    "total_transactions": 0,
    "total_pages": 0,
    "current_page": 0
  }
  ```
- **422 Validation Error**:
  ```json
  {
    "detail": [
      {
        "loc": [
          "string",
          0
        ],
        "msg": "string",
        "type": "string"
      }
    ]
  }
  ```
---

- **GET /users/{user_id}/wallet/{wallet_id}/valuation-by-date**
- **Description**: Get wallet valuation at a specific date.
- **Request Body**:
  ```json
  {
    "user_id": 0,
    "wallet_id": 0,
    "historical_date": "2025-03-25"
  }
  ```
- **200 Successful Response**:
  ```json
  {
    "wallet_id": 0,
    "snap_shot_date": "string",
    "snap_shot_date_relative_to_historic_date": "string",
    "holdings": {},
    "total_value_usd_on_snapshot_date": 0,
    "date_requested_total_value": 0,
    "net_gain_loss": 0
  }
  ```
- **422 Validation Error**:
  ```json
  {
    "detail": [
      {
        "loc": [
          "string",
          0
        ],
        "msg": "string",
        "type": "string"
      }
    ]
  }
  ```
---

- **PUT /users/{user_id}/wallet/{wallet_id}/purchase_asset**
- **Description**: Purchase asset for wallet.
- **Request Body**:
  ```json
  {
    "user_id": 0,
    "wallet_id": 0,
    "coin_name": "coin_name",
    "quantity": 1
  }
  ```
- **200 Successful Response**:
  ```json
  {
    "user_id": 0,
    "wallet_id": 0,
    "asset_id": 0,
    "coin_name": "string",
    "quantity_purchased": 0,
    "purchase_price": 0,
    "total_purchase_price": 0,
    "updated_coin_quantity": 0,
    "purchase_date": "2025-04-04T06:30:49.075Z",
    "id": 0
  }
  ```
- **422 Validation Error**:
  ```json
  {
    "detail": [
      {
        "loc": [
          "string",
          0
        ],
        "msg": "string",
        "type": "string"
      }
    ]
  }
  ```
---

- **PUT /users/{user_id}/wallet/{wallet_id}/sell_asset**
- **Description**: Sell asset from wallet.
- **Request Body**:
  ```json
  {
    "user_id": 0,
    "wallet_id": 0,
    "coin_name": "coin_name",
    "quantity": 1
  }
  ```
- **200 Successful Response**:
  ```json
  {
    "user_id": 0,
    "wallet_id": 0,
    "asset_id": 0,
    "coin_name": "string",
    "quantity_sold": 0,
    "sale_price": 0,
    "total_sale_price": 0,
    "remaining_coin_quantity": 0,
    "id": 0,
    "sale_date": "2025-04-04T06:32:16.937Z"
  }
  ```
- **422 Validation Error**:
  ```json
  {
    "detail": [
      {
        "loc": [
          "string",
          0
        ],
        "msg": "string",
        "type": "string"
      }
    ]
  }
  ```
---

## License

This project is licensed under the [MIT License](LICENSE.txt).
