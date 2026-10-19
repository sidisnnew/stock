from dataclasses import dataclass

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error


@dataclass
class ForecastResult:
    predicted_close: float
    mae: float
    rmse: float
    baseline_mae: float
    train_rows: int
    test_rows: int


def forecast_next_close(history):
    if "Close" not in history.columns:
        raise ValueError("Price data needs a 'Close' column.")

    close = pd.to_numeric(history["Close"], errors="coerce").dropna().sort_index()
    if len(close) < 60:
        raise ValueError("Please choose at least 6 months of daily data (60+ rows).")

    frame = pd.DataFrame(index=close.index)
    frame["close"] = close
    frame["return_1d"] = close.pct_change()
    frame["ma_5"] = close.rolling(5).mean()
    frame["ma_20"] = close.rolling(20).mean()
    frame["target_next_close"] = close.shift(-1)
    features = ["close", "return_1d", "ma_5", "ma_20"]

    # The final row has today's features but no known next-day label.
    labeled = frame.dropna(subset=features + ["target_next_close"])
    current_features = frame[features].dropna().iloc[[-1]]
    if len(labeled) < 40 or current_features.empty:
        raise ValueError("Not enough clean daily rows to build the model.")

    split = int(len(labeled) * 0.8)
    if split < 20 or len(labeled) - split < 10:
        raise ValueError("Not enough rows for a reliable time-ordered holdout.")

    x = labeled[features]
    y = labeled["target_next_close"]
    x_train, x_test = x.iloc[:split], x.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    evaluation_model = LinearRegression().fit(x_train, y_train)
    test_prediction = evaluation_model.predict(x_test)
    mae = mean_absolute_error(y_test, test_prediction)
    rmse = mean_squared_error(y_test, test_prediction) ** 0.5

    # Simple baseline: assume tomorrow's close equals today's close.
    baseline_prediction = labeled["close"].iloc[split:].to_numpy()
    baseline_mae = mean_absolute_error(y_test, baseline_prediction)

    final_model = LinearRegression().fit(x, y)
    predicted_close = float(final_model.predict(current_features)[0])
    
    return ForecastResult(
        predicted_close=predicted_close,
        mae=float(mae),
        rmse=float(rmse),
        baseline_mae=float(baseline_mae),
        train_rows=len(x_train),
        test_rows=len(x_test),
    )
