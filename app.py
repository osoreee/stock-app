import streamlit as st

from auth import current_user, logout, login_signup_ui
import portfolio
import stocks

st.set_page_config(page_title="내 주식 포트폴리오", page_icon="📈", layout="wide")

user = current_user()
if not user:
    login_signup_ui()
    st.stop()

st.sidebar.write(f"👤 **{user['username']}**님")
if st.sidebar.button("로그아웃"):
    logout()
    st.rerun()

st.title("📈 내 주식 포트폴리오")

if st.button("🔄 새로고침"):
    st.cache_data.clear()
    st.rerun()

with st.expander("➕ 종목 추가"):
    query = st.text_input("종목명 또는 티커 (예: 삼성전자, AAPL, QQQ, 005930)", key="search_query")
    if st.button("검색", key="search_btn") and query:
        with st.spinner("검색 중..."):
            st.session_state["search_results"] = stocks.search_symbols(query)

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
        st.caption("검색 버튼을 눌러주세요.")

holdings = portfolio.list_holdings(user["id"])

if not holdings:
    st.info("보유 종목이 없습니다. 위에서 추가해보세요.")
else:
    totals = {}  # currency -> {"value": float, "cost": float}

    for h in holdings:
        quote = stocks.get_quote(h["ticker"])
        price = quote["price"]
        change = quote["change"]
        change_pct = quote["change_pct"]
        currency = quote["currency"] or "?"

        value = (price or 0) * h["quantity"]
        cost = (h["avg_price"] or 0) * h["quantity"]
        t = totals.setdefault(currency, {"value": 0.0, "cost": 0.0})
        t["value"] += value
        t["cost"] += cost

        cols = st.columns([3, 2, 2, 2, 2, 1])
        cols[0].markdown(f"**{h['name']}**  \n`{h['ticker']}`")

        if price is not None:
            delta = f"{change:+,.2f} ({change_pct:+.2f}%)" if change is not None else None
            cols[1].metric("현재가", f"{price:,.2f} {currency}", delta)
        else:
            cols[1].write("가격 조회 실패")

        cols[2].write(f"수량: {h['quantity']:,.2f}")
        cols[3].write(f"평가금액: {value:,.0f} {currency}")

        if h["avg_price"]:
            pl = value - cost
            pl_pct = (pl / cost * 100) if cost else 0
            cols[4].write(f"손익: {pl:+,.0f} ({pl_pct:+.2f}%)")
        else:
            cols[4].write("")

        if cols[5].button("삭제", key=f"del_{h['id']}"):
            portfolio.delete_holding(h["id"])
            st.rerun()

        news = stocks.get_news(h["ticker"])
        if news:
            with st.expander(f"📰 {h['name']} 관련 뉴스"):
                for n in news:
                    line = f"- [{n['title']}]({n['link']})" if n["link"] else f"- {n['title']}"
                    if n["publisher"]:
                        line += f" — {n['publisher']}"
                    st.markdown(line)

        st.divider()

    st.subheader("포트폴리오 요약 (통화별)")
    for currency, t in totals.items():
        c1, c2 = st.columns(2)
        c1.metric(f"{currency} 총 평가금액", f"{t['value']:,.0f}")
        if t["cost"]:
            pl = t["value"] - t["cost"]
            c2.metric(f"{currency} 총 손익", f"{pl:+,.0f}", f"{(pl / t['cost'] * 100):+.2f}%")
