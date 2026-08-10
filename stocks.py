import streamlit as st
import yfinance as yf

from krx_list import KRX_STOCKS
from jp_list import JP_STOCKS
from us_list import US_STOCKS


def _name_matches(query: str, stock_list, code_field_is_ticker=False):
    matches = []
    for code, name in stock_list:
        if query in name or query == code:
            matches.append((code, name))
    return matches


def _try_candidates(candidates, max_results, results, debug):
    """candidates: list of (symbol, preferred_name_or_None). Appends to results in place."""
    for sym, preferred_name in candidates:
        if len(results) >= max_results:
            break
        try:
            info = yf.Ticker(sym).get_info()
            resolved_name = info.get("shortName") or info.get("longName")
            debug.append(f"{sym}: resolved={resolved_name!r}")
            if resolved_name:
                results.append({
                    "symbol": sym,
                    "name": preferred_name or resolved_name,
                    "exchange": info.get("exchange", ""),
                    "type": info.get("quoteType", ""),
                })
        except Exception as e:
            debug.append(f"{sym}: error {e!r}")


def search_symbols(query: str, max_results: int = 8):
    query = query.strip()
    if not query:
        return [], []

    results = []
    debug = []

    try:
        found = yf.Search(query, max_results=max_results, news_count=0, raise_errors=True).quotes
        debug.append(f"yf.Search: {len(found)} matches")
        for q in found:
            symbol = q.get("symbol")
            if not symbol:
                continue
            results.append({
                "symbol": symbol,
                "name": q.get("shortname") or q.get("longname") or symbol,
                "exchange": q.get("exchange", ""),
                "type": q.get("quoteType", ""),
            })
    except Exception as e:
        debug.append(f"yf.Search error: {e!r}")

    # Yahoo's search doesn't index Korean-language names (company or common names),
    # so try our own curated code/ticker lists next.
    if not results:
        candidates = []
        for code, name in _name_matches(query, KRX_STOCKS):
            candidates.append((f"{code}.KS", name))
            candidates.append((f"{code}.KQ", name))
        for code, name in _name_matches(query, JP_STOCKS):
            candidates.append((f"{code}.T", name))
        for ticker, name in _name_matches(query, US_STOCKS):
            candidates.append((ticker, None))  # keep Yahoo's own English name
        debug.append(f"curated-list candidates: {candidates!r}")
        _try_candidates(candidates[: max_results * 3], max_results, results, debug)

    if not results:
        # Last resort: treat the query as a raw ticker (also try KRX/Japan suffixes for numeric codes)
        candidates = [(query.upper(), None)]
        if query.isdigit() and len(query) == 6:
            candidates = [(f"{query}.KS", None), (f"{query}.KQ", None)]
        elif query.isdigit() and len(query) == 4:
            candidates = [(f"{query}.T", None)]
        _try_candidates(candidates, max_results, results, debug)

    return results, debug


@st.cache_data(ttl=60, show_spinner=False)
def get_quote(symbol: str):
    try:
        info = yf.Ticker(symbol).get_info()
    except Exception as e:
        return {
            "price": None, "prev_close": None, "change": None,
            "change_pct": None, "currency": None, "error": repr(e),
        }

    price = info.get("currentPrice") or info.get("regularMarketPrice")
    prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
    currency = info.get("currency")
    change = None
    change_pct = None
    if price is not None and prev_close:
        change = price - prev_close
        change_pct = (change / prev_close) * 100
    return {
        "price": price,
        "prev_close": prev_close,
        "change": change,
        "change_pct": change_pct,
        "currency": currency,
        "error": None if price is not None else f"no price field (keys sample: {list(info.keys())[:15]})",
    }


_FX_TICKERS = {"KRW": "KRW=X", "JPY": "JPY=X"}


@st.cache_data(ttl=3600, show_spinner=False)
def get_fx_rates():
    """Units of each currency per 1 USD, e.g. {"USD": 1.0, "KRW": 1350.0, "JPY": 150.0}."""
    rates = {"USD": 1.0}
    for currency, ticker in _FX_TICKERS.items():
        try:
            info = yf.Ticker(ticker).get_info()
            rate = info.get("regularMarketPrice") or info.get("currentPrice")
            if rate:
                rates[currency] = rate
        except Exception:
            pass
    return rates


def convert(amount, from_currency, to_currency, rates):
    if amount is None:
        return None
    if from_currency == to_currency:
        return amount
    if from_currency not in rates or to_currency not in rates:
        return None
    usd = amount / rates[from_currency]
    return usd * rates[to_currency]


PERIOD_OPTIONS = {
    "오늘": {"period": "1d", "interval": "5m"},
    "1주일": {"period": "5d", "interval": "30m"},
    "1개월": {"period": "1mo", "interval": "1d"},
    "1년": {"period": "1y", "interval": "1d"},
    "올해": {"period": "ytd", "interval": "1d"},
    "전체기간": {"period": "max", "interval": "1mo"},
}


@st.cache_data(ttl=300, show_spinner=False)
def get_history(symbol: str, period: str, interval: str):
    try:
        hist = yf.Ticker(symbol).history(period=period, interval=interval)
    except Exception:
        return None
    if hist is None or hist.empty:
        return None
    return hist["Close"]


@st.cache_data(ttl=300, show_spinner=False)
def get_news(symbol: str, limit: int = 4):
    try:
        raw = yf.Ticker(symbol).news or []
    except Exception:
        raw = []

    items = []
    for n in raw[:limit]:
        content = n.get("content") if isinstance(n.get("content"), dict) else n

        title = content.get("title") or n.get("title")
        if not title:
            continue

        link = None
        canonical = content.get("canonicalUrl")
        if isinstance(canonical, dict):
            link = canonical.get("url")
        if not link:
            click_through = content.get("clickThroughUrl")
            if isinstance(click_through, dict):
                link = click_through.get("url")
        if not link:
            link = n.get("link")

        publisher = None
        provider = content.get("provider")
        if isinstance(provider, dict):
            publisher = provider.get("displayName")
        if not publisher:
            publisher = n.get("publisher")

        items.append({"title": title, "link": link, "publisher": publisher})

    return items
