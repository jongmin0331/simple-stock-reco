import pandas as pd
import numpy as np


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
    """Simple rule-based recommender.

    - Fetch `period_days` of history per ticker using `history_func(ticker, period=...)`.
    - Score = momentum / volatility (higher is better).
    """
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
