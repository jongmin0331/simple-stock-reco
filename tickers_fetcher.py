import pandas as pd
import requests
from io import StringIO
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def _session_with_retries(total_retries=3, backoff=1.0):
    s = requests.Session()
    retries = Retry(total=total_retries, backoff_factor=backoff, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    s.mount('https://', adapter)
    s.mount('http://', adapter)
    return s


def fetch_nasdaq_list():
    """Fetch NASDAQ-listed tickers with retries and fallbacks.

    Tries NasdaqTrader first, then a mirrored CSV on GitHub, then returns a small fallback list.
    """
    primary = 'https://ftp.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt'
    fallback_raw = 'https://raw.githubusercontent.com/datasets/nasdaq-listings/master/data/nasdaq-listed.csv'
    session = _session_with_retries()

    for url in (primary, fallback_raw):
        try:
            r = session.get(url, timeout=30)
            r.raise_for_status()
            txt = r.text
            # NasdaqTrader uses '|' delimiter; CSV fallback uses comma
            if '|' in txt:
                df = pd.read_csv(StringIO(txt), sep='|')
                if 'Symbol' in df.columns:
                    syms = df['Symbol'].dropna().astype(str).tolist()
                    syms = [s for s in syms if s and 'File' not in s]
                    return syms
            else:
                df = pd.read_csv(StringIO(txt))
                # try common column names
                for col in ('Symbol', 'NASDAQ Symbol', 'symbol'):
                    if col in df.columns:
                        syms = df[col].dropna().astype(str).tolist()
                        return syms
        except Exception:
            # try next fallback
            continue

    # final fallback small list to avoid total failure
    return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']


def fetch_kospi_list():
    """Fetch KOSPI listed tickers (KRX). Returns list of tickers in KRX format (e.g., 005930.KS).

    Note: KRX pages sometimes require specific headers; this function uses the public download endpoint.
    """
    # KRX provides a download link that returns an HTML table; pandas can parse it.
    url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&marketType=stockMkt'
    try:
        # KRX uses euc-kr encoding
        tables = pd.read_html(url, encoding='euc-kr')
        if tables:
            df = tables[0]
            # typical columns: 회사명, 종목코드, 업종, 주식종류
            if '종목코드' in df.columns:
                df['종목코드'] = df['종목코드'].astype(str).str.zfill(6) + '.KS'
                return df['종목코드'].tolist()
    except Exception:
        pass
    # fallback: small static list so functions don't fail hard
    return ['005930.KS', '000660.KS', '035420.KS']
