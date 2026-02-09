import pandas as pd
import numpy as np
from inference.trade_logic import get_confirmation_score

def backtest_strategy(df, initial_balance=1000, risk_per_trade=0.02, min_confidence=50):
    """
    Simple backtest of trading strategy
    
    Args:
        df: DataFrame with OHLC data
        initial_balance: Starting capital
        risk_per_trade: Risk percentage per trade
        min_confidence: Minimum confidence threshold
    
    Returns:
        dict with performance metrics
    """
    balance = initial_balance
    position = False
    entry_price = 0
    trades = []
    
    for i in range(50, len(df)):
        current_df = df.iloc[:i+1].copy()
        close = df['close'].iloc[i]
        high = df['high'].iloc[i]
        low = df['low'].iloc[i]
        atr = df['ATR'].iloc[i] if 'ATR' in df.columns else (high - low)
        
        confidence = get_confirmation_score(current_df)
        
        # Entry signal
        if not position and confidence > min_confidence:
            position = True
            entry_price = close
            entry_idx = i
            trade_start = {
                "index": i,
                "entry_price": entry_price,
                "confidence": confidence,
                "date": df.index[i] if hasattr(df.index, '__getitem__') else i
            }
        
        # Exit signal
        if position:
            profit_pct = (close - entry_price) / entry_price if entry_price > 0 else 0
            
            # Take profit at 2% or stop loss at 1%
            if profit_pct > 0.02:
                profit = (close - entry_price) * 100
                balance += profit
                trades.append({
                    "entry": entry_price,
                    "exit": close,
                    "profit": profit,
                    "return_pct": profit_pct * 100,
                    "bars_held": i - entry_idx,
                    "status": "TP_HIT"
                })
                position = False
            elif profit_pct < -0.01:
                loss = (entry_price - close) * 100
                balance -= loss
                trades.append({
                    "entry": entry_price,
                    "exit": close,
                    "profit": -loss,
                    "return_pct": profit_pct * 100,
                    "bars_held": i - entry_idx,
                    "status": "SL_HIT"
                })
                position = False
    
    # Calculate metrics
    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t['profit'] > 0)
    losing_trades = sum(1 for t in trades if t['profit'] < 0)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    avg_profit = sum(t['profit'] for t in trades) / total_trades if total_trades > 0 else 0
    
    return {
        "final_balance": round(balance, 2),
        "initial_balance": initial_balance,
        "total_profit": round(balance - initial_balance, 2),
        "return_pct": round(((balance - initial_balance) / initial_balance * 100), 2),
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": round(win_rate, 2),
        "avg_profit_per_trade": round(avg_profit, 2),
        "trades": trades
    }
