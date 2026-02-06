from sklearn.ensemble import RandomForestClassifier

def train_model(df):
    df = df.copy()

    df["return"] = df["close"].pct_change()
    df["direction"] = (df["return"] > 0).astype(int)

    # ✅ Only use features that actually exist
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
