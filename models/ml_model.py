from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
import pandas as pd
import numpy as np

def prepare_features(df):
    """Prepare and scale features"""
    # Use available features
    feature_cols = ['open', 'high', 'low', 'close']
    if 'volume' in df.columns:
        feature_cols.append('volume')
    if 'SMA' in df.columns:
        feature_cols.append('SMA')
    if 'EMA' in df.columns:
        feature_cols.append('EMA')
    if 'RSI' in df.columns:
        feature_cols.append('RSI')
    if 'ATR' in df.columns:
        feature_cols.append('ATR')
    
    X = df[feature_cols].dropna().copy()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    return X_scaled, scaler, feature_cols

def train_model(df):
    """Train improved ML model with proper scaling"""
    df = df.copy()

    # Create target variable
    df["return"] = df["close"].pct_change()
    df["direction"] = (df["return"] > 0).astype(int)

    # Prepare features
    try:
        X_scaled, scaler, feature_cols = prepare_features(df)
    except:
        # Fallback to original method if features missing
        base_features = ["open", "high", "low", "close"]
        if "volume" in df.columns:
            base_features.append("volume")
        df = df.dropna()
        X = df[base_features]
        y = df["direction"]
        
        model = RandomForestClassifier(
            n_estimators=300,
            max_depth=7,
            min_samples_leaf=5,
            random_state=42
        )
        model.fit(X, y)
        return model, base_features

    # Remove NaN from target
    valid_idx = ~np.isnan(X_scaled).any(axis=1)
    X_scaled = X_scaled[valid_idx]
    y = df["direction"].iloc[:len(X_scaled)].values
    
    if len(y) == 0:
        raise ValueError("No valid data for training")

    # Train with time-series aware model
    model = GradientBoostingClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        random_state=42
    )

    model.fit(X_scaled, y)

    return model, feature_cols

def evaluate_model(df, model, feature_cols, test_size=0.2):
    """Evaluate model with time series split"""
    try:
        X_scaled, scaler, _ = prepare_features(df)
    except:
        return None
    
    split_idx = int(len(X_scaled) * (1 - test_size))
    X_train, X_test = X_scaled[:split_idx], X_scaled[split_idx:]
    
    df_clean = df.dropna()
    y = (df_clean["close"].pct_change() > 0).astype(int).values
    y_train, y_test = y[:split_idx], y[split_idx:len(X_test)]
    
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    
    return {"train_score": train_score, "test_score": test_score}
