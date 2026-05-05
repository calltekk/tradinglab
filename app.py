import pandas as pd
import streamlit as st

from src.data import download_price_data, get_latest_price
from src.indicators import add_moving_averages, add_rsi
from src.strategies import moving_average_strategy, rsi_mean_reversion_strategy
from src.backtest import run_backtest
from src.metrics import calculate_metrics
from src.momentum import rank_assets_by_momentum


def format_currency(value: float, currency: str = "£") -> str:
    return f"{currency}{value:,.2f}"


def format_currency_rounded(value: float, currency: str = "£") -> str:
    return f"{currency}{value:,.0f}"


def format_percent(value: float) -> str:
    return f"{value:.2%}"


def investment_decision(
    metrics: dict,
    results: pd.DataFrame,
    latest_signal: int,
) -> tuple[bool, list[str]]:
    """
    Practical trading decision.

    This is intentionally not too strict.
    It is designed to say INVEST when:
    - the current signal is active
    - the strategy made money historically
    - risk is not completely insane

    This does not guarantee profit.
    It is only a research filter.
    """

    reasons = []

    if latest_signal != 1:
        reasons.append("Latest signal is CASH / EXIT.")

    if metrics["total_return"] <= 0:
        reasons.append("Strategy did not make money overall.")

    if metrics["annual_return"] <= 0:
        reasons.append("Annual return is not positive.")

    if metrics["sharpe_ratio"] < 0.2:
        reasons.append("Sharpe ratio is too low (< 0.20).")

    if metrics["max_drawdown"] <= -0.60:
        reasons.append("Max drawdown is worse than -60%.")

    if metrics["annual_volatility"] >= 1.00:
        reasons.append("Annual volatility is extremely high (> 100%).")

    invest = len(reasons) == 0

    return invest, reasons


def display_market_price(ticker: str, latest_price: float | None) -> None:
    if latest_price is None:
        st.warning("Latest price unavailable.")
        return

    if ticker.endswith(".L") or ticker.startswith("^FTSE"):
        st.metric("Latest Market Price", f"{latest_price:,.2f} GBX")
        st.caption(
            f"Approx share price: £{latest_price / 100:,.2f}. "
            "UK shares on Yahoo Finance are usually shown in GBX/pence and may be delayed."
        )
    elif ticker.endswith("-USD"):
        st.metric("Latest Market Price", f"${latest_price:,.2f}")
        st.caption("Crypto prices such as BTC-USD are shown in USD.")
    else:
        st.metric("Latest Market Price", f"${latest_price:,.2f}")
        st.caption("US-listed assets are usually shown in USD.")


st.set_page_config(page_title="Trading Lab", layout="wide")

st.title("Trading Lab")
st.caption("A simple research tool for testing trading strategies before risking real money.")

with st.sidebar:
    st.header("Settings")

    mode = st.selectbox(
        "Mode",
        [
            "Single Asset Strategy",
            "Multi-Asset Momentum Ranking",
        ],
    )

    start_date = st.date_input("Start date", value=pd.to_datetime("2015-01-01"))
    end_date = st.date_input("End date", value=pd.Timestamp.today())

    st.caption(
        f"UK date range: {start_date.strftime('%d/%m/%Y')} → {end_date.strftime('%d/%m/%Y')}"
    )

    initial_capital = st.number_input(
        "Initial capital (£)",
        min_value=100,
        value=10_000,
        step=500,
    )

    transaction_cost = st.number_input(
        "Transaction cost",
        min_value=0.0,
        value=0.001,
        step=0.0005,
        format="%.4f",
        help="0.001 means 0.1% per trade.",
    )


