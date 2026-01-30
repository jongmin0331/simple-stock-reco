import pandas as pd
import numpy as np
import yfinance as yf
from indicators import compute_rsi, ichimoku_signal
from news_fetcher import fetch_news_and_sentiment


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


def recommend_advanced(history_func, tickers, max_scan=200):
    """Advanced recommender that combines RSI, Ichimoku and news sentiment.

    - `history_func(ticker, period=...)` should return a DataFrame with OHLCV.
    - `tickers` is an iterable of ticker strings.
    - `max_scan` limits how many tickers to check in one run (avoid very long runs).
    Returns a dict with DataFrames for `buy`, `sell`, and `hold`.
    """
    rows = []
    scanned = 0
    for t in tickers:
        if scanned >= max_scan:
            break
        scanned += 1
        try:
            df = history_func(t, period="6mo")
        except Exception:
            continue
        if len(df) < 60:
            continue

        # indicators
        try:
            rsi_series = compute_rsi(df['Close'], period=14)
            rsi_now = float(rsi_series.iloc[-1])
        except Exception:
            rsi_now = np.nan

        ichi = ichimoku_signal(df[['High','Low','Close']])
        news = fetch_news_and_sentiment(t)
        sentiment = news.get('sentiment', 0.0)

        mom = compute_momentum(df, days=20)
        vol = compute_volatility(df, days=20)

        # fundamentals: try getting PSR/PBR from yfinance info
        psr = np.nan
        pbr = np.nan
        try:
            tk = yf.Ticker(t)
            info = tk.info or {}
            psr = info.get('priceToSalesTrailing12Months') or info.get('priceToSales') or np.nan
            pbr = info.get('priceToBook') or np.nan
        except Exception:
            psr = np.nan
            pbr = np.nan

        # scoring rules (simple, tunable)
        score = 0.0
        # momentum normalized
        if not np.isnan(mom) and not np.isnan(vol) and vol > 0:
            score += (mom / (vol+1)) * 2.0
        # RSI: oversold adds to buy, overbought subtracts
        if not np.isnan(rsi_now):
            if rsi_now < 35:
                score += 1.5
            elif rsi_now > 65:
                score -= 1.5
        # Ichimoku: price above cloud is bullish
        if ichi.get('price_above_cloud') is True:
            score += 1.2
        elif ichi.get('price_above_cloud') is False:
            score -= 1.0
        # sentiment
        score += float(sentiment) * 2.0

        # determine recommendation
        # If RSI >= 80 -> strong sell signal per user rule
        reco = 'hold'
        if not np.isnan(rsi_now) and rsi_now >= 80:
            reco = 'sell'
        else:
            if score >= 2.0:
                # apply PSR/PBR filters for buy candidates
                # user rule: PSR <= 20, PBR <= 30
                psr_ok = True if (np.isnan(psr) or (psr <= 20)) else False
                pbr_ok = True if (np.isnan(pbr) or (pbr <= 30)) else False
                if psr_ok and pbr_ok:
                    reco = 'buy'
                else:
                    reco = 'hold'
            elif score <= -1.5:
                reco = 'sell'

        rows.append({
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
        })

    if not rows:
        return {'buy': pd.DataFrame(), 'sell': pd.DataFrame(), 'hold': pd.DataFrame()}
    df_out = pd.DataFrame(rows).sort_values('score', ascending=False).reset_index(drop=True)

    # split into buy / sell / hold
    df_buy = df_out[df_out['reco'] == 'buy'].reset_index(drop=True)
    df_sell = df_out[df_out['reco'] == 'sell'].reset_index(drop=True)
    df_hold = df_out[df_out['reco'] == 'hold'].reset_index(drop=True)
    return {'buy': df_buy, 'sell': df_sell, 'hold': df_hold}
