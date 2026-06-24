import torch
import torch.nn as nn
import os

class LoginAnomalyDetector(nn.Module):
    """
    유저의 로그인 행동 패턴의 정상성을 판단하는 오토인코더 모델
    """
    def __init__(self, input_dim):
        super(LoginAnomalyDetector, self).__init__()
        #인코더-디코더 뼈대 구조
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, input_dim),
            nn.Sigmoid()
        )

    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x

def get_reconstruction_error(user_id, ip, location, device_type, os_type, browser):
    # 모델에 넣을 feature 개수 9개로 세팅
    model = LoginAnomalyDetector(input_dim=9)
    
    # 학습 모델 불러오기
    if os.path.exists('saved_model.pth'):
        model.load_state_dict(torch.load('saved_model.pth', map_location=torch.device('cpu')))
    model.eval() # 추론 모드로 설정

    # 문자로 된 데이터를 AI가 이해할 수 있게 숫자(0~1 사이)로 임시 변환
    def encode(val):
        return float(abs(hash(str(val))) % 100) / 100.0

    # 9개의 Feature 순서대로 데이터 조립
    live_features = [
        encode("now"),         # timestamp 
        encode(user_id),       # user_id
        encode(ip),            # ip_address
        encode(location),      # location
        encode(device_type),   # device_type
        encode(os_type),       # os_type
        encode(browser),       # browser
        1.0,                   # success (로그인 시도 단계이므로 1로 간주)
        0.0                    # session_duration (방금 접속했으므로 0)
    ]

    # 파이썬 리스트 형태의 데이터를 텐서로 변환
    input_tensor = torch.tensor([live_features], dtype=torch.float32)

    # 모델 추론 및 오차 계산
    with torch.no_grad():
        output = model(input_tensor)
        error = ((input_tensor - output) ** 2).mean().item()
        
    return error