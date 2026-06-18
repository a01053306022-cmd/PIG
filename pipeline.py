# 내가 만든 파일(모듈)들로부터 함수 가져오기
from risk_calculator import calculate_risk_score
from alert_notifier import send_emergency_sms

# 로그인 결과 저장용 DB 역할 리스트
risk_score_db = []

def process_login_and_alert(user_id, reconstruction_error, is_overseas, is_new_device, fail_count, is_odd_time):
    # 1. 종합 위험 지수 계산
    final_score = calculate_risk_score(reconstruction_error, is_overseas, is_new_device, fail_count, is_odd_time)
    status = "정상"
    
    # 비정상적 로그인 발생 시 알림
    if reconstruction_error >= 3.0:
        status = "의심"
        print(f"⚠️ [알림] AI 패턴 이상 감지: '{user_id}'의 평소 접속 패턴과 다릅니다. (오차: {reconstruction_error})")
        # 내부 보안 로그를 남기거나 프론트엔드로 UI 경고 신호를 보낼 때 사용

    # 위험지수 특정값 도달 시 알림
    if final_score >= 70:
        status = "위험"
        print(f"🚨 [알림] 위험 지수 돌파: '{user_id}' 계정의 위험도가 {final_score}%에 도달했습니다.")
        # 솔라피 문자 발송 모듈 호출
        send_emergency_sms(user_id, final_score)
        
    # 2. 결과를 딕셔너리로 묶어서 임시 DB에 저장 및 반환
    login_record = {
        'user_id': user_id,
        'ai_anomaly': "비정상" if reconstruction_error >= 3.0 else "정상",
        'risk_score': final_score,
        'status': status
    }
    risk_score_db.append(login_record)
    
    return login_record