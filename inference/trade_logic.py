def trade_setup(price, atr, bias):
    if bias == "Bullish":
        entry = price
        sl = price - 1.2 * atr
        tp = price + 2.5 * atr
    elif bias == "Bearish":
        entry = price
        sl = price + 1.2 * atr
        tp = price - 2.5 * atr
    else:
        entry = sl = tp = None

    return entry, sl, tp
