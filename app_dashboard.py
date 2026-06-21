import streamlit as st
import pandas as pd
import sqlite3
from db_handler import get_all_logs, DB_NAME
from alert_handler import fetch_alerts_for_dashboard
sent_alerts = fetch_alerts_for_dashboard()


# 위험지수 함수(risk_calculator) 연동
try:
    from risk_calculator import calculate_risk_score  
    final_score = calculate_risk_score()             
except:
    final_score = -1.0  

# 테스트용 고정값
# final_score = 86.0
# ==============================================================================

st.set_page_config(layout="wide", page_title="보안 모니터링 대시보드")

# 데이터 수집
logs = get_all_logs()
columns_list = [
    "timestamp", "user_id", "ip_address", "location", 
    "device_type", "os_type", "browser", "success", "session_duration"
]
df_logs = pd.DataFrame(logs, columns=columns_list)

# blacklist 테이블에서 내용 추출
def get_blacklist_data():
    conn = sqlite3.connect(DB_NAME, timeout=20)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blacklist (
            ip_address TEXT, location TEXT, device_type TEXT, os_type TEXT
        )
    """)
    cursor.execute("SELECT ip_address, location, device_type, os_type FROM blacklist")
    rows = cursor.fetchall()
    conn.close()
    return rows

blacklist_rows = get_blacklist_data()

# 화면 분할 (5:2)
col1, col2 = st.columns([5, 2])

with col1:
    st.markdown("### 시스템 위험지수 상태")
    
    if final_score < 0:
        st.progress(0.0, text=f"🚨 연동 실패 오류 (에러 코드: {int(final_score)})")
    else:
        risk_progress_val = float(final_score) / 100.0
        risk_progress_val = max(0.0, min(1.0, risk_progress_val))
        st.progress(risk_progress_val, text=f"현재 위험지수: {final_score}%")
        
    st.markdown("---") # 구분을 위한 얇은 가로선
    
    st.markdown("### real_dataset 테이블 전체 로그")
    if not df_logs.empty:
        st.dataframe(df_logs, use_container_width=True, height=500)
    else:
        st.info("real_dataset 테이블에 아직 수집된 데이터가 없습니다.")

with col2:
    # 섹션 타이틀 크기 통일은 그대로 유지
    st.markdown("### 최근 알림 내역")
    
    # DB에서 alert 테이블 읽어오기
    def get_real_sent_alerts():
        conn = sqlite3.connect(DB_NAME, timeout=20)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                timestamp TEXT, user_id TEXT, message_content TEXT
            )
        """)
        # 가장 최근에 발송된 문자 내역이 맨 위로 오도록 최신순 조회
        cursor.execute("SELECT timestamp, message_content FROM alerts ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows

    sent_alerts = get_real_sent_alerts()

    if sent_alerts:
        for row in sent_alerts:
            # row: 발송 시간, row: 실제 발송된 문자 내용 전체
            st.error(f"[{row}] {row}")
    else:
        st.info("현재까지 실제로 발송 완료된 긴급 보안 알림 문자가 없습니다.")
        
    st.markdown("---")
    
    st.markdown("### 실시간 블랙리스트")
    if blacklist_rows:
        st.caption("현재 login_log.db의 blacklist 테이블에 등록된 차단 기기 조건입니다.")
        for idx, row in enumerate(blacklist_rows):
            st.code(
                f"[{idx+1}] IP: {row[0]} | 지역: {row[1]} | 기기: {row[2]} | OS: {row[3]}", 
                language="text"
            )
    else:
        st.success("✅ 현재 탐지 및 등록된 블랙리스트 기기가 없습니다.")
