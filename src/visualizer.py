import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def line_price_chart(df: pd.DataFrame, symbol: str, ma_short: int, ma_long: int):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Close'))
    if f"MA_{ma_short}" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[f"MA_{ma_short}"], mode='lines', name=f"MA {ma_short}"))
    if f"MA_{ma_long}" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[f"MA_{ma_long}"], mode='lines', name=f"MA {ma_long}"))
    fig.update_layout(title=f"{symbol} — Close & Moving Averages", xaxis_title="Date", yaxis_title="Price")
    return fig

def candlestick_chart(df: pd.DataFrame, symbol: str):
    if not set(['Open','High','Low','Close']).issubset(df.columns):
        return line_price_chart(df, symbol, 0, 0)
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name='OHLC'
    )])
    fig.update_layout(title=f"{symbol} — Candlestick", xaxis_title="Date", yaxis_title="Price")
    return fig

def multi_line_chart(df_combo: pd.DataFrame):
    fig = px.line(df_combo, x=df_combo.index, y=df_combo.columns, labels={'value':'Close','variable':'Ticker'}, title="Close Price Comparison")
    return fig
