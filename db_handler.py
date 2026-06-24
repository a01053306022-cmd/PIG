import sqlite3

DB_NAME = "login_log.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 🚨 risk_score, status 컬럼 추가
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS real_dataset (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blacklist (
            ip_address TEXT,
            location TEXT,
            device_type TEXT,
            os_type TEXT
        )
    ''')

    conn.commit()
    conn.close()

# 🚨 매개변수 11개로 확장
def insert_login_log(timestamp, user_id, ip_address, location, device_type, os_type, browser, success, session_duration, risk_score, status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO real_dataset (
            timestamp, user_id, ip_address, location, device_type, 
            os_type, browser, success, session_duration, risk_score, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, user_id, ip_address, location, device_type, os_type, browser, success, session_duration, risk_score, status))
    conn.commit()
    conn.close()

def check_blacklist(ip_address, location, device_type, os_type):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM blacklist 
        WHERE ip_address = ? OR (location = ? AND device_type = ? AND os_type = ?)
    ''', (ip_address, location, device_type, os_type))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# 🚨 SELECT 할 때 새로 추가한 컬럼들도 전부 불러오기
def get_all_logs():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, user_id, ip_address, location, device_type, 
               os_type, browser, success, session_duration, risk_score, status 
        FROM real_dataset 
        ORDER BY id DESC
    ''')
    logs = cursor.fetchall()
    conn.close()
    return logs