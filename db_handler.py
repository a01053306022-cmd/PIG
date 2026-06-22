import sqlite3

DB_NAME = "login_log.db"

def init_db():
    """real_dataset 테이블이 없을 경우 최초 1회 생성"""
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
            session_duration INTEGER
        )
    """)
    conn.commit()
    conn.close()

def check_blacklist(ip_address, location, device_type, os_type):
    """login_log.db 파일 안의 blacklist 테이블과 로그인 시도 정보 대조"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 예외 방지: 만약 blacklist 테이블이 없다면 자동 생성
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
    conn.close()
    
    return count > 0

def insert_login_log(timestamp, user_id, ip_address, location, device_type, os_type, browser, success, session_duration):
    """real_dataset 테이블에 실시간 수집된 9개 데이터 삽입"""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO real_dataset (timestamp, user_id, ip_address, location, device_type, os_type, browser, success, session_duration)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, user_id, ip_address, location, device_type, os_type, browser, success, session_duration))
    
    conn.commit()
    conn.close()

def get_all_logs():
    """대시보드 표 출력용 데이터 전체 조회"""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, user_id, ip_address, location, device_type, os_type, browser, success, session_duration FROM real_dataset ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows
