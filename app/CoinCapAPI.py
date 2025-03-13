import requests
import time

# Cache valid coin names for 5 minutes
_coin_cache = {
    "timestamp": 0,
    "coins": [],
    "values": {}
}
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

        _coin_cache["timestamp"] = int(time.time())
        _coin_cache["coins"] = all_coin_symbols

        return all_coin_symbols

    except requests.RequestException as e:
        print(f"Error fetching coin names: {e}")
        return []


def get_current_coin_value(coin_name: str):
    global _coin_cache

    if time.time() - _coin_cache["timestamp"] < CACHE_DURATION:
        if coin_name in _coin_cache["values"]:
            return _coin_cache["values"][coin_name]

    url = f"https://api.coincap.io/v2/assets/{coin_name}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json().get('data', {})

        price = data.get('priceUsd')
        if price is None:
            raise ValueError(f"Price not found for coin: {coin_name}")

        _coin_cache["values"][coin_name] = round(float(price), 4)

        return round(float(price), 4)

    except requests.RequestException as e:
        print(f"Error fetching coin value: {e}")
        return None

    except ValueError as ve:
        print(f"Invalid data: {ve}")
        return None


if __name__ == '__main__':
    print(valid_coin_names())
    print(get_current_coin_value("bitcoin"))
    print(get_current_coin_value("xrp"))
