import data
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from detection_model import LoginAnomalyDetector
from sklearn.preprocessing import MinMaxScaler


train_df = pd.read_csv('train_data.csv')
test_df = pd.read_csv('test_data.csv')

train_len = len(train_df)

# 두 데이터셋을 위아래로 합침
combined_df = pd.concat([train_df, test_df], axis=0, ignore_index=True)

# 합쳐진 하나의 데이터 통에서 결측치 채우기 진행
combined_df = combined_df.fillna(0)

for col in combined_df.columns:
    if combined_df[col].dtype == 'object' or combined_df[col].dtype == 'bool':
        combined_df[col] = combined_df[col].astype('category').cat.codes

combined_df = combined_df.astype('float32')

train_df = combined_df.iloc[:train_len].copy()
test_df = combined_df.iloc[train_len:].copy()

scaler = MinMaxScaler()
scaled_train = scaler.fit_transform(train_df.values)
scaled_test = scaler.transform(test_df.values)

INPUT_DIM = train_df.shape[1] 
print(f"감지된 데이터 Feature(특징) 개수: {INPUT_DIM}")

# 데이터프레임을 PyTorch 텐서로 변환
X_train = torch.tensor(scaled_train, dtype=torch.float32)
X_test = torch.tensor(scaled_test, dtype=torch.float32)

# 모델, 손실함수, 최적화 도구 설정
model = LoginAnomalyDetector(input_dim=INPUT_DIM)
criterion = nn.MSELoss() # 오토인코더의 핵심인 복원 오차 계산기
optimizer = optim.Adam(model.parameters(), lr=0.001)

# 모델 학습 진행
EPOCHS = 100
print("\n학습 시작")
for epoch in range(EPOCHS):
    model.train()
    outputs = model(X_train)
    loss = criterion(outputs, X_train) # 입력값과 출력값의 차이를 최소화하도록 학습
    
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    if (epoch + 1) % 10 == 0:
        print(f"Epoch [{epoch+1}/{EPOCHS}], Loss(훈련 오차): {loss.item():.6f}")

# 학습된 가중치를 파일로 저장
torch.save(model.state_dict(), 'saved_model.pth')
print("모델 학습 완료: 'saved_model.pth' 가중치 파일이 저장되었습니다.")    #detection_model.py에서 불러다 씀

# 테스트 데이터셋으로 정확도/성능 확인
model.eval()
with torch.no_grad():
    test_outputs = model(X_test)
    test_loss = criterion(test_outputs, X_test)
    
    print("\n==================================================")
    print("[모델 테스트 결과]")
    print(f"- 사용된 학습 데이터 개수: {len(X_train)}건")
    print(f"- 사용된 테스트 데이터 개수: {len(X_test)}건")
    print(f"- 최종 테스트 데이터셋 MSE Loss (복원 오차): {test_loss.item():.6f}")
    print("==================================================")