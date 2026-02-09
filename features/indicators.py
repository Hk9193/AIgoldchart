import pandas as pd
import numpy as np

def SMA(series, period=14):
    return series.rolling(period).mean()

def EMA(series, period=14):
    return series.ewm(span=period).mean()

def RSI(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def ATR(df, period=14):
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()

    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.rolling(period).mean()

# ========== NEW INDICATORS ==========

def MACD(close, fast=12, slow=26, signal=9):
    """MACD - Momentum indicator"""
    ema_fast = close.ewm(span=fast).mean()
    ema_slow = close.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def BOLLINGER_BANDS(close, period=20, std_dev=2):
    """Bollinger Bands for volatility"""
    sma = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, sma, lower_band

def STOCHASTIC_RSI(close, period=14, smooth_k=3, smooth_d=3):
    """Stochastic RSI - more sensitive than regular RSI"""
    rsi = RSI(close, period)
    min_rsi = rsi.rolling(window=period).min()
    max_rsi = rsi.rolling(window=period).max()
    
    stoch_rsi = (rsi - min_rsi) / (max_rsi - min_rsi)
    k_line = stoch_rsi.rolling(window=smooth_k).mean()
    d_line = k_line.rolling(window=smooth_d).mean()
    return k_line, d_line

def VWAP(high, low, close, volume):
    """Volume Weighted Average Price"""
    hlc3 = (high + low + close) / 3
    vwap = (hlc3 * volume).rolling(20).sum() / volume.rolling(20).sum()
    return vwap
