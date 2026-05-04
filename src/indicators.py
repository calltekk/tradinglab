import pandas as pd


def add_moving_averages(
    df: pd.DataFrame,
    short_window: int,
    long_window: int,
) -> pd.DataFrame:
    df = df.copy()

    df[f"ma_{short_window}"] = df["close"].rolling(short_window).mean()
    df[f"ma_{long_window}"] = df["close"].rolling(long_window).mean()

    return df


def add_rsi(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    df = df.copy()

    delta = df["close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()

    rs = avg_gain / avg_loss

    df[f"rsi_{window}"] = 100 - (100 / (1 + rs))

    return df