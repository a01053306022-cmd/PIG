import sqlite3
import pandas as pd

# DB 연결
logdata = sqlite3.connect('login_log.db')

# train_dataset 전체 추출 및 CSV 저장
train_dataset_df = pd.read_sql("SELECT * FROM train_dataset", con=logdata)
train_dataset_df.to_csv("train_data.csv", index=False)

# test_dataset 전체 추출 및 CSV 저장
test_dataset_df = pd.read_sql("SELECT * FROM test_dataset", con=logdata)
test_dataset_df.to_csv("test_data.csv", index=False)

# 연결 종료
logdata.close()
