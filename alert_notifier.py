from solapi import SolapiMessageService
from solapi.model import RequestMessage

# 솔라피 API 인증 정보 설정
API_KEY = "여기에_발급받은_API_KEY_입력"
API_SECRET = "여기에_발급받은_API_SECRET_입력"
MY_NUMBER = "01012345678"  # 솔라피에 등록한 발신자 번호

def send_emergency_sms(user_id, final_score):
    """
    위험 지수 특정값 도달 시 유저에게 긴급 경고 문자를 발송하는 함수
    """
    message_service = SolapiMessageService(api_key=API_KEY, api_secret=API_SECRET)
    sms_text = f"🚨 [PIG 보안 시스템] {user_id} 계정의 해킹 위험 지수가 {final_score}%입니다. 즉시 비밀번호를 변경해주세요!"
    
    try:
        message = RequestMessage(from_=MY_NUMBER, to=MY_NUMBER, text=sms_text)
        message_service.send(message)
        print(f"[{user_id}] 문자 전송 완료!")
        return True
    except Exception as e:
        print(f"문자 전송 실패: {e}")
        return False