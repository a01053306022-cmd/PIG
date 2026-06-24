import streamlit as st
import requests
import platform

st.set_page_config(page_title="PIG 로그인", page_icon="🔒")

st.title("🔒 PIG 서비스 로그인")
st.caption("AI 보안 모니터링 테스트 화면입니다.")

# 비밀번호 입력칸 추가
user_id = st.text_input("아이디")
password = st.text_input("비밀번호", type="password")

st.write("---")
st.write("🛠️ **테스트용 시뮬레이션 버튼**")

col1, col2 = st.columns(2)

with col1:
    success_btn = st.button("✅ 정상 로그인 시도", use_container_width=True)
with col2:
    fail_btn = st.button("❌ 일부러 비밀번호 틀리기", use_container_width=True)

if success_btn or fail_btn:
    if not user_id:
        st.warning("아이디를 입력해 주세요.")
    else:
        # 실패 버튼을 눌렀는지 여부를 서버로 같이 넘겨줌
        is_success = True if success_btn else False
        
        # 서버로 보낼 데이터 포맷
        data = {
            "user_id": user_id,
            "password_correct": is_success,  # 핵심: 성공/실패 여부 플래그
            "device_type": "PC", # 모바일/PC 구분용 임시값
            "os_type": platform.system(),
            "browser": "Chrome"
        }
        
        try:
            # 백엔드(app.py)로 전송
            res = requests.post("http://127.0.0.1:5000/login", json=data)
            
            # 서버에서 차단 먹인 경우 (HTTP 403)
            if res.status_code == 403:
                st.error("🚨 보안 시스템에 의해 차단된 IP입니다. (3회 이상 실패 또는 해킹 의심)")
            else:
                result = res.json()
                
                # 버튼 누른 거에 맞춰서 메시지 다르게 띄워주기
                if not is_success:
                    st.warning("비밀번호가 틀렸습니다. (서버에 로그인 실패 카운트 누적됨)")
                else:
                    st.success("로그인 성공!")
                    st.info(f"방금 로그인의 AI 위험지수: {result.get('risk_result', {}).get('risk_score', 0)}%")
                    
        except Exception as e:
            st.error(f"서버랑 연결이 안 돼. app.py가 켜져 있는지 확인해봐! (에러: {e})")