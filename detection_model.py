import torch
import torch.nn as nn

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