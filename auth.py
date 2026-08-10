import streamlit as st
import bcrypt

from db import get_client


def _hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def _check_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())


def current_user():
    return st.session_state.get("user")


def logout():
    st.session_state.pop("user", None)


def signup(username: str, password: str):
    username = username.strip()
    client = get_client()
    existing = client.table("users").select("id").eq("username", username).execute()
    if existing.data:
        return False, "이미 존재하는 아이디입니다."
    client.table("users").insert({
        "username": username,
        "password_hash": _hash_password(password),
    }).execute()
    return True, "가입 완료! 로그인해주세요."


def login(username: str, password: str):
    username = username.strip()
    client = get_client()
    res = client.table("users").select("id, username, password_hash").eq("username", username).execute()
    if not res.data:
        return False, "아이디 또는 비밀번호가 틀렸습니다."
    row = res.data[0]
    if not _check_password(password, row["password_hash"]):
        return False, "아이디 또는 비밀번호가 틀렸습니다."
    st.session_state["user"] = {"id": row["id"], "username": row["username"]}
    return True, "로그인 성공"


def login_signup_ui():
    st.markdown(
        "<div style='display:flex;align-items:center;gap:12px;margin-bottom:1.2rem;'>"
        "<span style='font-size:2.1rem;'>💹</span>"
        "<span style='font-size:1.9rem;font-weight:800;letter-spacing:-0.02em;'>내 주식 포트폴리오</span>"
        "</div>",
        unsafe_allow_html=True,
    )
    tab_login, tab_signup = st.tabs(["로그인", "회원가입"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("아이디", key="login_username")
            password = st.text_input("비밀번호", type="password", key="login_password")
            submitted = st.form_submit_button("로그인")
            if submitted:
                if not username or not password:
                    st.error("아이디와 비밀번호를 입력해주세요.")
                else:
                    ok, msg = login(username, password)
                    if ok:
                        st.rerun()
                    else:
                        st.error(msg)

    with tab_signup:
        with st.form("signup_form"):
            username = st.text_input("아이디", key="signup_username")
            password = st.text_input("비밀번호", type="password", key="signup_password")
            password2 = st.text_input("비밀번호 확인", type="password", key="signup_password2")
            submitted = st.form_submit_button("회원가입")
            if submitted:
                if not username or not password:
                    st.error("아이디와 비밀번호를 입력해주세요.")
                elif password != password2:
                    st.error("비밀번호가 일치하지 않습니다.")
                else:
                    ok, msg = signup(username, password)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
