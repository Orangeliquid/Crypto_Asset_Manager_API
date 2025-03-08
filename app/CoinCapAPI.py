import requests


def valid_coin_symbols():
    url = "https://api.coincap.io/v2/assets"

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    data = response.json()['data']
    all_coin_symbols = [coin['symbol'] for coin in data]
    # for count, item in enumerate(data):
    #     print(f"{count + 1}| id: {item['id']} | name: {item['name']} | symbol: {item['symbol']} |"
    #           f" priceUsd: {item['priceUsd']}")
    return all_coin_symbols


if __name__ == '__main__':
    results = valid_coin_symbols()
    print(results)
    print(len(results))