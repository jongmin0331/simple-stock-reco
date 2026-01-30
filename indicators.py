import pandas as pd
import numpy as np


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI (Wilder's smoothing). Returns a Series aligned with input index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def ichimoku(df: pd.DataFrame):
    """Compute Ichimoku components and return dict with recent values.

    Expects `df` with columns ['High','Low','Close'] and DateTime index or integer index.
    """
    high = df['High']
    low = df['Low']
    close = df['Close']

    # Tenkan-sen (conversion line): (9-period high + 9-period low)/2
    period9_high = high.rolling(window=9).max()
    period9_low = low.rolling(window=9).min()
    tenkan = (period9_high + period9_low) / 2

    # Kijun-sen (base line): (26-period high + 26-period low)/2
    period26_high = high.rolling(window=26).max()
    period26_low = low.rolling(window=26).min()
    kijun = (period26_high + period26_low) / 2

    # Senkou Span A (leading span A): (tenkan + kijun)/2 shifted 26 periods ahead
    span_a = ((tenkan + kijun) / 2).shift(26)

    # Senkou Span B (leading span B): (52-period high + 52-period low)/2 shifted 26 ahead
    period52_high = high.rolling(window=52).max()
    period52_low = low.rolling(window=52).min()
    span_b = ((period52_high + period52_low) / 2).shift(26)

    # Chikou Span (lagging): close shifted -26 (i.e., 26 periods back)
    chikou = close.shift(-26)

    res = {
        'tenkan': tenkan,
        'kijun': kijun,
        'span_a': span_a,
        'span_b': span_b,
        'chikou': chikou,
    }
    return res


def ichimoku_signal(df: pd.DataFrame) -> dict:
    """Return simple ichimoku-based signals for the most recent row.

    Signals: price_above_cloud (bool), bullish_cross (tenkan > kijun), bearish_cross
    """
    ichi = ichimoku(df)
    last_idx = df.index[-1]
    price = df['Close'].iloc[-1]
    span_a = ichi['span_a'].iloc[-1]
    span_b = ichi['span_b'].iloc[-1]
    tenkan_last = ichi['tenkan'].iloc[-1]
    kijun_last = ichi['kijun'].iloc[-1]

    # cloud top/bottom
    if pd.isna(span_a) or pd.isna(span_b):
        price_above_cloud = None
    else:
        cloud_top = max(span_a, span_b)
        cloud_bottom = min(span_a, span_b)
        price_above_cloud = price > cloud_top

    bullish_cross = False
    bearish_cross = False
    if not pd.isna(tenkan_last) and not pd.isna(kijun_last):
        bullish_cross = tenkan_last > kijun_last
        bearish_cross = tenkan_last < kijun_last

    return {
        'price': price,
        'price_above_cloud': price_above_cloud,
        'bullish_cross': bullish_cross,
        'bearish_cross': bearish_cross,
    }
