import pandas as pd
import yfinance as yf
from functools import lru_cache

@lru_cache(maxsize=64)
def _ticker_obj(symbol: str):
    return yf.Ticker(symbol)

def fetch_history(symbol: str, start=None, end=None) -> pd.DataFrame:
    """Fetch historical OHLCV data for a symbol."""
    try:
        df = yf.download(symbol, start=start, end=end, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df.reset_index().set_index("Date")
    except Exception:
        return pd.DataFrame()

def add_indicators(df: pd.DataFrame, ma_short: int = 7, ma_long: int = 30) -> pd.DataFrame:
    out = df.copy()
    if "Close" in out.columns:
        out[f"MA_{ma_short}"] = out["Close"].rolling(window=ma_short).mean()
        out[f"MA_{ma_long}"] = out["Close"].rolling(window=ma_long).mean()
    return out

def fetch_info(symbol: str) -> dict:
    try:
        t = _ticker_obj(symbol)
        return t.fast_info if hasattr(t, "fast_info") else t.info
    except Exception:
        return {}
