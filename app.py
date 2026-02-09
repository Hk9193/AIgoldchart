import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

from data.fetch_data import fetch_xauusd
from features.indicators import SMA, EMA, RSI, ATR, MACD, BOLLINGER_BANDS, STOCHASTIC_RSI
from models.ml_model import train_model
from inference.trade_logic import trade_setup
from ui.theme import apply_theme
from config import TIMEFRAMES, ACCENT_COLOR

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Algoldchart – XAUUSD AI Trading Dashboard",
    page_icon="🟡",
    layout="wide"
)

apply_theme()

# ---------------- CUSTOM CSS ----------------
st.markdown(f"""
<style>
.card {{
    background-color: #111827;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    margin-bottom: 20px;
}}

.header button {{
    background: transparent !important;
    color: #e5e7eb !important;
    border: none !important;
    font-size: 15px !important;
}}

.bias-bullish {{ color: #22c55e; font-weight: 700; }}
.bias-bearish {{ color: #ef4444; font-weight: 700; }}
.bias-neutral {{ color: #9ca3af; font-weight: 700; }}

.metric-big {{
    font-size: 44px;
    font-weight: 800;
}}

.stButton>button {{
    background-color: {ACCENT_COLOR};
    color: black;
    border-radius: 10px;
}}

.caption {{
    color: #9ca3af;
    font-size: 13px;
}}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
col1, col2 = st.columns([3, 2])
with col1:
    st.markdown("## 🟡 **Algoldchart**")
with col2:
    menu = ["Dashboard", "Strategies", "Backtest", "Settings", "Profile"]
    cols = st.columns(len(menu))
    for c, item in zip(cols, menu):
        with c:
            st.button(item, key=item)

# ---------------- HERO SECTION ----------------
hero_left, hero_right = st.columns([3, 2])

with hero_left:
    st.markdown("## **XAUUSD AI Trading Dashboard**")
    st.write(
        "Professional AI-powered Gold (XAUUSD) analysis with real-time charts, "
        "market bias, confidence scoring, and risk-managed trade setups."
    )

    b1, b2 = st.columns(2)
    with b1:
        run_ai = st.button("🚀 Run AI Analysis", use_container_width=True)
    with b2:
        st.button("📄 Export Report", use_container_width=True)

# ---------------- TIMEFRAME + DATA ----------------
timeframe_label = st.selectbox("Timeframe", list(TIMEFRAMES.keys()))
interval = TIMEFRAMES[timeframe_label]

@st.cache_data(ttl=60)
def load_data(interval):
    return fetch_xauusd(interval)

df, error = load_data(interval)

if error:
    st.error(error)
    st.stop()

# ---------------- INDICATORS ----------------
df["SMA"] = SMA(df["close"])
df["EMA"] = EMA(df["close"])
df["RSI"] = RSI(df["close"])
df["ATR"] = ATR(df)
# New indicators
df["MACD"], df["MACD_Signal"], df["MACD_Hist"] = MACD(df["close"])
df["BB_Upper"], df["BB_Middle"], df["BB_Lower"] = BOLLINGER_BANDS(df["close"])
df["Stoch_K"], df["Stoch_D"] = STOCHASTIC_RSI(df["close"])

# ---------------- HERO CHART ----------------
with hero_right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    fig_small = go.Figure(go.Candlestick(
        x=df.index[-20:],
        open=df["open"].tail(20),
        high=df["high"].tail(20),
        low=df["low"].tail(20),
        close=df["close"].tail(20),
    ))
    fig_small.update_layout(
        template="plotly_dark",
        height=220,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis_rangeslider_visible=False
    )
    st.plotly_chart(fig_small, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- MAIN CHART ----------------
st.markdown('<div class="card">', unsafe_allow_html=True)

fig = go.Figure(go.Candlestick(
    x=df.index,
    open=df["open"],
    high=df["high"],
    low=df["low"],
    close=df["close"],
    increasing_line_color="#22c55e",
    decreasing_line_color="#ef4444",
))

fig.update_layout(
    template="plotly_dark",
    height=520,
    xaxis_rangeslider_visible=False,
    yaxis_title="Price (USD)"
)

st.plotly_chart(fig, use_container_width=True)
st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
st.markdown('</div>', unsafe_allow_html=True)

# ---------------- AI ANALYSIS ----------------
if run_ai:
    model, features = train_model(df)
    latest = df.iloc[-1][features].values.reshape(1, -1)
    prob = model.predict_proba(latest)[0][1]

    if prob > 0.6:
        bias, css = "Bullish", "bias-bullish"
    elif prob < 0.4:
        bias, css = "Bearish", "bias-bearish"
    else:
        bias, css = "Neutral", "bias-neutral"

    entry, sl, tp = trade_setup(df["close"].iloc[-1], df["ATR"].iloc[-1], bias)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🤖 AI Trade Analysis")
    st.markdown(f"<div class='{css}'>Market Bias: {bias}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-big'>{round(prob*100,2)}%</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Trend Strength", "Strong")
    c2.metric("Volatility", "Medium")
    c3.metric("Signal Time", "Now")

    if entry:
        st.write(f"**Entry:** {round(entry,2)}")
        st.write(f"**Stop Loss:** {round(sl,2)}")
        st.write(f"**Take Profit:** {round(tp,2)}")

    st.markdown('</div>', unsafe_allow_html=True)
