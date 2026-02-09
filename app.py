import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import numpy as np

from data.fetch_data import fetch_xauusd
from features.indicators import SMA, EMA, RSI, ATR, MACD, BOLLINGER_BANDS, STOCHASTIC_RSI, VWAP
from models.ml_model import train_model
from inference.trade_logic import trade_setup, get_confirmation_score, RiskManager
from ui.theme import apply_theme
from config import TIMEFRAMES, ACCENT_COLOR

# ============ PAGE CONFIG ============
st.set_page_config(
    page_title="Algoldchart – XAUUSD AI Trading Dashboard",
    page_icon="🟡",
    layout="wide"
)

apply_theme()

# ============ CUSTOM CSS ============
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

# ============ HEADER ============
col1, col2 = st.columns([3, 2])
with col1:
    st.markdown("## 🟡 **Algoldchart**")
with col2:
    menu = ["Dashboard", "Strategies", "Backtest", "Settings", "Profile"]
    cols = st.columns(len(menu))
    for c, item in zip(cols, menu):
        with c:
            st.button(item, key=item)

# ============ HERO SECTION ============
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

# ============ TIMEFRAME + DATA ============
timeframe_label = st.selectbox("Timeframe", list(TIMEFRAMES.keys()))
interval = TIMEFRAMES[timeframe_label]

@st.cache_data(ttl=60)
def load_data(interval):
    return fetch_xauusd(interval)

df, error = load_data(interval)

if error:
    st.error(error)
    st.stop()

if df is None or len(df) == 0:
    st.error("No data available")
    st.stop()

# ============ CALCULATE ALL INDICATORS ============
try:
    # Original indicators
    df["SMA"] = SMA(df["close"])
    df["EMA"] = EMA(df["close"])
    df["RSI"] = RSI(df["close"])
    df["ATR"] = ATR(df)
    
    # NEW INDICATORS (MACD, Bollinger Bands, Stochastic RSI)
    df["MACD"], df["MACD_Signal"], df["MACD_Hist"] = MACD(df["close"])
    df["BB_Upper"], df["BB_Middle"], df["BB_Lower"] = BOLLINGER_BANDS(df["close"])
    df["Stoch_K"], df["Stoch_D"] = STOCHASTIC_RSI(df["close"])
    
    # VWAP (if volume available)
    if "volume" in df.columns:
        df["VWAP"] = VWAP(df["high"], df["low"], df["close"], df["volume"])
    
    st.success("✅ All indicators calculated successfully")
    
except Exception as e:
    st.error(f"Error calculating indicators: {e}")
    import traceback
    st.error(traceback.format_exc())
    st.stop()

