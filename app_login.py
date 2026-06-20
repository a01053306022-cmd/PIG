import streamlit as st
import requests
from datetime import datetime
from user_agents import parse
from db_handler import check_blacklist, insert_login_log

st.set_page_config(page_title="로그인 시스템", layout="centered")

# 세션 상태 초기화
if "page_status" not in st.session_state:
    st.session_state.page_status = "login"
if "logged_user" not in st.session_state:
    st.session_state.logged_user = ""

def get_realtime_env():
    """실시간으로 접속자의 IP, 위치, OS, 기기, 브라우저 정보를 자동으로 추출"""
    # 1. 실시간 공인 IP 주소 가져오기
    try:
        ip_address = requests.get("https://api.ipify.org", timeout=3).text
    except:
        ip_address = "127.0.0.1"

    # 2. IP 기반 실시간 위치 가져오기
    try:
        geo_resp = requests.get(f"http://ip-api.com{ip_address}", timeout=3).json()
        if geo_resp.get("status") == "success":
            location = f"{geo_resp.get('city')}, {geo_resp.get('country')}"
        else:
            location = "Unknown Location"
    except:
        location = "Unknown Location"

    # 3. User-Agent 추출 및 파싱
    headers = st.context.headers
    user_agent_string = headers.get("User-Agent", "")
    user_agent = parse(user_agent_string)
    
    os_type = user_agent.os.family
    browser = user_agent.browser.family
    
    if user_agent.is_mobile:
        device_type = "Mobile"
    elif user_agent.is_tablet:
        device_type = "Tablet"
    else:
        device_type = "PC"
        
    return {
        "ip_address": ip_address,
        "location": location,
        "device_type": device_type,
        "os_type": os_type,
        "browser": browser
    }

def handle_login_submit(uid, pwd):
    if not uid or not pwd:
        st.warning("아이디와 비밀번호를 모두 입력해주세요.")
        return

    st.session_state.logged_user = uid
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 실시간 환경 데이터 자동 수집
    env = get_realtime_env()
    session_duration = 15 
    
    # DB의 blacklist 테이블과 대조
    is_black = check_blacklist(env["ip_address"], env["location"], env["device_type"], env["os_type"])
    
    if is_black:
        # 블랙리스트에 걸렸을 때
        insert_login_log(
            timestamp, uid, env["ip_address"], env["location"], 
            env["device_type"], env["os_type"], env["browser"], "FALSE", session_duration
        )
        st.session_state.page_status = "abnormal"
    else:
        # 블랙리스트가 비어있거나 걸리는 게 없을 때 (정상 통과)
        insert_login_log(
            timestamp, uid, env["ip_address"], env["location"], 
            env["device_type"], env["os_type"], env["browser"], "TRUE", session_duration
        )
        st.session_state.page_status = "normal"

# --- [화면 2] 로그인 입력 폼 ---
if st.session_state.page_status == "login":
    st.title("🔑 Login 화면")
    
    with st.form("login_form"):
        st.subheader("계정 정보 입력")
        user_id = st.text_input("ID (User_id)", placeholder="user_id 입력")
        password = st.text_input("PW", type="password", placeholder="비밀번호 입력")
        
        st.form_submit_button(
            "Login", 
            on_click=handle_login_submit, 
            args=(user_id, password)
        )

# --- [화면 3] 정상 로그인 성공 결과 화면 ---
elif st.session_state.page_status == "normal":
    st.success("🟢 정상 로그인")
    st.subheader(f"👋 '{st.session_state.logged_user}'님")
    st.info("실시간 보안 검증 결과 안전한 환경으로 확인되었습니다.")
    if st.button("처음으로 돌아가기"):
        st.session_state.page_status = "login"
        st.rerun()

# --- [화면 4] 비정상 로그인 차단 결과 화면 ---
elif st.session_state.page_status == "abnormal":
    st.error("🔴 비정상 로그인 차단")
    st.subheader(f"⚠️ 위험 환경 탐지 차단: {st.session_state.logged_user}")
    st.warning("현재 접속하신 실시간 네트워크 및 기기 정보가 위험 블랙리스트 데이터와 일치하여 접근이 제한되었습니다.")
    if st.button("처음으로 돌아가기"):
        st.session_state.page_status = "login"
        st.rerun()