if mode == "Single Asset Strategy":
    with st.sidebar:
        preset = st.selectbox(
            "Quick select",
            [
                "Custom",
                "Gold ETF (GLD)",
                "S&P 500 ETF (SPY)",
                "Nasdaq 100 ETF (QQQ)",
                "FTSE 100 Index (^FTSE)",
                "Bitcoin (BTC-USD)",
                "Ethereum (ETH-USD)",
                "BP (BP.L)",
                "HSBC (HSBA.L)",
                "AstraZeneca (AZN.L)",
            ],
        )

        if preset == "Custom":
            ticker = st.text_input("Ticker", "GLD").upper()
        else:
            ticker = preset.split("(")[-1].replace(")", "").upper()

        strategy = st.selectbox(
            "Strategy",
            [
                "Moving Average Crossover",
                "RSI Mean Reversion",
            ],
        )

        if strategy == "Moving Average Crossover":
            short_window = st.slider("Short MA", 5, 100, 20)
            long_window = st.slider("Long MA", 20, 300, 100)

        if strategy == "RSI Mean Reversion":
            rsi_window = st.slider("RSI window", 5, 50, 14)
            oversold = st.slider("Oversold", 5, 45, 30)
            exit_level = st.slider("Exit level", 40, 80, 55)

    latest_price = get_latest_price(ticker)
    display_market_price(ticker, latest_price)

    df = download_price_data(
        ticker=ticker,
        start=str(start_date),
        end=str(end_date),
    )

    if df.empty:
        st.error("No data found. Try BTC-USD for Bitcoin, ETH-USD for Ethereum, or BP.L for UK shares.")
        st.stop()

    if strategy == "Moving Average Crossover":
        df = add_moving_averages(df, short_window, long_window)
        df = moving_average_strategy(df, short_window, long_window)

        strategy_explanation = f"""
        This strategy compares two moving averages:

        - Short moving average: {short_window} days
        - Long moving average: {long_window} days

        It buys when the short moving average is above the long moving average.
        It exits when the short moving average falls below the long moving average.
        """

    elif strategy == "RSI Mean Reversion":
        df = add_rsi(df, rsi_window)
        df = rsi_mean_reversion_strategy(
            df,
            rsi_col=f"rsi_{rsi_window}",
            oversold=oversold,
            exit_level=exit_level,
        )

        strategy_explanation = f"""
        This strategy uses RSI, which measures whether an asset may be overbought or oversold.

        - Buy when RSI falls below {oversold}
        - Exit when RSI rises above {exit_level}

        It tries to buy weakness and sell after recovery.
        """

    results = run_backtest(
        df=df,
        initial_capital=initial_capital,
        transaction_cost=transaction_cost,
    )

    metrics = calculate_metrics(results)

    latest_signal = int(results["signal"].iloc[-1])
    final_value = results["strategy_equity"].iloc[-1]

    invest, reasons = investment_decision(metrics, results, latest_signal)

    st.subheader("What should I do?")

    if invest:
        st.success(f"{ticker}: INVEST — current signal is active and risk/reward is acceptable.")
    else:
        st.error(f"{ticker}: DON'T INVEST — current setup is not strong enough.")

        with st.expander("Why?"):
            for reason in reasons:
                st.write(f"- {reason}")

    st.warning(
        "This is not financial advice. This app is a backtesting/research tool only. "
        "Use small position sizes and never risk money you cannot afford to lose."
    )

    st.info(strategy_explanation)

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric("Portfolio Value", format_currency_rounded(final_value))
    c2.metric("Total Return", format_percent(metrics["total_return"]))
    c3.metric("Annual Return", format_percent(metrics["annual_return"]))
    c4.metric("Volatility", format_percent(metrics["annual_volatility"]))
    c5.metric("Sharpe", f"{metrics['sharpe_ratio']:.2f}")
    c6.metric("Max Drawdown", format_percent(metrics["max_drawdown"]))

    st.subheader("TLDR")

    st.write(
        f"""
        Starting with **{format_currency_rounded(initial_capital)}**, this strategy would have ended at
        approximately **{format_currency_rounded(final_value)}**.

        The worst historical drop was **{format_percent(metrics["max_drawdown"])}**.

        It made **{metrics["trades"]} trades** over the selected period.
        """
    )

    st.subheader("For the finance bros")

    st.markdown(
        """
        - **Total Return**: how much the strategy made overall.
        - **Annual Return**: average yearly growth.
        - **Volatility**: how rough the ride was.
        - **Sharpe**: return compared with risk. Above 1 is strong, 0.5–1 is decent, below 0.5 is weak.
        - **Max Drawdown**: the worst fall from a previous high.
        - **Trades**: how many buy/sell changes happened.
        """
    )

    st.subheader("Equity Curve")
    st.caption("This compares your strategy against simply buying and holding the asset.")
    st.line_chart(results[["strategy_equity", "buy_hold_equity"]])

    st.subheader("Drawdown")
    st.caption("This shows the worst dips from previous highs. Lower is worse.")
    st.line_chart(results["drawdown"])

    st.subheader("Price and Indicators")

    if strategy == "Moving Average Crossover":
        st.line_chart(
            results[
                [
                    "close",
                    f"ma_{short_window}",
                    f"ma_{long_window}",
                ]
            ]
        )

    elif strategy == "RSI Mean Reversion":
        st.line_chart(results["close"])
        st.line_chart(results[f"rsi_{rsi_window}"])

    st.subheader("Recent Data")
    recent = results.tail(30).copy()
    recent.index = recent.index.strftime("%d/%m/%Y")
    st.dataframe(recent, use_container_width=True)


