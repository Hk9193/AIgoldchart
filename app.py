import streamlit as st
import plotly.graph_objects as go

from data.fetch_data import fetch_xauusd
from features.indicators import SMA, EMA, RSI, ATR
from models.ml_model import train_model
from inference.trade_logic import trade_setup
from ui.theme import apply_theme
from config import TIMEFRAMES

# ----------------- UI THEME -----------------
apply_theme()

st.title("AIgoldchart – XAUUSD AI Trading Dashboard")

# ----------------- TIMEFRAME -----------------
timeframe_label = st.selectbox(
    "Select Timeframe",
    list(TIMEFRAMES.keys())
)

interval = TIMEFRAMES[timeframe_label]

# ----------------- DATA LOADING (CACHED) -----------------
@st.cache_data(ttl=60)
def load_data(interval):
    return fetch_xauusd(interval=interval)

df, error = load_data(interval)

if error:
    st.error(f"Data Error: {error}")
    st.info("If API limit was reached, please wait 1 minute and refresh.")
    st.stop()

# ----------------- INDICATORS -----------------
df["SMA"] = SMA(df["close"])
df["EMA"] = EMA(df["close"])
df["RSI"] = RSI(df["close"])
df["ATR"] = ATR(df)

# ----------------- CHART -----------------
fig = go.Figure(
    data=[
        go.Candlestick(
            x=df.index,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            increasing_line_color="#00FFD1",
            decreasing_line_color="#FF4B4B",
        )
    ]
)

fig.update_layout(
    template="plotly_dark",
    height=550,
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis_title="Time",
    yaxis_title="Price (USD)",
)

st.plotly_chart(fig, use_container_width=True)

# ----------------- AI ANALYSIS -----------------
if st.button("Run A.I. Analysis"):
    model, features = train_model(df)

    latest = df.iloc[-1][features].values.reshape(1, -1)
    prob = model.predict_proba(latest)[0][1]

    if prob > 0.6:
        bias = "Bullish"
    elif prob < 0.4:
        bias = "Bearish"
    else:
        bias = "Neutral"

    entry, sl, tp = trade_setup(
        df["close"].iloc[-1],
        df["ATR"].iloc[-1],
        bias
    )

    st.subheader("A.I. Trade Analysis")

    col1, col2 = st.columns(2)
    col1.metric("Market Bias", bias)
    col2.metric("Confidence", f"{round(prob * 100, 2)}%")

    if entry:
        st.write(f"**Entry Price:** {round(entry, 2)}")
        st.write(f"**Stop Loss:** {round(sl, 2)}")
        st.write(f"**Take Profit:** {round(tp, 2)}")
