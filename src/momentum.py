import pandas as pd

from src.data import download_price_data


def rank_assets_by_momentum(
    tickers: list[str],
    start: str,
    end: str,
    lookback_days: int = 126,
) -> pd.DataFrame:
    rows = []

    for ticker in tickers:
        df = download_price_data(ticker=ticker, start=start, end=end)

        if df.empty or len(df) <= lookback_days:
            continue

        latest_price = df["close"].iloc[-1]
        old_price = df["close"].iloc[-lookback_days]

        momentum = latest_price / old_price - 1

        rows.append(
            {
                "ticker": ticker,
                "latest_price": latest_price,
                "momentum": momentum,
            }
        )

    ranking = pd.DataFrame(rows)

    if ranking.empty:
        return ranking

    ranking = ranking.sort_values("momentum", ascending=False).reset_index(drop=True)

    ranking.insert(0, "rank", ranking.index + 1)

    return ranking