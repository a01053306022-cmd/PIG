# Flask = 서버 만드는 도구
# request = 프론트에서 오는 데이터 받는 도구
# jsonify = 데이터를 JSON 형식으로 변환해서 보내는 도구
from flask import Flask, request, jsonify
import requests # 외부 API 호출할 때 쓰는 도구
import datetime # 현재 시간 가져오는 도구
import sqlite3 # DB 다루는 도구
# 자동으로 0으로 초기화 해주는 도구(IP횟수 셀 때 사용)
from collections import defaultdict 

from detection_model import get_reconstruction_error 
from db_handler import check_blacklist, insert_login_log
from pipeline import process_login_and_alert

app = Flask(__name__) # 앱 초기화

DB_FILE = "login_log.db"

# IP별 로그인 시도 횟수 저장
login_attempts = defaultdict(int)

# 한 번 본 적 있는 (user_id, device_type) 조합을 기억해두는 집합
known_devices = set()

# IP 위치 정보를 저장할 별도 테이블 생성
def init_ip_location_table():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # PRIMARY KEY AUTOINCREMENT = 자동 증가하는 고유 번호
    # checked_at TEXT = 언제 조회/저장했는지 확인
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ip_location (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  
            ip_address TEXT,                       
            country TEXT,                           
            city TEXT,                                
            is_foreign INTEGER,                       
            checked_at TEXT)""")
            
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blacklist (
            ip_address TEXT, location TEXT, device_type TEXT, os_type TEXT
        )
    """)
    conn.commit()
    conn.close()

# IP -> 국가/도시 변환 (ip-api.com 사용)
def get_ip_location(ip):
    # ip-api.com 이라는 무료 API에 IP 주소를 보내서 위치 정보를 요청
    res = requests.get(f"http://ip-api.com/json/{ip}")
    data = res.json()
    
    country = data.get("country")
    city = data.get("city")

    # 해외 여부는 이 함수 안에서 바로 계산해서 함께 저장
    is_foreign = None
    if country is not None:
        is_foreign = "Korea" not in country
    
    # 변환 결과를 ip_location 테이블에 기록
    conn = sqlite3.connect(DB_FILE) 
    cursor = conn.cursor() 
    cursor.execute("""
        INSERT INTO ip_location (ip_address, country, city, is_foreign, checked_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        ip,
        country,
        city,
        int(is_foreign) if is_foreign is not None else None,
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    ))
    conn.commit()
    conn.close()

    return country, city, is_foreign

# db에 이미 저장된 결과를 기준으로 해외 IP 여부를 가져오는 함수
def is_foreign_ip(ip):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT is_foreign FROM ip_location
        WHERE ip_address = ?
        ORDER BY id DESC
        LIMIT 1
    """, (ip,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None  # 아직 한 번도 조회 안 된 IP
    return bool(row[0])

# 반복 로그인 감지 + 블랙리스트 추가 (3회 기준)
def check_and_block(ip, location, device_type, os_type, is_success):
    # db의 blacklist 테이블과 대조 (db_handler.py의 함수 사용)
    if check_blacklist(ip, location, device_type, os_type):
        return "blocked"
    
    if not is_success:
        login_attempts[ip] += 1
    
    if login_attempts[ip] >= 3:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blacklist (
                ip_address TEXT, location TEXT, device_type TEXT, os_type TEXT
            )
        """)
        cursor.execute("INSERT INTO blacklist VALUES (?, ?, ?, ?)", (ip, location, device_type, os_type))
        conn.commit()
        conn.close()
        return "blacklisted"
    return "ok"

# 새 기기인지 판단하는 함수
def check_new_device(user_id, device_type):
    key = (user_id, device_type)
    if key in known_devices:
        return False  # 이미 본 적 있는 조합 -> 새 기기 아님
    known_devices.add(key)
    return True  # 처음 보는 조합 -> 새 기기

# 로그인 API
# "/login" 이라는 주소로 POST 방식 요청이 오면 아래 함수가 실행
@app.route("/login", methods=["POST"])
def login():
    # 프론트엔드(app_login.py)에서 보낸 JSON 데이터를 꺼냄
    data = request.get_json()

    ip = request.remote_addr

    # 현재 시간을 "2026-06-18 14:30" 같은 문자열 형식으로 만듦
    # db의 timestamp 컬럼 형식과 맞추기 위해 이 포맷을 사용
    now = datetime.datetime.now()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 프론트로부터 받은 것 없으면 기본값 "Unknown"
    device_type = data.get("device_type", "Unknown") # 기기 종류
    os_type = data.get("os_type", "Unknown") # 운영체제 종류
    browser = data.get("browser", "Unknown") # 브라우저 종류
    
    user_id = data.get("user_id")
    password_correct = data.get("password_correct", True)

    # IP 변환 + db에 기록
    country, city, is_foreign = get_ip_location(ip)
    location = f"{city}, {country}" if city and country else "Unknown"
    
    # 비정상 시간대 판단 로직 추가
    is_odd_time = 1 <= now.hour <= 5

    # 블랙리스트 차단 확인
    status = check_and_block(ip, location, device_type, os_type, password_correct)
    if status == "blocked":
        # 차단된 경우에도 real_dataset에 기록 (success=FALSE)
        insert_login_log(
            timestamp, user_id, ip, location,
            device_type, os_type, browser,
            "FALSE", 0, 0.0, "차단"
        )
        return jsonify({"status": "blocked"}), 403
    
    # 새 기기 여부 판단
    is_new_device = check_new_device(user_id, device_type)
    
    # AI 모델로부터 실제 오차값 추출
    actual_error = get_reconstruction_error(user_id, ip, location, device_type, os_type, browser)

    # 파이프라인 호출
    pipeline_result = process_login_and_alert(
        user_id=user_id,
        reconstruction_error=actual_error,   
        is_overseas=bool(is_foreign),
        is_new_device=is_new_device,
        fail_count=login_attempts[ip],
        is_odd_time=is_odd_time              
    )

    # real_dataset 테이블에 로그인 기록 저장
    # db_handler.py의 insert_login_log() 사용
    insert_login_log(
        timestamp, user_id, ip, location,
        device_type, os_type, browser,
        "FALSE" if status == "blacklisted" else "TRUE",
        0  # session_duration: 로그인 시점엔 알 수 없어서 0
    )

    # 프론트엔드에 응답 보내기
    return jsonify({
        "status": "ok",
        "country": country,
        "city": city,
        "foreign_ip": is_foreign,
        "blacklisted": status == "blacklisted",
        "risk_result": pipeline_result
    })

# 서버 실행 부분
if __name__ == "__main__":
    init_ip_location_table()  # 서버 시작할 때 ip_location 테이블 없으면 생성
    app.run(debug=True)