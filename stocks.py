import streamlit as st
import yfinance as yf
import requests


def _extract_krx_candidates(obj):
    """Recursively scan a JSON structure for [6-digit code, name, ...] patterns,
    since Naver's autocomplete response shape isn't officially documented."""
    found = []
    if isinstance(obj, list):
        if len(obj) >= 2 and isinstance(obj[0], str) and obj[0].isdigit() and len(obj[0]) == 6:
            name = obj[1] if isinstance(obj[1], str) else obj[0]
            found.append((obj[0], name))
        else:
            for item in obj:
                found.extend(_extract_krx_candidates(item))
    elif isinstance(obj, dict):
        for v in obj.values():
            found.extend(_extract_krx_candidates(v))
    return found


def search_krx_by_name(query: str, limit: int = 5):
    """Korean company name -> KRX code, via Naver Finance's autocomplete API.
    Yahoo Finance's search doesn't index Korean-language company names."""
    resp = requests.get(
        "https://ac.finance.naver.com/ac",
        params={
            "q": query, "q_enc": "UTF-8", "st": 111, "frm": "stock",
            "r_format": "json", "r_enc": "UTF-8", "r_unicode": 0,
            "t_koreng": 1, "run": 2, "rev": 4,
        },
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=10,
    )
    data = resp.json()
    seen = set()
    matches = []
    for code, name in _extract_krx_candidates(data):
        if code in seen:
            continue
        seen.add(code)
        matches.append({"code": code, "name": name})
        if len(matches) >= limit:
            break
    return matches


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

    candidates = []
    if not results:
        try:
            krx_matches = search_krx_by_name(query, limit=max_results)
            debug.append(f"Naver KRX matches: {krx_matches!r}")
            for m in krx_matches:
                candidates.append(f"{m['code']}.KS")
                candidates.append(f"{m['code']}.KQ")
        except Exception as e:
            debug.append(f"Naver search error: {e!r}")

    if not results and not candidates:
        # Last resort: treat the query as a raw ticker (also try KRX suffixes for 6-digit codes)
        candidates = [query.upper()]
        if query.isdigit() and len(query) == 6:
            candidates = [f"{query}.KS", f"{query}.KQ"]

    for sym in candidates:
        if len(results) >= max_results:
            break
        try:
            info = yf.Ticker(sym).get_info()
            name = info.get("shortName") or info.get("longName")
            debug.append(f"{sym}: name={name!r}")
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
