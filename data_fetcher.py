import yfinance as yf
import pandas as pd


def fetch_history(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """Fetch historical OHLCV data for a ticker using yfinance.

    For KOSPI tickers, pass the ticker with the ".KS" suffix (e.g. "005930.KS").
    """
    tk = yf.Ticker(ticker)
    df = tk.history(period=period, interval=interval)
    if df.empty:
        raise ValueError(f"No data for {ticker}")
    df = df[['Open','High','Low','Close','Volume']].copy()
    df.reset_index(inplace=True)
    return df


def ensure_kr_suffix(ticker: str) -> str:
    """If the ticker looks numeric (Korean), append .KS"""
    if ticker.replace('.', '').isdigit() and not ticker.endswith('.KS'):
        return ticker + '.KS'
    return ticker
