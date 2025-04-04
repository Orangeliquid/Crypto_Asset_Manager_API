import requests
import time
from fastapi import HTTPException

# Cache for assets and coin names (2-minute expiration)
_cache = {
    "timestamp": 0,
    "assets": {},
    "coins": [],
    "historical_prices": {}
}

CACHE_DURATION = 120
HISTORICAL_CACHE_DURATION = 86400


def fetch_all_assets():
    """Fetch all crypto assets and cache them for quick access."""
    global _cache

    if time.time() - _cache["timestamp"] < CACHE_DURATION:
        print(
            f"Using cached data, time remaining for cache: "
            f"{CACHE_DURATION - (time.time() - _cache['timestamp']):.2f} seconds"
        )
        return _cache

    url = "https://api.coincap.io/v2/assets"

    try:
        time.sleep(0.5)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print("Called GET CoinCapAPI")

        data = response.json().get("data", [])

        assets_dict = {coin["id"]: coin for coin in data}

        _cache.update({
            "timestamp": time.time(),
            "assets": assets_dict,
            "coins": list(assets_dict.keys())
        })

        return _cache

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching all assets: {e}")


def valid_coin_names():
    """Returns a list of valid coin names using cached data when possible."""
    return fetch_all_assets()["coins"]


def get_current_coin_data(coin_name: str):
    """Fetches the current value of a specific coin, using cache if available."""
    cache = fetch_all_assets()
    return cache["assets"].get(coin_name, None)


def fetch_dated_coin_price(coin_name: str, start_timestamp: int, end_timestamp: int):
    """Fetches the historical price of the coin within a time range."""
    global _cache

    # Convert timestamps to milliseconds
    start_timestamp = (start_timestamp - (2 * 86400)) * 1000  # Subtract two days to ensure capture
    end_timestamp *= 1000

    # Check cache
    if coin_name in _cache["historical_prices"]:
        historical_data = _cache["historical_prices"][coin_name]
        if historical_data["start"] == start_timestamp and historical_data["end"] == end_timestamp:
            print(f"Using cached historical data for {coin_name}.")
            return historical_data["data"]

    # CoinCap API URL
    url = f"https://api.coincap.io/v2/assets/{coin_name}/history?interval=d1&start={start_timestamp}&end={end_timestamp}"

    try:
        time.sleep(0.50)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print(f"Called GET CoinCapAPI for {coin_name}")

        data = response.json().get("data", [])

        if not data:
            print(f"No data found for {coin_name} between {start_timestamp} and {end_timestamp}")
            return None

        # Ensure first date matches the intended start
        if data and data[0]["time"] > start_timestamp:
            print(f"Adjusting first record. First data point is {data[0]['date']} instead of requested start.")

        # Cache the data
        _cache["historical_prices"][coin_name] = {
            "start": start_timestamp,
            "end": end_timestamp,
            "timestamp": time.time(),
            "data": data
        }

        return data

    except requests.RequestException as e:
        print(f"Error fetching historical data for {coin_name}: {e}")
        return None
