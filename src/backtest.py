import pandas as pd


def run_backtest(
    df: pd.DataFrame,
    initial_capital: float = 10_000,
    transaction_cost: float = 0.001,
) -> pd.DataFrame:
    df = df.copy().dropna()

    df["position"] = df["signal"].shift(1).fillna(0)

    df["market_return"] = df["close"].pct_change().fillna(0)

    df["trade"] = df["position"].diff().abs().fillna(0)

    df["strategy_return"] = (
        df["position"] * df["market_return"]
        - df["trade"] * transaction_cost
    )

    df["strategy_equity"] = initial_capital * (1 + df["strategy_return"]).cumprod()

    df["buy_hold_equity"] = initial_capital * (1 + df["market_return"]).cumprod()

    df["peak"] = df["strategy_equity"].cummax()
    df["drawdown"] = df["strategy_equity"] / df["peak"] - 1

    return df