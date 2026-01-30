from joblib import Memory
from typing import Any, Dict

memory = Memory(location=".cache", verbose=0)

@memory.cache
def cached_fetch_history(ticker: str, period: str):
    # Import inside function to avoid circular imports at module import time
    from data_fetcher import fetch_history

    return fetch_history(ticker, period=period)


@memory.cache
def cached_fetch_news_and_sentiment(ticker: str) -> Dict[str, Any]:
    from news_fetcher import fetch_news_and_sentiment

    return fetch_news_and_sentiment(ticker)


@memory.cache
def cached_fetch_info(ticker: str) -> Dict[str, Any]:
    # Use yfinance to fetch ticker info; cached to avoid repeated network calls
    import yfinance as yf

    tk = yf.Ticker(ticker)
    try:
        return tk.info or {}
    except Exception:
        return {}


def clear_cache():
    memory.clear(warn=False)
