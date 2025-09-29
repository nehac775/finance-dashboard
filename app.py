"""
Financial Dashboard (my version)

Why I built it
--------------
I wanted a single page where I can search stock tickers, 
see their history, plot candlesticks, and compare multiple tickers.
This gave me a good chance to practice Streamlit, yfinance, and Plotly.

Challenges & notes
------------------
- yfinance returned MultiIndex columns when fetching multiple tickers,
  which broke my early attempts → I fixed it by fetching each ticker individually.
- Candlestick + volume overlapped at first → solved with Plotly subplots.
- Normalization for comparison was tricky but makes charts way more readable.
- TODO: Add RSI/EMA indicators for technical analysis.
- TODO: Save a watchlist so I don’t have to type tickers every time.
"""

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime as dt

# --- Streamlit config ---
st.set_page_config(page_title="Financial Dashboard", page_icon="📊", layout="wide")
st.title("📊 Financial Dashboard")
st.caption("Search tickers, view historical data, candlesticks, moving averages, compare multiple stocks, and export CSV.")

# --- Sidebar controls ---
with st.sidebar:
    st.header("Search")
    # User can type multiple tickers separated by commas
    tickers_raw = st.text_input("Tickers (comma separated)", placeholder="AAPL, MSFT, NVDA")

    # Default: last 1 year
    today = dt.date.today()
    default_start = today - dt.timedelta(days=365)

    start_date = st.date_input("Start date", default_start)
    end_date = st.date_input("End date", today)

    st.divider()
    st.header("Indicators")
    sma_short = st.number_input("SMA (short)", min_value=5, max_value=100, value=20, step=1)
    sma_mid   = st.number_input("SMA (mid)",   min_value=10, max_value=250, value=50, step=1)
    sma_long  = st.number_input("SMA (long)",  min_value=20, max_value=400, value=200, step=5)

    show_volume = st.checkbox("Show volume (candlestick)", value=True)

    fetch_btn = st.button("Fetch data")

# --- Helpers ---
@st.cache_data(ttl=1800)  # cache for 30 min
def fetch_history(ticker: str, start: dt.date, end: dt.date) -> pd.DataFrame:
    """Download history for one ticker. 
    NOTE: Fetching per ticker avoids yfinance's MultiIndex weirdness."""
    try:
        df = yf.Ticker(ticker).history(start=start, end=end)
        if df.empty:
            return pd.DataFrame()
        df = df.reset_index()
        df["Ticker"] = ticker
        return df
    except Exception:
        return pd.DataFrame()

def add_sma(df: pd.DataFrame, windows: list[int]) -> pd.DataFrame:
    """Add SMA columns for each ticker separately."""
    out = df.copy()
    for w in windows:
        out[f"SMA_{w}"] = out.groupby("Ticker")["Close"].transform(lambda s: s.rolling(w).mean())
    return out

def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize Close so that all tickers start at 100 (for comparison)."""
    out = df.copy()
    def norm(s):
        first = s.iloc[0] if not s.empty else None
        return (s / first * 100) if first else None
    out["CloseNorm"] = out.groupby("Ticker")["Close"].transform(norm)
    return out

def clean_tickers(s: str) -> list[str]:
    """Turn comma/space separated string into list of tickers."""
    tickers = [t.strip().upper() for t in s.replace(" ", ",").split(",") if t.strip()]
    return tickers[:8]  # safety: limit to 8 tickers

# --- Main logic ---
if fetch_btn:
    tickers = clean_tickers(tickers_raw)

    if not tickers:
        st.warning("⚠ Enter at least one ticker (example: AAPL, MSFT).")
        st.stop()

    dfs, missing = [], []
    for t in tickers:
        df_one = fetch_history(t, start_date, end_date)
        if df_one.empty:
            missing.append(t)
        else:
            dfs.append(df_one)

    if missing:
        st.warning(f"No data for: {', '.join(missing)}")

    if not dfs:
        st.error("No valid tickers fetched. Try different ones.")
        st.stop()

    df = pd.concat(dfs).sort_values(["Ticker", "Date"])
    df = add_sma(df, [sma_short, sma_mid, sma_long])

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Candlestick", "📈 Comparison", "📥 Export"])

    # --- Candlestick view ---
    with tab1:
        choice = st.selectbox("Choose ticker", tickers)
        df_one = df[df["Ticker"] == choice]

        if df_one.empty:
            st.info("No data for this ticker.")
        else:
            rows = 2 if show_volume else 1
            fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.05)

            # Candlestick chart
            fig.add_trace(go.Candlestick(
                x=df_one["Date"],
                open=df_one["Open"],
                high=df_one["High"],
                low=df_one["Low"],
                close=df_one["Close"],
                name=choice
            ), row=1, col=1)

            # Add SMAs
            for w in [sma_short, sma_mid, sma_long]:
                fig.add_trace(go.Scatter(
                    x=df_one["Date"], y=df_one[f"SMA_{w}"], mode="lines", name=f"SMA {w}"
                ), row=1, col=1)

            # Volume (optional)
            if show_volume:
                fig.add_trace(go.Bar(
                    x=df_one["Date"], y=df_one["Volume"], name="Volume", opacity=0.5
                ), row=2, col=1)

            fig.update_layout(
                title=f"{choice} Candlestick + SMAs",
                xaxis_rangeslider_visible=False,
                height=700 if show_volume else 480
            )
            st.plotly_chart(fig, use_container_width=True)

    # --- Comparison view ---
    with tab2:
        df_norm = normalize(df)
        fig_cmp = px.line(
            df_norm, x="Date", y="CloseNorm", color="Ticker",
            title="Normalized comparison (100 = first day)"
        )
        st.plotly_chart(fig_cmp, use_container_width=True)

        # Quick return summary
        st.subheader("Returns (%)")
        returns = df.groupby("Ticker").apply(lambda g: (g["Close"].iloc[-1] / g["Close"].iloc[0] - 1) * 100)
        st.dataframe(returns.reset_index(name="Return %"))

    # --- Export view ---
    with tab3:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, f"stocks_{start_date}_{end_date}.csv", "text/csv")
else:
    st.info("👉 Enter tickers in the sidebar and click Fetch.")

