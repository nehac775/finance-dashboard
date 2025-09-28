import streamlit as st
import pandas as pd
from datetime import date, timedelta
from src.finance import fetch_history, add_indicators, fetch_info
from src.visualizer import line_price_chart, candlestick_chart, multi_line_chart

st.set_page_config(page_title="Finance Dashboard", page_icon="📈", layout="wide")

st.title("📈 Finance Dashboard")
st.caption("Search tickers (e.g., AAPL, MSFT, TSLA). View prices, indicators, and compare multiple stocks.")

# Sidebar inputs
st.sidebar.header("Query")
tickers = st.sidebar.text_input("Ticker(s) (comma-separated)", value="AAPL").upper()
tickers_list = [t.strip() for t in tickers.split(",") if t.strip()]

today = date.today()
default_start = today - timedelta(days=365)
col_s1, col_s2 = st.sidebar.columns(2)
start_date = col_s1.date_input("Start", value=default_start, max_value=today)
end_date = col_s2.date_input("End", value=today, max_value=today)

st.sidebar.header("Indicators")
ma_short = st.sidebar.number_input("Short MA (days)", min_value=1, value=7, step=1)
ma_long = st.sidebar.number_input("Long MA (days)", min_value=2, value=30, step=1)

chart_type = st.sidebar.selectbox("Chart type", ["Line", "Candlestick"])
run = st.sidebar.button("Run", type="primary")

if run:
    if not tickers_list:
        st.error("Enter at least one ticker (e.g., AAPL).")
        st.stop()

    tabs = st.tabs(["Overview"] + tickers_list + (["Compare"] if len(tickers_list) > 1 else []))

    # Overview tab
    with tabs[0]:
        st.subheader("Overview")
        info_rows = []
        for t in tickers_list[:5]:  # limit for speed
            info = fetch_info(t)
            if info:
                info_rows.append({
                    "Ticker": t,
                    "Name": info.get("shortName") or info.get("longName"),
                    "Price": info.get("currentPrice"),
                    "Market Cap": info.get("marketCap"),
                    "PE Ratio (TTM)": info.get("trailingPE"),
                    "52W High": info.get("fiftyTwoWeekHigh"),
                    "52W Low": info.get("fiftyTwoWeekLow"),
                    "Sector": info.get("sector"),
                    "Industry": info.get("industry"),
                })
        if info_rows:
            df_info = pd.DataFrame(info_rows)
            st.dataframe(df_info, use_container_width=True, hide_index=True)
        else:
            st.write("No overview data available.")

    # Per-ticker tabs
    for i, t in enumerate(tickers_list, start=1):
        with tabs[i]:
            st.subheader(f"{t}")
            df = fetch_history(t, start=start_date, end=end_date)
            if df.empty:
                st.warning(f"No data for {t} in the selected range.")
                continue

            df = add_indicators(df, ma_short=ma_short, ma_long=ma_long)

            c1, c2 = st.columns([3, 1])
            with c1:
                if chart_type == "Line":
                    st.plotly_chart(line_price_chart(df, t, ma_short, ma_long), use_container_width=True)
                else:
                    st.plotly_chart(candlestick_chart(df, t), use_container_width=True)
            with c2:
                st.markdown("**Latest**")
                last = df.iloc[-1]
                st.metric("Close", f"{last['Close']:.2f}")
                st.metric(f"MA {ma_short}", f"{last[f'MA_{ma_short}']:.2f}")
                st.metric(f"MA {ma_long}", f"{last[f'MA_{ma_long}']:.2f}")

            st.download_button(
                "Download CSV",
                df.to_csv(index=True).encode("utf-8"),
                file_name=f"{t}_history.csv",
                mime="text/csv",
                use_container_width=True,
            )

    # Compare tab
    if len(tickers_list) > 1:
        with tabs[-1]:
            st.subheader("Compare")
            combo = {}
            for t in tickers_list:
                df = fetch_history(t, start=start_date, end=end_date)
                if df.empty:
                    continue
                df = add_indicators(df, ma_short=ma_short, ma_long=ma_long)
                combo[t] = df["Close"]
            if combo:
                df_combo = pd.DataFrame(combo).dropna(how="all")
                st.plotly_chart(multi_line_chart(df_combo), use_container_width=True)
                st.download_button(
                    "Download Combined CSV",
                    df_combo.to_csv(index=True).encode("utf-8"),
                    file_name="combined_prices.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            else:
                st.write("No data available for comparison.")
else:
    st.info("Enter ticker(s), choose dates, then click **Run**.")
