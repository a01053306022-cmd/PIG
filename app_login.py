import streamlit as st
from db_handler import insert_login_log

st.set_page_config(page_title="로그인 시스템", layout="centered")

# 세션 상태를 이용해 결과 화면 이동 제어
# 세션 상태가 login(기본값)이면 로그인 화면으로 연결
if "page_status" not in st.session_state:
    st.session_state.page_status = "login"
if "logged_user" not in st.session_state:
    st.session_state.logged_user = ""
# 로그인 시 normal(정상 로그인) 또는 abnormal(비정상 로그인)으로 연결

# --- [화면 2] 로그인 입력 폼 ---
if st.session_state.page_status == "login":
    st.title("Login Page")
    st.caption("개인정보 보호 및 보안 구현 상태 테스트 화면")

    with st.form("login_form"):
        user_id = st.text_input("ID (User_id)", placeholder="아이디를 입력하세요")
        password = st.text_input("PW", type="password", placeholder="비밀번호를 입력하세요")
        submit_btn = st.form_submit_button("Login")
        
    if submit_btn:
        if not user_id or not password:
            st.warning("아이디와 비밀번호를 모두 입력해주세요.")
        else:
            st.session_state.logged_user = user_id
            # 기획서 시연 예시 필터 적용
            if "hack" in user_id.lower() or "test" in user_id.lower() or "blacklist" in user_id.lower():
                # [화면 4] 비정상 로그인 판정 및 DB 저장
                insert_login_log(user_id, "비정상")
                st.session_state.page_status = "abnormal"
                st.rerun()
            else:
                # [화면 3] 정상 로그인 판정 및 DB 저장
                insert_login_log(user_id, "정상")
                st.session_state.page_status = "normal"
                st.rerun()

# --- [화면 3] 정상 로그인 성공 결과 화면 ---
elif st.session_state.page_status == "normal":
    st.success("🟢 정상 로그인")
    st.subheader(f"👋 '{st.session_state.logged_user}'님")
    st.info("정상적으로 로그인되었습니다.")
    
    if st.button("처음으로 돌아가기"):
        st.session_state.page_status = "login"
        st.rerun()

# --- [화면 4] 비정상 로그인 차단 결과 화면 ---
elif st.session_state.page_status == "abnormal":
    st.error("🔴 비정상 로그인")
    st.subheader(f"⚠️ 위험 계정 탐지: {st.session_state.logged_user}")
    st.warning("비정상적인 로그인으로 판단되었습니다. 추가 인증 혹은 관리자 승인이 필요합니다.")
    
    if st.button("처음으로 돌아가기"):
        st.session_state.page_status = "login"
        st.rerun()
