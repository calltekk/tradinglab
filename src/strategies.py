import pandas as pd


def moving_average_strategy(
    df: pd.DataFrame,
    short_window: int,
    long_window: int,
) -> pd.DataFrame:
    df = df.copy()

    short_col = f"ma_{short_window}"
    long_col = f"ma_{long_window}"

    df["signal"] = 0
    df.loc[df[short_col] > df[long_col], "signal"] = 1

    return df


def rsi_mean_reversion_strategy(
    df: pd.DataFrame,
    rsi_col: str,
    oversold: int = 30,
    exit_level: int = 55,
) -> pd.DataFrame:
    df = df.copy()

    in_position = False
    signals = []

    for _, row in df.iterrows():
        rsi = row[rsi_col]

        if pd.isna(rsi):
            signals.append(0)
            continue

        if not in_position and rsi < oversold:
            in_position = True

        elif in_position and rsi > exit_level:
            in_position = False

        signals.append(1 if in_position else 0)

    df["signal"] = signals

    return df