import data
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from detection_model import LoginAnomalyDetector
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import average_precision_score, precision_score, recall_score


train_df = pd.read_csv('train_data.csv')
test_df = pd.read_csv('test_data.csv')

# target 채점용으로 뺌
test_targets = test_df['target'].map({'TRUE': 1, 'FALSE': 0, True: 1, False: 0}).values

# target FALSE인 데이터만 살림
train_df = train_df[train_df['target'].isin([False, 'FALSE', 0, '0'])]

train_df = train_df.drop(columns=['target'])
test_df = test_df.drop(columns=['target'])

# 원래 크기 기억
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

print("\n====================================================================")
print("모델 학습 완료: 'saved_model.pth' 가중치 파일이 저장되었습니다.")
print("====================================================================\n")

# 테스트 데이터셋으로 정확도/성능 확인
model.eval()
with torch.no_grad():
    test_outputs = model(X_test)
    test_loss = criterion(test_outputs, X_test) #전체 평균 오차

    # 데이터 복원 오차 계산
    sample_losses = torch.mean((test_outputs - X_test)**2, dim=1).numpy()
    
    # PR-AUC 계산
    pr_auc = average_precision_score(test_targets, sample_losses)

    # Precision, Recall 계산을 위한 커트라인 설정, 정상 데이터만 있는 train의 오차 중 상위 5%를 해킹 커트라인으로
    train_outputs = model(X_train)
    train_losses = torch.mean((train_outputs - X_train)**2, dim=1).numpy()
    threshold = np.percentile(train_losses, 95)

    # 커트라인 넘으면 해킹(1), 아니면 정상(0)으로 판단
    predictions = (sample_losses > threshold).astype(int)
    
    precision = precision_score(test_targets, predictions)
    recall = recall_score(test_targets, predictions)

    print("\n====================================================================")
    print("[모델 테스트 결과]")
    print("--------------------------------------------------------------------")
    print(f"- 사용된 학습 데이터 개수: {len(X_train)}건")
    print(f"- 사용된 테스트 데이터 개수: {len(X_test)}건")
    print(f"- 최종 테스트 데이터셋 MSE Loss (복원 오차): {test_loss.item():.6f}")
    print("--------------------------------------------------------------------")
    print(f"PR-AUC (전반적 탐지 성능): {pr_auc:.4f}")
    print(f"Precision (정밀도): {precision:.4f}")
    print(f"Recall (재현율): {recall:.4f}")
    print("====================================================================")