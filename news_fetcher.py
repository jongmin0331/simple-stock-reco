import yfinance as yf
import requests

# Very small rule-based sentiment (fallback). You can extend with NewsAPI or other services.
POSITIVE = set(["gain","positive","up","beat","rise","record","strong","upgrade","buy","outperform"])
NEGATIVE = set(["drop","down","fall","miss","weak","downgrade","sell","underperform","loss","decline"])


def fetch_yf_news(ticker: str, max_items: int = 5):
    """Fetch news items from yfinance (limited). Returns list of dicts with title and link."""
    tk = yf.Ticker(ticker)
    try:
        items = tk.news
    except Exception:
        items = []
    out = []
    for it in items[:max_items]:
        title = it.get('title') or it.get('headline') or ''
        link = it.get('link') or it.get('url') or ''
        out.append({'title': title, 'link': link})
    return out


def simple_sentiment(text: str) -> float:
    """Naive sentiment score between -1 and 1 based on presence of words.

    Positive words add +1, negative words add -1, normalized by number of matches.
    """
    if not text:
        return 0.0
    t = text.lower()
    score = 0
    matches = 0
    for w in POSITIVE:
        if w in t:
            score += 1
            matches += 1
    for w in NEGATIVE:
        if w in t:
            score -= 1
            matches += 1
    if matches == 0:
        return 0.0
    return max(-1.0, min(1.0, score / matches))


def aggregate_news_sentiment(news_items):
    """Compute average sentiment for a list of news items (each with 'title')."""
    if not news_items:
        return 0.0
    scores = [simple_sentiment(it.get('title','')) for it in news_items]
    return sum(scores) / len(scores)


def fetch_news_and_sentiment(ticker: str):
    news = fetch_yf_news(ticker, max_items=6)
    sent = aggregate_news_sentiment(news)
    return {'news': news, 'sentiment': sent}
