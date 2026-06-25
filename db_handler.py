import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "login_log.db")

def init_db():
    """real_dataset 테이블이 없을 경우 최초 1회 생성 (11개 컬럼)"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS real_dataset (
                timestamp TEXT,
                user_id TEXT,
                ip_address TEXT,
                location TEXT,
                device_type TEXT,
                os_type TEXT,
                browser TEXT,
                success TEXT,
                session_duration INTEGER,
                risk_score REAL,
                status TEXT
            )
        """)
        conn.commit()
    except sqlite3.Error as e:
        print(f"[DB 에러] init_db 실패: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def check_blacklist(ip_address, location, device_type, os_type):
    """login_log.db 파일 안의 blacklist 테이블과 로그인 시도 정보 대조"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blacklist (
                ip_address TEXT,
                location TEXT,
                device_type TEXT,
                os_type TEXT
            )
        """)
        
        query = """
            SELECT COUNT(*) FROM blacklist 
            WHERE ip_address = ? 
              AND location = ? 
              AND (device_type = ? OR os_type = ?)
        """
        
        cursor.execute(query, (ip_address, location, device_type, os_type))
        count = cursor.fetchone()[0]
        return count > 0
    except sqlite3.Error as e:
        print(f"[DB 에러] check_blacklist 실패: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def insert_login_log(timestamp, user_id, ip_address, location, device_type, os_type, browser, success, session_duration, risk_score, status):
    """real_dataset 테이블에 실시간 수집된 11개 데이터 삽입"""
    init_db()
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO real_dataset (
                timestamp, user_id, ip_address, location, device_type, 
                os_type, browser, success, session_duration, risk_score, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, user_id, ip_address, location, device_type, os_type, browser, success, session_duration, risk_score, status))
        
        conn.commit()
        return True 
    except sqlite3.Error as e:
        print(f"[DB 에러] insert_login_log 실패: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False 
    finally:
        if 'conn' in locals():
            conn.close()

def get_all_logs():
    """대시보드 표 출력용 데이터 전체 조회 (11개 컬럼)"""
    init_db()
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, user_id, ip_address, location, device_type, 
                   os_type, browser, success, session_duration, risk_score, status 
            FROM real_dataset 
            ORDER BY timestamp DESC
        """)
        rows = cursor.fetchall()
        return rows
    except sqlite3.Error as e:
        print(f"[DB 에러] get_all_logs 실패: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def sync_login_record_to_main_db(login_record_db_path="login_record.db"):
    """
    임시 login_record.db의 값을 메인 login_log.db의 real_dataset 테이블에 이관
    (명시된 9개 컬럼만 삽입하며 나머지 2개는 빈값으로 처리됨)
    """
    if not os.path.isabs(login_record_db_path):
        login_record_db_path = os.path.join(BASE_DIR, login_record_db_path)
        
    if not os.path.exists(login_record_db_path):
        print(f"[동기화 알림] 임시 파일({login_record_db_path})이 존재하지 않아 동기화를 건너뜁니다.")
        return False

    init_db()  
    
    src_conn = None
    dest_conn = None
    try:
        src_conn = sqlite3.connect(login_record_db_path)
        src_cursor = src_conn.cursor()
        
        src_cursor.execute("SELECT timestamp, user_id, ip_address, location, device_type, os_type, browser, success, session_duration FROM login_record")
        records = src_cursor.fetchall()
        
        if not records:
            print("[동기화 알림] 이관할 임시 레코드가 없습니다.")
            return True

        dest_conn = sqlite3.connect(DB_NAME)
        dest_cursor = dest_conn.cursor()
        
        dest_cursor.executemany("""
            INSERT INTO real_dataset (timestamp, user_id, ip_address, location, device_type, os_type, browser, success, session_duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, records)
        
        dest_conn.commit()
        print(f"[동기화 성공] {len(records)}개의 로그인 기록을 login_log.db로 완벽히 이관했습니다!")
        
        src_conn.close()
        os.remove(login_record_db_path)
        print("[동기화 완료] 중복 충돌을 방지하기 위해 임시 login_record 파일을 삭제했습니다.")
        return True

    except sqlite3.Error as e:
        print(f"[동기화 치명적 에러] 데이터 이관 실패: {e}")
        if dest_conn:
            dest_conn.rollback()
        return False
    finally:
        if src_conn and src_conn.fp: 
            src_conn.close()
        if dest_conn:
            dest_conn.close()