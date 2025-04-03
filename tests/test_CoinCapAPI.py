import time
import pytest
from unittest.mock import patch
from fastapi import HTTPException
import requests

from app import CoinCapAPI as CCA


def test_fetch_dated_coin_price_no_data():
    """Tests that fetch_dated_coin_price returns None when no data is found."""
    start = int(time.mktime(time.strptime("2025-03-23", "%Y-%m-%d")))
    end = int(time.mktime(time.strptime("2025-03-24", "%Y-%m-%d")))

    fake_empty_data = {"data": []}  # Correctly formatted empty response

    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = fake_empty_data

        result = CCA.fetch_dated_coin_price("xrp", start, end)

        assert result is None, f"Expected None, but got {result}"  # Debugging message
        mock_get.assert_called_once()


def test_fetch_all_asset_failure():
    with patch("requests.get", side_effect=requests.RequestException("Mock API failure")):
        with pytest.raises(HTTPException) as exc_info:
            CCA.fetch_all_assets()

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Error fetching all assets: Mock API failure"


def test_fetch_dated_coin_price():
    start = int(time.mktime(time.strptime("2025-03-23", "%Y-%m-%d")))
    end = int(time.mktime(time.strptime("2025-03-24", "%Y-%m-%d")))

    fake_data = {
        "data": [
            {'priceUsd': '2.3878369598216121', 'time': 1742601600000, 'date': '2025-03-22T00:00:00.000Z'},
            {'priceUsd': '2.3969424945949251', 'time': 1742688000000, 'date': '2025-03-23T00:00:00.000Z'}
        ]
    }

    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = fake_data

        first_call = CCA.fetch_dated_coin_price("xrp", start, end)
        assert first_call == fake_data["data"]
        assert "xrp" in CCA._cache["historical_prices"]
        mock_get.assert_called_once()

        second_call = CCA.fetch_dated_coin_price("xrp", start, end)
        assert second_call == fake_data["data"]
        mock_get.assert_called_once()
