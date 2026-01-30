import pandas as pd
import requests
from io import StringIO


def fetch_nasdaq_list():
    """Fetch NASDAQ-listed tickers from NasdaqTrader FTP (public). Returns list of symbols."""
    url = 'https://ftp.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt'
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    txt = r.text
    # file uses | as separator with a final footer line
    df = pd.read_csv(StringIO(txt), sep='|')
    if 'Symbol' in df.columns:
        syms = df['Symbol'].dropna().astype(str).tolist()
        # remove the footer row if present (e.g., 'File Creation Time')
        syms = [s for s in syms if s and 'File' not in s]
        return syms
    return []


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
