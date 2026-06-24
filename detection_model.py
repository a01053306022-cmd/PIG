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

def get_reconstruction_error(input_data):
    # 모델에 넣을 feature 개수 임시로 5개 세팅
    model = LoginAnomalyDetector(input_dim=5)
    
    # 학습 모델 불러오기
    if os.path.exists('saved_model.pth'):
        model.load_state_dict(torch.load('saved_model.pth'))
    model.eval() # 추론 모드로 설정

    # app.py의 파이썬 리스트 형태의 데이터를 텐서로 변환
    if not isinstance(input_data, torch.Tensor):
        input_data = torch.tensor(input_data, dtype=torch.float32)

    # 모델 추론 및 오차 계산
    with torch.no_grad():
        output = model(input_data)
        error = ((input_data - output) ** 2).mean().item()
        
    return error