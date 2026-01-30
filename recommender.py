import pandas as pd
import numpy as np
import yfinance as yf
from indicators import compute_rsi, ichimoku_signal
from news_fetcher import fetch_news_and_sentiment
from joblib import Parallel, delayed
from cache_utils import cached_fetch_history, cached_fetch_news_and_sentiment, cached_fetch_info


def compute_momentum(df: pd.DataFrame, days: int = 20) -> float:
    """Return simple momentum: percent change over `days` trading days."""
    if len(df) < days + 1:
        return np.nan
    start = df['Close'].iloc[-(days+1)]
    end = df['Close'].iloc[-1]
    return (end - start) / start * 100


def compute_volatility(df: pd.DataFrame, days: int = 20) -> float:
    """Return annualized volatility estimate from daily returns over `days`."""
    if len(df) < days + 1:
        return np.nan
    returns = df['Close'].pct_change().dropna().iloc[-days:]
    return returns.std() * np.sqrt(252) * 100


def recommend_by_momentum(history_func, tickers, period_days=60, top_n=5):
    """Backward-compatible simple recommender kept for quick checks."""
    rows = []
    for t in tickers:
        try:
            df = history_func(t, period=f"{int(period_days/21)+1}mo")
        except Exception:
            continue
        mom = compute_momentum(df, days=min(20, len(df)-1))
        vol = compute_volatility(df, days=min(20, len(df)-1))
        if np.isnan(mom) or np.isnan(vol) or vol == 0:
            continue
        score = mom / vol
        rows.append({'ticker': t, 'momentum_%': mom, 'volatility_%': vol, 'score': score})
    if not rows:
        return []
    df_out = pd.DataFrame(rows).sort_values('score', ascending=False)
    return df_out.head(top_n).reset_index(drop=True)


def _process_one_ticker(t: str):
    try:
        df = cached_fetch_history(t, "6mo")
    except Exception:
        return None
    if df is None or len(df) < 60:
        return None

    try:
        rsi_series = compute_rsi(df['Close'], period=14)
        rsi_now = float(rsi_series.iloc[-1])
    except Exception:
        rsi_now = np.nan

    ichi = ichimoku_signal(df[['High', 'Low', 'Close']])
    news = cached_fetch_news_and_sentiment(t)
    sentiment = news.get('sentiment', 0.0)

    mom = compute_momentum(df, days=20)
    vol = compute_volatility(df, days=20)

    # fundamentals via cached info
    info = cached_fetch_info(t)
    psr = info.get('priceToSalesTrailing12Months') or info.get('priceToSales') or np.nan
    pbr = info.get('priceToBook') or np.nan

    # scoring rules
    score = 0.0
    if not np.isnan(mom) and not np.isnan(vol) and vol > 0:
        score += (mom / (vol + 1)) * 2.0
    if not np.isnan(rsi_now):
        if rsi_now < 35:
            score += 1.5
        elif rsi_now > 65:
            score -= 1.5
    if ichi.get('price_above_cloud') is True:
        score += 1.2
    elif ichi.get('price_above_cloud') is False:
        score -= 1.0
    score += float(sentiment) * 2.0

    # apply user rules
    if not np.isnan(rsi_now) and rsi_now >= 80:
        reco = 'sell'
    else:
        if score >= 2.0:
            psr_ok = True if (np.isnan(psr) or (psr <= 20)) else False
            pbr_ok = True if (np.isnan(pbr) or (pbr <= 30)) else False
            reco = 'buy' if (psr_ok and pbr_ok) else 'hold'
        elif score <= -1.5:
            reco = 'sell'
        else:
            reco = 'hold'

    return {
        'ticker': t,
        'score': score,
        'reco': reco,
        'momentum_%': mom,
        'volatility_%': vol,
        'rsi': rsi_now,
        'ichimoku_price_above_cloud': ichi.get('price_above_cloud'),
        'sentiment': sentiment,
        'psr': psr,
        'pbr': pbr,
    }


def recommend_advanced(history_func=None, tickers=None, max_scan=200, n_jobs=4):
    """Advanced recommender that combines RSI, Ichimoku and news sentiment.

    - `history_func(ticker, period=...)` should return a DataFrame with OHLCV.
    - `tickers` is an iterable of ticker strings.
    - `max_scan` limits how many tickers to check in one run (avoid very long runs).
    Returns a dict with DataFrames for `buy`, `sell`, and `hold`.
    """
    if tickers is None:
        return {'buy': pd.DataFrame(), 'sell': pd.DataFrame(), 'hold': pd.DataFrame()}

    tickers = list(tickers)[:max_scan]

    # run processing in parallel
    results = Parallel(n_jobs=n_jobs)(delayed(_process_one_ticker)(t) for t in tickers)

    rows = [r for r in results if r is not None]

    if not rows:
        return {'buy': pd.DataFrame(), 'sell': pd.DataFrame(), 'hold': pd.DataFrame()}

    df_out = pd.DataFrame(rows).sort_values('score', ascending=False).reset_index(drop=True)
    df_buy = df_out[df_out['reco'] == 'buy'].reset_index(drop=True)
    df_sell = df_out[df_out['reco'] == 'sell'].reset_index(drop=True)
    df_hold = df_out[df_out['reco'] == 'hold'].reset_index(drop=True)
    return {'buy': df_buy, 'sell': df_sell, 'hold': df_hold}
