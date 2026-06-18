def calculate_risk_score(reconstruction_error, is_overseas, is_new_device, fail_count, is_odd_time):
    """
    AI 모델의 복원 오차와 보안 가중치 항목들을 합산하여 최종 위험 지수(%)를 산출하는 함수
    """
    # 기본 AI 오차 가중치 계산 (최대 40점)
    base_score = min(reconstruction_error * 15, 40)
    
    # 정황 가중치 합산
    if is_overseas:
        base_score += 25
    if is_new_device:
        base_score += 15
    if is_odd_time:
        base_score += 10
        
    # 로그인 실패 횟수 추가 가중치
    base_score += (fail_count * 5)
    
    # 최종 점수는 100%를 넘지 않도록 제한
    final_score = min(base_score, 100)
    return round(final_score, 1)