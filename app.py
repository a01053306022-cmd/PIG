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

login_attempts = defaultdict(int) # IP별 로그인 시도 횟수 저장
blacklist = set() # 차단된 IP목록 저장

# DB 초기화
def init_db():
    conn = sqlite3.connect("pig.db") # pig.db 파일 열기(없으면 자동 생성)
    cursor = conn.cursor() #DB에 명령 내릴 수 있는 커서 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            ip TEXT,
            country TEXT,
            city TEXT,
            device TEXT,
            time TEXT,
            is_foreign INTEGER,
            is_blocked INTEGER)""")
    conn.commit() # 변경사항 저장
    conn.close() # DB 연결 닫기

# IP -> 국가/도시 변환
def get_ip_location(ip):
    res = requests.get(f"http://ip-api.com/json/{ip}")
    data = res.json()
    return data.get("country"), data.get("city")

# 해외 IP 여부 판단
def is_foreign_ip(country):
    if country != "South Korea":
        return True
    return False

# 반복 감지 + 블랙리스트 추가 (3회 기준)
def check_and_block(ip):
    # 이미 블랙리스트에 있으면 차단
    if ip in blacklist:
        return "blocked"
    
    # 시도 횟수 1 증가
    login_attempts[ip] += 1

    # 3회 이상이면 블랙리스트 추가
    if login_attempts[ip] >= 5:
        blacklist.add(ip)
        return "blacklisted"
    
    return "ok"

# 로그인 API
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    # 프론트에서 받은 데이터
    ip = request.remote_addr
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    device = data.get("device")
    username = data.get("username")

    # 블랙리스트 차단 확인
    status = check_and_block(ip)
    if status == "blocked":
        # DB에 차단 기록 저장
        conn = sqlite3.connect("pig.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO login_log VALUES (NULL, ?, ?, NULL, NULL, ?, ?, NULL, 1)",
                       (username, ip, device, time))
        conn.commit()
        conn.close()
        return jsonify({"status": "blocked"}), 403

    # IP → 국가/도시 변환
    country, city = get_ip_location(ip)
    
    # 해외 IP 여부 확인
    foreign = is_foreign_ip(country)

    # DB에 로그인 기록 저장
    conn = sqlite3.connect("pig.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO login_log VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, 0)",
                   (username, ip, country, city, device, time, int(foreign)))
    conn.commit()
    conn.close()

    # 프론트에 응답 전송
    return jsonify({
        "status": "ok",
        "country": country,
        "city": city,
        "foreign_ip": foreign,          # 해외 IP 여부
        "blacklisted": status == "blacklisted"  # 방금 블랙리스트 추가됐는지
    })

if __name__ == "__main__":
    init_db()
    app.run(debug=True)