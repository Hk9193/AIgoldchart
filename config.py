import streamlit as st

TD_API_KEY = st.secrets["TD_API_KEY"]

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