# ============ HERO CHART ============
with hero_right:
    try:
        fig = go.Figure()
        
        # Add price line
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df["close"],
            mode='lines',
            name='Close Price',
            line=dict(color='#00FFD1', width=2)
        ))
        
        # Add SMA
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df["SMA"],
            mode='lines',
            name='SMA (14)',
            line=dict(color='#FFA500', width=1, dash='dash')
        ))
        
        # Add EMA
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df["EMA"],
            mode='lines',
            name='EMA (14)',
            line=dict(color='#FF6B6B', width=1, dash='dash')
        ))
        
        fig.update_layout(
            title="XAUUSD Price Chart",
            hovermode='x unified',
            template='plotly_dark',
            height=400,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not render chart: {e}")

# ============ TRADE SETUP SECTION (THE MAIN FIX) ============
st.markdown("---")
st.markdown("## 📈 AI Trade Analysis")

try:
    # Get current values
    current_price = df["close"].iloc[-1]
    current_atr = df["ATR"].iloc[-1] if pd.notna(df["ATR"].iloc[-1]) else 0.01
    
    # Determine bias based on recent price action
    if len(df) > 50:
        recent_returns = df["close"].pct_change().tail(50).mean()
        if recent_returns > 0.0001:
            bias = "Bullish"
            bias_color = "🟢"
        elif recent_returns < -0.0001:
            bias = "Bearish"
            bias_color = "🔴"
        else:
            bias = "Neutral"
            bias_color = "🟡"
    else:
        bias = "Neutral"
        bias_color = "🟡"
    
    # ✅ FIXED: Call trade_setup and handle DICTIONARY response
    trade_result = trade_setup(
        price=current_price,
        atr=current_atr,
        bias=bias,
        df=df,
        min_confidence=50
    )
    
    # Extract dictionary values (NOT tuple unpacking)
    entry = trade_result.get("entry")
    sl = trade_result.get("sl")
    tp = trade_result.get("tp")
    confidence = trade_result.get("confidence", 0)
    status = trade_result.get("status", "NEUTRAL")
    reason = trade_result.get("reason", "No signal")
    
    # Display main metrics
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric(
            "Market Bias",
            f"{bias_color} {bias}",
            delta=f"{confidence:.1f}% confidence"
        )
    
    with metric_col2:
        status_icon = "🟢" if status == "BUY" else "🔴" if status == "SELL" else "⏳"
        st.metric("Signal Status", f"{status_icon} {status}")
    
    with metric_col3:
        st.metric("Current Price", f"${current_price:.2f}")
    
    with metric_col4:
        st.metric("Volatility (ATR)", f"${current_atr:.4f}")
    
    st.markdown("---")
    
    # Display trade setup if signal exists
    if entry and status != "NEUTRAL":
        st.success(f"✅ **TRADE SIGNAL DETECTED** - {reason}")
        
        trade_col1, trade_col2, trade_col3 = st.columns(3)
        
        with trade_col1:
            st.metric("📍 Entry Price", f"${entry:.2f}", delta=f"Current: ${current_price:.2f}")
        
        with trade_col2:
            st.metric("⛔ Stop Loss", f"${sl:.2f}", delta=f"Risk: ${abs(entry-sl):.2f}")
        
        with trade_col3:
            st.metric("🎯 Take Profit", f"${tp:.2f}", delta=f"Target: ${abs(tp-entry):.2f}")
        
        # Calculate Risk/Reward Ratio
        if sl != entry:
            risk = abs(entry - sl)
            reward = abs(tp - entry)
            rrr = reward / risk if risk > 0 else 0
            
            rrr_col1, rrr_col2, rrr_col3 = st.columns(3)
            with rrr_col1:
                st.metric("📊 Risk/Reward", f"1:{rrr:.2f}")
            with rrr_col2:
                st.metric("💡 Confidence", f"{confidence:.1f}%", delta="Signal Quality")
            with rrr_col3:
                st.metric("Direction", bias)
    else:
        st.info(f"⏳ {reason}")
        st.write(f"**Confidence Score**: {confidence:.1f}% (Need 50%+ for signal)")

except Exception as e:
    st.error(f"Error in trade setup: {str(e)}")
    import traceback
    st.error(traceback.format_exc())

# ============ INDICATORS DASHBOARD ============
st.markdown("---")
st.markdown("## 📊 Technical Indicators Dashboard")

# Row 1: RSI, MACD, Stochastic
ind_row1_col1, ind_row1_col2, ind_row1_col3 = st.columns(3)

with ind_row1_col1:
    st.subheader("RSI (14)")
    if "RSI" in df.columns and pd.notna(df["RSI"].iloc[-1]):
        rsi_val = df["RSI"].iloc[-1]
        if rsi_val > 70:
            st.metric("RSI", f"{rsi_val:.2f}", delta="🔴 Overbought")
        elif rsi_val < 30:
            st.metric("RSI", f"{rsi_val:.2f}", delta="🟢 Oversold")
        else:
            st.metric("RSI", f"{rsi_val:.2f}", delta="🟡 Neutral")

with ind_row1_col2:
    st.subheader("MACD")
    if "MACD" in df.columns and "MACD_Signal" in df.columns:
        if pd.notna(df["MACD"].iloc[-1]) and pd.notna(df["MACD_Signal"].iloc[-1]):
            macd_val = df["MACD"].iloc[-1]
            signal_val = df["MACD_Signal"].iloc[-1]
            hist_val = df["MACD_Hist"].iloc[-1]
            
            macd_trend = "🟢 Bullish" if macd_val > signal_val else "🔴 Bearish"
            st.metric("MACD", f"{macd_val:.4f}", delta=f"{macd_trend} (Hist: {hist_val:.4f})")

with ind_row1_col3:
    st.subheader("Stochastic RSI")
    if "Stoch_K" in df.columns and pd.notna(df["Stoch_K"].iloc[-1]):
        stoch_k = df["Stoch_K"].iloc[-1]
        stoch_d = df["Stoch_D"].iloc[-1]
        st.metric("Stoch K", f"{stoch_k:.2f}", delta=f"D: {stoch_d:.2f}")

# Row 2: Bollinger Bands, ATR, Price vs Moving Averages
ind_row2_col1, ind_row2_col2, ind_row2_col3 = st.columns(3)

with ind_row2_col1:
    st.subheader("Bollinger Bands (20)")
    if "BB_Upper" in df.columns and "BB_Lower" in df.columns:
        if pd.notna(df["BB_Upper"].iloc[-1]) and pd.notna(df["BB_Lower"].iloc[-1]):
            upper = df["BB_Upper"].iloc[-1]
            middle = df["BB_Middle"].iloc[-1]
            lower = df["BB_Lower"].iloc[-1]
            current = df["close"].iloc[-1]
            
            if current > upper:
                position = "🔴 Above Upper (Overbought)"
            elif current < lower:
                position = "🟢 Below Lower (Oversold)"
            else:
                position = "🟡 Within Bands"
            
            st.metric("BB Status", position)

with ind_row2_col2:
    st.subheader("ATR (14)")
    if "ATR" in df.columns and pd.notna(df["ATR"].iloc[-1]):
        atr_current = df["ATR"].iloc[-1]
        atr_avg = df["ATR"].rolling(20).mean().iloc[-1]
        
        if pd.notna(atr_avg):
            atr_trend = "📈 Expanding" if atr_current > atr_avg else "📉 Contracting"
            st.metric("ATR", f"{atr_current:.4f}", delta=f"{atr_trend} (Avg: {atr_avg:.4f})")

with ind_row2_col3:
    st.subheader("Price vs MA")
    if "SMA" in df.columns and "EMA" in df.columns:
        if pd.notna(df["SMA"].iloc[-1]) and pd.notna(df["EMA"].iloc[-1]):
            sma_val = df["SMA"].iloc[-1]
            ema_val = df["EMA"].iloc[-1]
            price = df["close"].iloc[-1]
            
            if price > ema_val > sma_val:
                trend = "🟢 Strong Uptrend"
            elif price < ema_val < sma_val:
                trend = "🔴 Strong Downtrend"
            elif ema_val > sma_val:
                trend = "🟢 EMA > SMA (Bullish)"
            else:
                trend = "🔴 SMA > EMA (Bearish)"
            
            st.metric("Trend", trend)

st.markdown("---")
st.markdown(f"*Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S UTC')}*")