elif mode == "Multi-Asset Momentum Ranking":
    with st.sidebar:
        tickers_input = st.text_area(
            "Assets",
            value="SPY, QQQ, IWM, TLT, GLD, BTC-USD, ETH-USD, ^FTSE",
        )

        momentum_days = st.slider("Momentum lookback days", 30, 252, 126)

    tickers = [
        ticker.strip().upper()
        for ticker in tickers_input.split(",")
        if ticker.strip()
    ]

    st.subheader("Top Asset Right Now")

    ranking = rank_assets_by_momentum(
        tickers=tickers,
        start=str(start_date),
        end=str(end_date),
        lookback_days=momentum_days,
    )

    if ranking.empty:
        st.error("No ranking data found.")
        st.stop()

    best_asset = ranking.iloc[0]

    st.success(
        f"Best asset by {momentum_days}-day momentum: "
        f"{best_asset['ticker']} ({best_asset['momentum']:.2%})"
    )

    if best_asset["momentum"] > 0:
        st.success("Decision: INVEST in the top-ranked asset.")
    else:
        st.error("Decision: STAY IN CASH. No asset has positive momentum.")

    st.warning(
        "This is not financial advice. This app is a backtesting/research tool only."
    )

    st.info(
        """
        This ranks assets by recent performance.

        Instead of asking whether one asset is good, this compares several assets
        and highlights the strongest one.

        This is not a prediction. It is a momentum ranking tool.
        """
    )

    display_ranking = ranking.copy()

    def format_price(row):
        ticker_value = row["ticker"]
        price = row["latest_price"]

        if ticker_value.endswith(".L") or ticker_value.startswith("^FTSE"):
            return f"{price:,.2f} GBX"
        elif ticker_value.endswith("-USD"):
            return f"${price:,.2f}"
        else:
            return f"${price:,.2f}"

    display_ranking["latest_price"] = display_ranking.apply(format_price, axis=1)
    display_ranking["momentum"] = display_ranking["momentum"].map(lambda x: f"{x:.2%}")

    st.dataframe(display_ranking, use_container_width=True)

    st.subheader("Momentum Chart")
    chart_data = ranking.set_index("ticker")["momentum"]
    st.bar_chart(chart_data)

    st.subheader("How to use this")

    st.markdown(
        """
        - Look at the **rank 1 asset**.
        - Check whether its momentum is positive.
        - If positive, the strategy favours that asset.
        - If negative, the strategy favours cash.
        - Re-check weekly or monthly rather than every hour.
        """
    )