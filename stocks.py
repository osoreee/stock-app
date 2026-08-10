import streamlit as st
import yfinance as yf


def search_symbols(query: str, max_results: int = 8):
    query = query.strip()
    if not query:
        return [], []

    results = []
    debug = []
    try:
        found = yf.Search(query, max_results=max_results, news_count=0, raise_errors=True).quotes
        debug.append(f"yf.Search raw quotes: {found!r}")
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

    if not results:
        # Fallback: treat the query as a raw ticker (also try KRX suffixes for 6-digit codes)
        candidates = [query.upper()]
        if query.isdigit() and len(query) == 6:
            candidates = [f"{query}.KS", f"{query}.KQ"]
        for sym in candidates:
            try:
                info = yf.Ticker(sym).get_info()
                name = info.get("shortName") or info.get("longName")
                debug.append(f"{sym}: info keys={list(info.keys())[:10]}, name={name!r}")
                if name:
                    results.append({
                        "symbol": sym,
                        "name": name,
                        "exchange": info.get("exchange", ""),
                        "type": info.get("quoteType", ""),
                    })
            except Exception as e:
                debug.append(f"{sym}: error {e!r}")

    return results, debug


@st.cache_data(ttl=60, show_spinner=False)
def get_quote(symbol: str):
    fi = yf.Ticker(symbol).fast_info
    price = fi.get("last_price")
    prev_close = fi.get("previous_close")
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
        "currency": fi.get("currency"),
    }


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
