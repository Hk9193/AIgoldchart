import requests
import pandas as pd
from config import TD_API_KEY, SYMBOL

def fetch_xauusd(interval="5min", outputsize=300):
    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": SYMBOL,
        "interval": interval,
        "apikey": TD_API_KEY,
        "outputsize": outputsize,
        "format": "JSON"
    }

    response = requests.get(url, params=params).json()

    if "status" in response and response["status"] == "error":
        return None, response.get("message", "API error")

    if "values" not in response:
        return None, "No data returned (API limit or invalid request)"

    df = pd.DataFrame(response["values"])

    df["datetime"] = pd.to_datetime(df["datetime"])
    df.set_index("datetime", inplace=True)

    # ✅ Convert price columns
    for col in ["open", "high", "low", "close"]:
        df[col] = df[col].astype(float)

    # ✅ SAFE volume handling (CRITICAL FIX)
    if "volume" in df.columns:
        df["volume"] = df["volume"].astype(float)
    else:
        df["volume"] = 0.0   # metals/FX often have no volume

    df = df.sort_index()

    return df, None
