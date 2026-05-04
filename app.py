import pandas as pd
import streamlit as st

from src.data import download_price_data
from src.indicators import add_moving_averages, add_rsi
from src.strategies import moving_average_strategy, rsi_mean_reversion_strategy
from src.backtest import run_backtest
from src.metrics import calculate_metrics


st.set_page_config(page_title="Trading Lab", layout="wide")

st.title("Trading Lab")
st.caption("Research strategies before risking real money.")


with st.sidebar:
    st.header("Settings")

    ticker = st.text_input("Ticker", "SPY").upper()

    start_date = st.date_input("Start date", value=pd.to_datetime("2015-01-01"))
    end_date = st.date_input("End date", value=pd.Timestamp.today())

    strategy = st.selectbox(
        "Strategy",
        [
            "Moving Average Crossover",
            "RSI Mean Reversion",
        ],
    )

    initial_capital = st.number_input(
        "Initial capital",
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
    )

    if strategy == "Moving Average Crossover":
        short_window = st.slider("Short MA", 5, 100, 20)
        long_window = st.slider("Long MA", 20, 300, 100)

    if strategy == "RSI Mean Reversion":
        rsi_window = st.slider("RSI window", 5, 50, 14)
        oversold = st.slider("Oversold", 5, 45, 30)
        exit_level = st.slider("Exit level", 40, 80, 55)


df = download_price_data(
    ticker=ticker,
    start=str(start_date),
    end=str(end_date),
)

if df.empty:
    st.error("No data found.")
    st.stop()


if strategy == "Moving Average Crossover":
    df = add_moving_averages(df, short_window, long_window)
    df = moving_average_strategy(df, short_window, long_window)

elif strategy == "RSI Mean Reversion":
    df = add_rsi(df, rsi_window)
    df = rsi_mean_reversion_strategy(
        df,
        rsi_col=f"rsi_{rsi_window}",
        oversold=oversold,
        exit_level=exit_level,
    )


results = run_backtest(
    df=df,
    initial_capital=initial_capital,
    transaction_cost=transaction_cost,
)

metrics = calculate_metrics(results)


c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric("Total Return", f"{metrics['total_return']:.2%}")
c2.metric("Annual Return", f"{metrics['annual_return']:.2%}")
c3.metric("Volatility", f"{metrics['annual_volatility']:.2%}")
c4.metric("Sharpe", f"{metrics['sharpe_ratio']:.2f}")
c5.metric("Max Drawdown", f"{metrics['max_drawdown']:.2%}")
c6.metric("Trades", metrics["trades"])


latest_signal = int(results["signal"].iloc[-1])

st.subheader("Latest Signal")

if latest_signal == 1:
    st.success(f"{ticker}: BUY / HOLD")
else:
    st.warning(f"{ticker}: CASH / EXIT")


st.subheader("Equity Curve")
st.line_chart(results[["strategy_equity", "buy_hold_equity"]])


st.subheader("Drawdown")
st.line_chart(results["drawdown"])


st.subheader("Price")

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
st.dataframe(results.tail(30), use_container_width=True)