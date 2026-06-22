import sqlite3
from datetime import datetime

DB_NAME = "login_log.db"

def save_sent_alert(user_id, final_score):

    conn = sqlite3.connect(DB_NAME, timeout=20)
    cursor = conn.cursor()
    
    # 테이블이 없으면 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            timestamp TEXT,
            user_id TEXT,
            message_content TEXT
        )
    """)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    # alert notifier 코드의 양식과 완전히 동일하게 메시지 텍스트 조립
    sms_text = f"🚨 [PIG 보안 시스템] {user_id} 계정의 해킹 위험 지수가 {final_score}%입니다. 즉시 비밀번호를 변경해주세요!"
    
    cursor.execute("""
        INSERT INTO alerts (timestamp, user_id, message_content)
        VALUES (?, ?, ?)
    """, (timestamp, user_id, sms_text))
    
    conn.commit()
    conn.close()

def fetch_alerts_for_dashboard():
    # app_dashboard로 전달
    conn = sqlite3.connect(DB_NAME, timeout=20)
    cursor = conn.cursor()
    
    # 예외 방지용 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            timestamp TEXT, user_id TEXT, message_content TEXT
        )
    """)
    
    # 최신 알림 내역이 맨 위로 오도록 정렬하여 전체 조회
    cursor.execute("SELECT timestamp, message_content FROM alerts ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return rows # 대시보드가 읽어갈 리스트 리턴
