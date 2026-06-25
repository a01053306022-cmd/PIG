import streamlit as st
import pandas as pd
import sqlite3
from db_handler import get_all_logs, DB_NAME
from alert_handler import fetch_alerts_for_dashboard

# --- 페이지 기본 설정 ---
st.set_page_config(layout="wide", page_title="PIG 보안 모니터링 대시보드", page_icon="🛡️")

# --- 상단 타이틀 및 새로고침 버튼 ---
col_header1, col_header2 = st.columns([8, 1])
with col_header1:
    st.title("🛡️ PIG AI 보안 모니터링 시스템")
with col_header2:
    st.write("") 
    if st.button("🔄 새로고침", use_container_width=True):
        st.rerun()

st.markdown("---")

# --- 1. 데이터 수집 및 전처리 ---
logs = get_all_logs()

# DB 컬럼 개수에 맞춰 유연하게 리스트 설정
columns_list = [
    "timestamp", "user_id", "ip_address", "location", 
    "device_type", "os_type", "browser", "success", "session_duration"
]

if logs:
    col_count = len(logs[0])
    if col_count == 11:
        columns_list = [
            "timestamp", "user_id", "ip_address", "location", 
            "device_type", "os_type", "browser", "success", "session_duration", "risk_score", "status"
        ]
    elif col_count == 10:
        columns_list = [
            "timestamp", "user_id", "ip_address", "location", 
            "device_type", "os_type", "browser", "success", "risk_score", "status"
        ]

# 데이터프레임 생성
df_logs = pd.DataFrame(logs, columns=columns_list)

# 최신 로그 기준 최종 위험 지수 추출
final_score = 0.0
latest_status = "정상"
if not df_logs.empty and 'risk_score' in df_logs.columns:
    try:
        df_logs = df_logs.sort_values(by="timestamp", ascending=False).reset_index(drop=True)
        final_score = float(df_logs['risk_score'].iloc[0])
        latest_status = str(df_logs['status'].iloc[0])
    except Exception:
        final_score = 0.0

# 블랙리스트 데이터 추출 함수
def get_blacklist_data():
    try:
        conn = sqlite3.connect(DB_NAME, timeout=20)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blacklist (
                ip_address TEXT, location TEXT, device_type TEXT, os_type TEXT
            )
        """)
        cursor.execute("SELECT ip_address, location, device_type, os_type FROM blacklist")
        rows = cursor.fetchall()
        return rows
    except sqlite3.Error:
        return []
    finally:
        if 'conn' in locals():
            conn.close()

# 🚨 블랙리스트 최신순(역순)으로 뒤집기
blacklist_rows = get_blacklist_data()[::-1]

# --- 2. 대시보드 화면 구성 (비율 6:3) ---
col1, col2 = st.columns([6, 3])

with col1:
    st.subheader("📊 실시간 시스템 로그인 위험도")
    
    risk_progress_val = max(0.0, min(1.0, final_score / 100.0))
    
    if final_score >= 70.0:
        st.error(f"🚨 **[위험 상태 감지]** 최신 인입 유저 위험지수: {final_score}% ({latest_status})")
        st.progress(risk_progress_val)
    elif final_score >= 40.0:
        st.warning(f"⚠️ **[의심 상태 감지]** 최신 인입 유저 위험지수: {final_score}% ({latest_status})")
        st.progress(risk_progress_val)
    else:
        st.success(f"✅ **[정상 상태 보증]** 최신 인입 유저 위험지수: {final_score}% ({latest_status})")
        st.progress(risk_progress_val)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.subheader("📋 전체 로그인 로그 (real_dataset)")
    if not df_logs.empty:
        st.dataframe(df_logs, use_container_width=True, height=500)
    else:
        st.info("데이터베이스에 아직 수집된 로그인 로그가 없습니다.")

with col2:
    st.subheader("🔔 최근 긴급 알림 발송 내역")
    sent_alerts_db = fetch_alerts_for_dashboard()

    if sent_alerts_db:
        with st.container(height=300, border=True):
            for row in sent_alerts_db:
                st.error(f"🕒 **{row[0]}**\n\n{row[1]}")
    else:
        st.info("발송 완료된 긴급 보안 알림 문자가 없습니다.")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.subheader("🚫 실시간 차단 IP (블랙리스트)")
    if blacklist_rows:
        with st.container(height=250, border=True):
            st.caption("최근에 차단된 기기부터 표시됩니다.")
            total_bl = len(blacklist_rows)
            for idx, row in enumerate(blacklist_rows):
                display_idx = total_bl - idx 
                st.code(
                    f"[{display_idx}] IP: {row[0]}\n지역: {row[1]}\n기기: {row[2]}\nOS: {row[3]}", 
                    language="text"
                )
    else:
        st.success("✅ 현재 탐지 및 등록된 악성 기기가 없습니다.")