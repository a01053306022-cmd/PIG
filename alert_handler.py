import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "login_log.db")

def save_sent_alert(user_id, final_score):
    """보안 위반 알림 내역을 DB에 저장"""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=20)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                timestamp TEXT,
                user_id TEXT,
                message_content TEXT
            )
        """)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        sms_text = f"🚨 [PIG 보안 시스템] {user_id} 계정의 해킹 위험 지수가 {final_score}%입니다. 즉시 비밀번호를 변경해주세요!"
        
        cursor.execute("""
            INSERT INTO alerts (timestamp, user_id, message_content)
            VALUES (?, ?, ?)
        """, (timestamp, user_id, sms_text))
        
        conn.commit()
        print(f"[알림 핸들러] 알림 저장 완료 - User: {user_id}")
        return True # 성공 결과 반환
    except sqlite3.Error as e:
        print(f"[DB 에러] save_sent_alert 실패: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False # 실패 결과 반환
    finally:
        if 'conn' in locals():
            conn.close()

def fetch_alerts_for_dashboard():
    """대시보드가 읽어갈 최신 알림 내역 리스트 리턴"""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=20)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                timestamp TEXT, user_id TEXT, message_content TEXT
            )
        """)
        
        cursor.execute("SELECT timestamp, message_content FROM alerts ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        return rows 
    except sqlite3.Error as e:
        print(f"[DB 에러] fetch_alerts_for_dashboard 실패: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()
