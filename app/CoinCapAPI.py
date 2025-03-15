import requests
import time

# Cache for assets and coin names (2-minute expiration)
_cache = {
    "timestamp": 0,
    "assets": {},
    "coins": []
}
CACHE_DURATION = 120


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
        print(f"Error fetching all assets: {e}")
        return _cache


def valid_coin_names():
    """Returns a list of valid coin names using cached data when possible."""
    return fetch_all_assets()["coins"]


def get_current_coin_data(coin_name: str):
    """Fetches the current value of a specific coin, using cache if available."""

    cache = fetch_all_assets()

    if coin_name in cache["coins"]:
        return cache["assets"].get(coin_name)

    print(f"Coin '{coin_name}' not found.")
    return None


if __name__ == '__main__':
    print("Valid Coins:", valid_coin_names())
    print("Cardano Price:", get_current_coin_data("cardano"))
    print("XRP Price:", get_current_coin_data("xrp"))
    print("Ethereum Price:", get_current_coin_data("ethereum"))
