# Flask = 서버 만드는 도구
# request = 프론트에서 오는 데이터 받는 도구
# jsonify = 데이터를 JSON 형식으로 변환해서 보내는 도구
from flask import Flask, request, jsonify
import requests # 외부 API 호출할 때 쓰는 도구
import datetime # 현재 시간 가져오는 도구
import sqlite3 # DB 다루는 도구
# 자동으로 0으로 초기화 해주는 도구(IP횟수 셀 때 사용)
from collections import defaultdict 

app = Flask(__name__) # 앱 초기화

DB_FILE = "login_log.db"

# IP별 로그인 시도 횟수 저장
login_attempts = defaultdict(int)
# 차단된 IP 목록
blacklist = set()

# IP -> 국가/도시 변환 (ip-api.com 사용)
def get_ip_location(ip):
    # ip-api.com 이라는 무료 API에 IP 주소를 보내서 위치 정보를 요청
    res = requests.get(f"http://ip-api.com/json/{ip}")
    # API가 보내준 응답을 JSON(딕셔너리 형태)으로 변환
    data = res.json()
    return data.get("country"), data.get("city")

# 해외 IP 여부 판단 (db의 location은 "도시, Korea" 형식 -> "South Korea" 아님)
def is_foreign_ip(country):
    # ip-api.com은 "South Korea"로 반환하지만, db 표기는 "Korea" 이므로 맞춰서 비교
    if country is None:
        return None
    return "Korea" not in country

# 반복 로그인 감지 + 블랙리스트 추가 (3회 기준)
def check_and_block(ip):
    if ip in blacklist:
        return "blocked"
    
    login_attempts[ip] += 1

    if login_attempts[ip] >= 3:
        blacklist.add(ip)
        return "blacklisted"
    
    # 3회 미만이면 -> 아직은 정상적인 시도로 판단
    return "ok"

# 로그인 API
# "/login" 이라는 주소로 POST 방식 요청이 오면 아래 함수가 실행
@app.route("/login", methods=["POST"])
def login():
    # 프론트엔드(Streamlit)에서 보낸 JSON 데이터를 꺼냄
    data = request.get_json()

    ip = request.remote_addr

    # 현재 시간을 "2026-06-18 14:30" 같은 문자열 형식으로 만듦
    # db의 timestamp 컬럼 형식과 맞추기 위해 이 포맷을 사용
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 프론트로부터 받은 것 없으면 기본값 "Unknown"
    device_type = data.get("device_type", "Unknown") # 기기 종류
    os_type = data.get("os_type", "Unknown") # 운영체제 종류
    browser = data.get("browser", "Unknown") # 브라우저 종류
    
    user_id = data.get("user_id")

    # 블랙리스트 차단 확인
    status = check_and_block(ip)
    if status == "blocked":
        return jsonify({"status": "blocked"}), 403

    # IP -> 국가/도시 변환
    country, city = get_ip_location(ip)
    foreign = is_foreign_ip(country)
    location = f"{city}, {country}" if city and country else "Unknown"

    # 데이터베이스에 로그인 기록 저장
    conn = sqlite3.connect(DB_FILE) # db 파일 연결
    cursor = conn.cursor() # db에 명령을 내릴 수 있는 커서 객체 생성

    # train_dataset 테이블에 새로운 한 줄(row)을 추가하는 SQL문 실행
    # 물음표(?)는 나중에 나오는 튜플 값들이 순서대로 들어가는 자리(보안상 안전한 방식)
    cursor.execute("""
        INSERT INTO train_dataset
        (timestamp, user_id, ip_address, location, device_type, os_type, browser, success, session_duration, target)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp,
        user_id,
        ip,
        location,
        device_type,
        os_type,
        browser,
        "FALSE" if status == "blacklisted" else "TRUE",
        0,  # session_duration은 로그인 시점엔 알 수 없어서 0으로 기본값
        "TRUE" if status == "blacklisted" else "FALSE"
    ))
    conn.commit() # 위에서 실행한 INSERT 내용을 실제로 db 파일에 저장
    conn.close() # db 연결 종료

    # 프론트엔드에 응답 보내기
    return jsonify({
        "status": "ok",
        "country": country,
        "city": city,
        "foreign_ip": foreign,
        "blacklisted": status == "blacklisted"
    })

# 서버 실행 부분
if __name__ == "__main__":
    app.run(debug=True)