import pandas as pd
import numpy as np

class RiskManager:
    def __init__(self, account_balance=1000, max_risk_per_trade=0.02):
        self.account_balance = account_balance
        self.max_risk_per_trade = max_risk_per_trade  # 2% risk per trade
    
    def calculate_position_size(self, entry, stop_loss):
        """Calculate proper position size based on risk"""
        if entry == stop_loss:
            return 0
        risk_amount = self.account_balance * self.max_risk_per_trade
        pip_distance = abs(entry - stop_loss)
        position_size = risk_amount / pip_distance if pip_distance > 0 else 0
        return max(0.01, position_size)  # Minimum 0.01 lot
    
    def get_dynamic_stop_loss(self, entry, atr):
        """Dynamic SL based on ATR"""
        return entry - (atr * 2)  # 2x ATR below entry
    
    def get_take_profit(self, entry, stop_loss):
        """2:1 Risk/Reward ratio"""
        if stop_loss == entry:
            return None
        risk = abs(entry - stop_loss)
        return entry + (risk * 2)

def get_confirmation_score(df):
    """Score trade setup based on indicator confluence"""
    if len(df) < 2:
        return 0
    
    confirmations = 0
    max_confirmations = 6
    
    try:
        # 1. RSI confirmation
        if 'RSI' in df.columns:
            rsi_val = df['RSI'].iloc[-1]
            if pd.notna(rsi_val):
                if rsi_val > 70 or rsi_val < 30:
                    confirmations += 1
        
        # 2. EMA/SMA alignment
        if 'EMA' in df.columns and 'SMA' in df.columns:
            if pd.notna(df['EMA'].iloc[-1]) and pd.notna(df['SMA'].iloc[-1]):
                if df['EMA'].iloc[-1] > df['SMA'].iloc[-1]:
                    confirmations += 1
        
        # 3. Price above close
        if len(df) > 1:
            if df['close'].iloc[-1] > df['close'].iloc[-2]:
                confirmations += 0.5
        
        # 4. ATR expansion
        if 'ATR' in df.columns:
            atr_current = df['ATR'].iloc[-1]
            atr_mean = df['ATR'].rolling(20).mean().iloc[-1]
            if pd.notna(atr_current) and pd.notna(atr_mean):
                if atr_current > atr_mean:
                    confirmations += 0.5
        
        # 5. Volatility confirmation (High-Low range)
        if len(df) > 0:
            current_range = df['high'].iloc[-1] - df['low'].iloc[-1]
            avg_range = (df['high'] - df['low']).rolling(20).mean().iloc[-1]
            if current_range > avg_range * 0.9:
                confirmations += 1
        
        # 6. Close near high (bullish) or near low (bearish)
        if len(df) > 0:
            high = df['high'].iloc[-1]
            low = df['low'].iloc[-1]
            close = df['close'].iloc[-1]
            position = (close - low) / (high - low) if (high - low) > 0 else 0.5
            if position > 0.6 or position < 0.4:
                confirmations += 1
    
    except Exception as e:
        print(f"Error calculating confirmation score: {e}")
        return 0
    
    confidence = (confirmations / max_confirmations) * 100
    return round(confidence, 2)

def trade_setup(price, atr, bias, df=None, min_confidence=50):
    """
    Generate trade setup with confirmation scoring
    
    Args:
        price: Current price
        atr: ATR value
        bias: "Bullish", "Bearish", or "Neutral"
        df: DataFrame for confirmation scoring (optional)
        min_confidence: Minimum confidence threshold (default 50%)
    
    Returns:
        dict with entry, sl, tp, confidence, and status
    """
    
    # Calculate confidence if dataframe provided
    confidence = 0
    if df is not None:
        confidence = get_confirmation_score(df)
    
    # Check if confidence threshold met
    if confidence < min_confidence and df is not None:
        return {
            "entry": None,
            "sl": None,
            "tp": None,
            "confidence": confidence,
            "status": "WAIT",
            "reason": f"Low confidence ({confidence}% < {min_confidence}%)"
        }
    
    # Generate trade setup
    if bias == "Bullish":
        entry = price
        sl = price - 1.2 * atr
        tp = price + 2.5 * atr
        status = "BUY"
    elif bias == "Bearish":
        entry = price
        sl = price + 1.2 * atr
        tp = price - 2.5 * atr
        status = "SELL"
    else:
        entry = sl = tp = None
        status = "NEUTRAL"
        confidence = 0
    
    return {
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "confidence": confidence if df is not None else 0,
        "status": status,
        "reason": f"{status} signal with {confidence}% confidence"
    }
