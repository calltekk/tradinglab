import pandas as pd
import yfinance as yf


def download_price_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    df = yf.download(
        ticker,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
    )

    if df.empty:
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )

    required_columns = ["open", "high", "low", "close", "volume"]

    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]

    if missing_columns:
        return pd.DataFrame()

    return df[required_columns].dropna()


def get_latest_price(ticker: str):
    asset = yf.Ticker(ticker)
    history = asset.history(period="1d")

    if history.empty:
        return None

    return float(history["Close"].iloc[-1])