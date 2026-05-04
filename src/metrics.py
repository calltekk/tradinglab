import numpy as np
import pandas as pd


def calculate_metrics(df: pd.DataFrame) -> dict:
    total_return = df["strategy_equity"].iloc[-1] / df["strategy_equity"].iloc[0] - 1

    years = (df.index[-1] - df.index[0]).days / 365.25

    if years <= 0:
        years = 1 / 365.25

    annual_return = (1 + total_return) ** (1 / years) - 1

    annual_volatility = df["strategy_return"].std() * np.sqrt(252)

    if annual_volatility == 0:
        sharpe_ratio = 0
    else:
        sharpe_ratio = (df["strategy_return"].mean() * 252) / annual_volatility

    max_drawdown = df["drawdown"].min()

    trades = int(df["trade"].sum())

    return {
        "total_return": total_return,
        "annual_return": annual_return,
        "annual_volatility": annual_volatility,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown,
        "trades": trades,
    }