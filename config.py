# config.py
import os

# Read API key ONLY from environment variable (Render-compatible)
TD_API_KEY = os.getenv("TD_API_KEY")

if not TD_API_KEY:
    raise RuntimeError(
        "TD_API_KEY not found. Please set it in Render Environment Variables."
    )

SYMBOL = "XAU/USD"

TIMEFRAMES = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1H": "1h",
    "4H": "4h",
    "1D": "1day"
}

ACCENT_COLOR = "#00FFD1"
