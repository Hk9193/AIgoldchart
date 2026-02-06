import os
import streamlit as st

# ✅ Works for: Local + Streamlit Cloud + Render
TD_API_KEY = (
    st.secrets.get("TD_API_KEY")
    if hasattr(st, "secrets")
    else None
) or os.getenv("TD_API_KEY")

if TD_API_KEY is None:
    raise RuntimeError(
        "TD_API_KEY not found. Set it as an environment variable or Streamlit secret."
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
