import requests
import time

# Cache valid coin names for 5 minutes
_coin_cache = {"timestamp": 0, "coins": []}
CACHE_DURATION = 300


def valid_coin_names():
    global _coin_cache

    if time.time() - _coin_cache["timestamp"] < CACHE_DURATION:
        return _coin_cache["coins"]

    url = "https://api.coincap.io/v2/assets"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json().get('data', [])
        all_coin_symbols = [coin['id'] for coin in data]

        # Update cache
        _coin_cache = {"timestamp": time.time(), "coins": all_coin_symbols}

        return all_coin_symbols

    except requests.RequestException as e:
        print(f"Error fetching coin names: {e}")
        return []


def get_current_coin_value(coin_name: str):
    url = f"https://api.coincap.io/v2/assets/{coin_name}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json().get('data', {})

        price = data.get('priceUsd')
        if price is None:
            raise ValueError(f"Price not found for coin: {coin_name}")

        return round(float(price), 4)

    except requests.RequestException as e:
        print(f"Error fetching coin value: {e}")
        return None

    except ValueError as ve:
        print(f"Invalid data: {ve}")
        return None


if __name__ == '__main__':
    # name_of_coin = "tether"
    # print(get_current_coin_value(name_of_coin))
    print(valid_coin_names())
