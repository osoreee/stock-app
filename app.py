from datetime import datetime

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from auth import current_user, logout, login_signup_ui
import portfolio
import stocks

st.set_page_config(page_title="내 주식 포트폴리오", page_icon="💹", layout="wide")

UP_COLOR = "#e03131"
DOWN_COLOR = "#1971c2"
FLAT_COLOR = "#868e96"

CURRENCY_LABELS = {"KRW": "원", "USD": "달러", "JPY": "엔"}
CURRENCY_SUFFIX = {"KRW": "원", "USD": "$", "JPY": "¥"}

CUSTOM_CSS = """
<style>
.block-container { padding-top: 2rem; max-width: 1200px; }

.app-header { display:flex; align-items:center; gap:12px; margin-bottom: 2px; }
.app-header-icon { font-size: 2.1rem; }
.app-header-title { font-size: 1.9rem; font-weight: 800; letter-spacing: -0.02em; }
.app-subtitle { color:#868e96; font-size:0.85rem; margin-bottom:1.4rem; letter-spacing: 0.01em; }

.stock-badge {
    display: inline-block; padding: 2px 9px; border-radius: 999px;
    font-size: 0.77rem; font-weight: 700; background: #eef1f5; color: #495057;
    letter-spacing: 0.02em;
}
.stock-name { font-size: 1.37rem; font-weight: 700; color: inherit; }
.stock-ticker { font-size: 0.86rem; color: #868e96; }
.stock-price { font-size: 1.7rem; font-weight: 800; margin-top: 10px; line-height: 1.2; }
.stock-currency { font-size: 0.94rem; font-weight: 500; color: #868e96; }
.stock-change { font-size: 1.05rem; font-weight: 700; margin-top: 2px; }
.stock-error { font-size: 0.95rem; color: #868e96; margin-top: 10px; }
.stock-eval { font-size: 0.91rem; color: #495057; margin-top: 12px; line-height: 1.6; }
.stock-eval b { font-weight: 700; }
.portfolio-total-label { font-size: 0.85rem; color: #868e96; }
.portfolio-total-value { font-size: 1.4rem; font-weight: 800; }

.st-key-ctrl_row > div > div[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; }

/* 스마트폰: 3열 카드 그리드와 상단 컨트롤을 한 줄로 유지 (가로 스크롤 없이) */
@media (max-width: 640px) {
    /* 바깥쪽(3장 카드) 행에만 적용 — 카드 안쪽 [이름/삭제] 같은 중첩 컬럼은 건드리지 않음 */
    .st-key-stock_grid > div > div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        gap: 0.3rem !important;
    }
    .st-key-stock_grid > div > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
        width: 33.33% !important;
        min-width: 33.33% !important;
        max-width: 33.33% !important;
        flex: 1 1 0 !important;
    }
    .st-key-stock_grid [data-testid="stVerticalBlockBorderWrapper"] { padding: 0.4rem !important; }

    .st-key-ctrl_row > div > div[data-testid="stHorizontalBlock"] { gap: 0.25rem !important; }
    .st-key-ctrl_row div[data-testid="stColumn"] { min-width: 0 !important; width: 33.33% !important; }
    .st-key-ctrl_row label p { font-size: 0.68rem !important; }
    .st-key-ctrl_row [data-baseweb="select"] * { font-size: 0.72rem !important; }

    .stock-name { font-size: 1.04rem; }
    .stock-ticker { font-size: 0.68rem; }
    .stock-price { font-size: 1.05rem; margin-top: 6px; }
    .stock-currency { font-size: 0.72rem; }
    .stock-change { font-size: 0.75rem; }
    .stock-eval { font-size: 0.68rem; margin-top: 8px; }
    .stock-badge { font-size: 0.64rem; padding: 1px 6px; }
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def change_color(value):
    if not value:
        return FLAT_COLOR
    return UP_COLOR if value > 0 else DOWN_COLOR


def fmt(value, decimals=2):
    return f"{value:,.{decimals}f}"


def is_kr(ticker: str) -> bool:
    return ticker.upper().endswith((".KS", ".KQ"))


def render_detail(h):
    name = stocks.display_name(h["ticker"], h["name"])
    with st.container(border=True):
        st.markdown(f"#### {name} ({h['ticker']})")

        period_label = st.radio(
            "기간", list(stocks.PERIOD_OPTIONS.keys()),
            horizontal=True, key=f"period_{h['id']}",
        )
        opt = stocks.PERIOD_OPTIONS[period_label]
        with st.spinner("차트 불러오는 중..."):
            series = stocks.get_history(h["ticker"], opt["period"], opt["interval"])
        if series is not None and not series.empty:
            st.line_chart(series, height=280)
        else:
            st.caption("차트 데이터를 불러오지 못했습니다.")

        st.markdown("**관련 뉴스**")
        if is_kr(h["ticker"]):
            code = h["ticker"].split(".")[0]
            st.markdown(f"📰 [네이버에서 {name} 뉴스 보기](https://finance.naver.com/item/news.naver?code={code})")
        else:
            news = stocks.get_news(h["ticker"])
            if news:
                for n in news:
                    line = f"- [{n['title']}]({n['link']})" if n["link"] else f"- {n['title']}"
                    if n["publisher"]:
                        line += f" — {n['publisher']}"
                    st.markdown(line)
            else:
                st.caption("관련 뉴스가 없습니다.")


def render_edit_form(h):
    with st.container(border=True):
        st.markdown(f"**✏️ {stocks.display_name(h['ticker'], h['name'])} 보유 정보 수정**")
        edit_cols = st.columns([1, 1, 1])
        with edit_cols[0]:
            new_qty = st.number_input(
                "수량", min_value=0.0, value=float(h["quantity"]), step=1.0, key=f"edit_qty_{h['id']}"
            )
        with edit_cols[1]:
            new_avg = st.number_input(
                "평균 매입단가", min_value=0.0, value=float(h["avg_price"] or 0), step=100.0,
                key=f"edit_avg_{h['id']}",
            )
        with edit_cols[2]:
            st.write("")
            st.write("")
            if st.button("저장", key=f"save_{h['id']}", use_container_width=True):
                portfolio.update_holding(h["id"], new_qty, new_avg)
                st.session_state["editing_id"] = None
                st.success("수정됐습니다.")
                st.rerun()


user = current_user()
if not user:
    login_signup_ui()
    st.stop()

st_autorefresh(interval=60_000, key="auto_refresh")

st.sidebar.markdown(f"### 👤 {user['username']}님")
if st.sidebar.button("로그아웃", use_container_width=True):
    logout()
    st.rerun()

st.markdown(
    "<div class='app-header'><span class='app-header-icon'>💹</span>"
    "<span class='app-header-title'>내 주식 포트폴리오</span></div>"
    f"<div class='app-subtitle'>실시간 시세 · 손익 · 관련 뉴스를 한눈에 · "
    f"마지막 갱신 {datetime.now().strftime('%H:%M:%S')} (1분마다 자동)</div>",
    unsafe_allow_html=True,
)

with st.expander("➕ 종목 추가"):
    query = st.text_input("종목명 또는 티커 (예: 삼성전자, 애플, 도요타, AAPL, 005930)", key="search_query")
    if st.button("검색", key="search_btn") and query:
        with st.spinner("검색 중..."):
            results, _debug = stocks.search_symbols(query)
            st.session_state["search_results"] = results

    results = st.session_state.get("search_results", [])
    if results:
        options = {f"{r['symbol']} — {r['name']} ({r['exchange']})": r for r in results}
        choice = st.selectbox("검색 결과에서 선택", list(options.keys()), key="search_choice")

        col1, col2 = st.columns(2)
        with col1:
            qty = st.number_input("수량", min_value=0.0, value=1.0, step=1.0, key="add_qty")
        with col2:
            avg_price = st.number_input(
                "평균 매입단가 (모르면 0)", min_value=0.0, value=0.0, step=100.0, key="add_avg_price"
            )

        if st.button("추가하기", key="add_btn"):
            picked = options[choice]
            portfolio.add_holding(
                user["id"], picked["symbol"], picked["name"], picked["exchange"], qty, avg_price
            )
            st.session_state.pop("search_results", None)
            st.success(f"{picked['name']} 추가됨")
            st.rerun()
    elif query:
        st.caption("검색 결과가 없습니다. 티커(예: AAPL, 005930)로도 시도해보세요.")

holdings = portfolio.list_holdings(user["id"])

if not holdings:
    st.info("보유 종목이 없습니다. 위에서 추가해보세요.")
    st.stop()

quotes = {h["id"]: stocks.get_quote(h["ticker"]) for h in holdings}
fx_rates = stocks.get_fx_rates()

with st.container(key="ctrl_row"):
    ctrl_cols = st.columns(3)
    with ctrl_cols[0]:
        market_filter = st.selectbox("시장", ["전체", "국장", "해외"], key="market_filter")
    with ctrl_cols[1]:
        sort_key = st.selectbox("정렬", ["시장순", "이름순", "평가금액순", "등락률순"], key="sort_key")
    with ctrl_cols[2]:
        display_currency_label = st.selectbox("통화", list(CURRENCY_LABELS.values()), key="display_currency")
display_currency = next(k for k, v in CURRENCY_LABELS.items() if v == display_currency_label)

filtered = holdings
if market_filter == "국장":
    filtered = [h for h in filtered if is_kr(h["ticker"])]
elif market_filter == "해외":
    filtered = [h for h in filtered if not is_kr(h["ticker"])]


def sort_value(h):
    q = quotes[h["id"]]
    value = (q["price"] or 0) * h["quantity"]
    if sort_key == "이름순":
        return (h["name"], 0)
    if sort_key == "평가금액순":
        return (-value, h["name"])
    if sort_key == "등락률순":
        return (-(q["change_pct"] if q["change_pct"] is not None else -9999), h["name"])
    return (0 if is_kr(h["ticker"]) else 1, h["name"])


filtered = sorted(filtered, key=sort_value)

N_COLS = 3
total_display_value = 0.0
total_display_cost = 0.0

with st.container(key="stock_grid"):
    for row_start in range(0, len(filtered), N_COLS):
        row_items = filtered[row_start:row_start + N_COLS]
        cols = st.columns(N_COLS)
        for col, h in zip(cols, row_items):
            quote = quotes[h["id"]]
            price = quote["price"]
            currency = quote["currency"] or ""
            value = (price or 0) * h["quantity"]

            disp_price = stocks.convert(price, currency, display_currency, fx_rates)
            disp_change = stocks.convert(quote["change"], currency, display_currency, fx_rates)
            disp_value = stocks.convert(value, currency, display_currency, fx_rates)
            if disp_value is not None:
                total_display_value += disp_value

            with col:
                with st.container(border=True):
                    top = st.columns([4, 1, 1])
                    ticker_upper = h["ticker"].upper()
                    if is_kr(h["ticker"]):
                        badge = "국장"
                    elif ticker_upper.endswith(".T"):
                        badge = "일본"
                    else:
                        badge = "해외"
                    display_name = stocks.display_name(h["ticker"], h["name"])
                    top[0].markdown(
                        f"<span class='stock-badge'>{badge}</span><br>"
                        f"<span class='stock-name'>{display_name}</span><br>"
                        f"<span class='stock-ticker'>{h['ticker']}</span>",
                        unsafe_allow_html=True,
                    )
                    if top[1].button("✏️", key=f"edit_{h['id']}", help="수정"):
                        cur = st.session_state.get("editing_id")
                        st.session_state["editing_id"] = None if cur == h["id"] else h["id"]
                        st.rerun()
                    if top[2].button("🗑", key=f"del_{h['id']}", help="삭제"):
                        portfolio.delete_holding(h["id"])
                        st.rerun()

                    if disp_price is not None:
                        change = disp_change or 0
                        change_pct = quote["change_pct"] or 0
                        sign = "+" if change > 0 else ""
                        color = change_color(change)
                        st.markdown(
                            f"<div class='stock-price'>{fmt(disp_price)} "
                            f"<span class='stock-currency'>{CURRENCY_SUFFIX[display_currency]}</span></div>"
                            f"<div class='stock-change' style='color:{color}'>"
                            f"{sign}{fmt(change)} ({sign}{fmt(change_pct)}%)</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown("<div class='stock-error'>가격 조회 실패</div>", unsafe_allow_html=True)

                    eval_html = f"평가금액 <b>{fmt(disp_value or 0, 0)} {CURRENCY_SUFFIX[display_currency]}</b>"
                    if h["avg_price"] and disp_price is not None:
                        cost = h["avg_price"] * h["quantity"]
                        disp_cost = stocks.convert(cost, currency, display_currency, fx_rates) or 0
                        total_display_cost += disp_cost
                        pl = (disp_value or 0) - disp_cost
                        pl_pct = (pl / disp_cost * 100) if disp_cost else 0
                        pl_color = change_color(pl)
                        sign = "+" if pl > 0 else ""
                        eval_html += (
                            f"<br>평가손익 <b style='color:{pl_color}'>"
                            f"{sign}{fmt(pl, 0)} ({sign}{fmt(pl_pct)}%)</b>"
                        )
                    eval_html += f"<br>수량 {fmt(h['quantity'])}"
                    st.markdown(f"<div class='stock-eval'>{eval_html}</div>", unsafe_allow_html=True)

                    st.write("")
                    is_expanded = st.session_state.get("expanded_id") == h["id"]
                    label = "닫기 ▲" if is_expanded else "상세보기 ▾"
                    if st.button(label, key=f"toggle_{h['id']}", use_container_width=True):
                        st.session_state["expanded_id"] = None if is_expanded else h["id"]
                        st.rerun()

        editing_in_row = next(
            (h for h in row_items if st.session_state.get("editing_id") == h["id"]), None
        )
        if editing_in_row:
            render_edit_form(editing_in_row)

        expanded_in_row = next(
            (h for h in row_items if st.session_state.get("expanded_id") == h["id"]), None
        )
        if expanded_in_row:
            render_detail(expanded_in_row)

st.divider()
st.subheader("포트폴리오 요약")
summary_cols = st.columns(2)
with summary_cols[0]:
    st.markdown(
        f"<div class='portfolio-total-label'>총 평가금액 ({display_currency_label})</div>"
        f"<div class='portfolio-total-value'>{fmt(total_display_value, 0)} {CURRENCY_SUFFIX[display_currency]}</div>",
        unsafe_allow_html=True,
    )
if total_display_cost:
    pl = total_display_value - total_display_cost
    pl_pct = pl / total_display_cost * 100
    color = change_color(pl)
    sign = "+" if pl > 0 else ""
    with summary_cols[1]:
        st.markdown(
            f"<div class='portfolio-total-label'>총 손익 ({display_currency_label})</div>"
            f"<div class='portfolio-total-value' style='color:{color}'>"
            f"{sign}{fmt(pl, 0)} ({sign}{fmt(pl_pct)}%)</div>",
            unsafe_allow_html=True,
        )
st.caption("매입단가를 입력하지 않은 종목은 손익 계산에서 제외됩니다. 시세는 1분마다 자동으로 갱신됩니다.")
