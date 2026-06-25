# 26-1 오픈소스프로그래밍 기말 팀 프로젝트 <계정 해킹 위험도 분석 서비스>
### PIG (2514549 이채영, 2511283 서호연, 2515180 이세나)

---

### 1. 프로젝트 요약 및 성과

프로젝트 목적: 실시간 로그인 기록을 바탕으로 계정 해킹 위험도를 분석하는 서비스를 구축하여 단순히 ID-PW 조합만을 확인하는 정적 방어 체계의 한계를 극복하고 오픈소스를 활용한 기술의 안정적 융합을 도모하고자 함. 더불어 사이버 개인정보 침해 사고 감소 문제의 해결책을 제시함으로써 현존하는 플랫폼 전반의 계정 보안 수준의 상향 평준화를 지향, 사회적 비용 감소로 귀결될 수 있도록 기여하고자 함.

서비스 기능 요약: 고성능의 이상 탐지 모델을 구축하여 비정상적 로그인을 감지하고 사용자에게 경고 알림을 전송하며, 실시간 로그인 기록에 대한 위험 지수를 계산하여 대시보드에 표현함. 특정 %마다 사용자에게 경고 알림을 전송하여 개인정보 침해 사고에 대한 경각심 도모 및 문제 해소의 기회를 제공함. 비정상 로그인 기록 데이터를 통해 해킹 유저를 판단하여 자동 차단 기능을 실행하여 계정 보안 수준을 증대함.

모델 성능 지표: 
- `PR-AUC`: 약 `0.9484` (테스트 데이터셋이 TRUE:FALSE=84770:3503으로 한쪽에 매우 치우친 형태이므로 AUC-ROC 대신 PR-AUC를 성능 지표로 사용함.)
- `Precision`: 약 `0.9545`
- `Recall`: 약 `0.8676`

---

### 2. 데이터셋 및 분석 모델 요약

학습 데이터: kaggle의 공개 데이터셋 [Authentication & Authorization Failures Dataset](https://www.kaggle.com/datasets/mirzayasirabdullah07/authentication-and-authorization-failures-dataset) 에서 필요한 column만을 취사선택하여 사용. 

테스트 데이터: Google Takeout 기능을 사용해 팀원 3인의 구글 계정 로그인 기록을 다운로드한 후 필요한 column만을 선택, 공란을 임의로 채워 데이터셋을 구축.

모델 기반 서비스 설명: 정상적인 유저의 로그인 패턴을 학습한 모델이, 평소와 다른 접속 시도에 대해 '오차값'을 기준으로 반응. 오차값이 클수록 해킹 시도일 가능성을 높이 판별하여 위험도를 계산. 모델이 산출한 오차값은 파이프라인으로 전달되어 위치 및 시간대 등의 기타 요소와 결합, 최종 위험 지수를 도출.

---

### 3. 역할 분담 내역

이채영(팀장)([@a01053306022-cmd](https://github.com/a01053306022-cmd)): 데이터셋 구축 및 프론트엔드
- (dataset) `login_log.db`: 메인 데이터베이스 파일
- (dataset) `data.py`: 학습 및 테스트 데이터셋을 CSV 파일로 가공(전처리)
- (prontend) `app_login.py`: 실시간 로그인 기록을 받아오기 위한 임시 사이트로, 백엔드와 실시간 연결됨
- (prontend) `app_dashboard.py`: 위험 지수 및 실시간 로그인 로그, 블랙리스트 현황 표시
- (prontend) `db_handler.py`: python-db 파일 간 연결성 보장
- (prontend) `alert_handler.py`: db에 저장된 알림 전송 내역을 대시보드에 표시
 
서호연([@standuphy](https://github.com/standuphy)): 백엔드-모델 구축 및 학습, 테스트
- (backend-alarm) `alert_notifier.py`: 위험 지수 상승 시 사용자에게 알림 전송
- (backend-alarm) `detection_model.py`: 로그인 기록의 해킹 의심 정도를 판별하는 이상 탐지 모델
- (backend-alarm) `pipeline.py`: 최종 위험 지수 산출
- (backend-alarm) `risk_calculator.py`: pipeline.py에 위험도 수치 산정 공식 및 임계치를 전달
- (backend-alarm) `train.py`: 모델 학습 및 블랙리스트 업데이트
- (backend-alarm) `saved_model.pth`: 학습 완료된 모델의 가중치 저장 파일

이세나([@i4302904-source](https://github.com/i4302904-source)): 백엔드-서버 구축 및 모델 연결
- (master) `app.py`: 프론트엔드와 이상 탐지 모델 간의 요청 조율 및 전체 시스템 운영—로그인 정보를 받아 IP를 국가 및 지역 정보로 변환해 db에 저장, 블랙리스트 조회를 통한 IP 접속 차단, 이상 탐지 모델과 파이프라인 간 연결, 로그인 시도 결과 및 위험 지수를 db에 저장 등

---

### 4. 기타

협업 관리용 노션: [https://notion.com](https://app.notion.com/p/PIG-365c9a45261180f79d38e971e462c51a?source=copy_link)

관련 파일 드라이브: [https://drive.google.com](https://drive.google.com/drive/folders/13qgx2alCxuCzLqhbolwsq_JmOUzRnpjO?usp=drive_link)
