"""
Создание тестовой модели с сохранением пайплайна предобработки.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import joblib

np.random.seed(42)
n_samples = 1000

# Синтетические данные
data = pd.DataFrame({
    'person_age': np.random.randint(20, 70, n_samples),
    'person_gender': np.random.choice(['male', 'female'], n_samples),
    'person_education': np.random.choice(['High School', 'Bachelor', 'Master'], n_samples),
    'person_income': np.random.randint(20000, 150000, n_samples),
    'person_emp_exp': np.random.randint(0, 30, n_samples),
    'person_home_ownership': np.random.choice(['RENT', 'OWN', 'MORTGAGE'], n_samples),
    'loan_amnt': np.random.randint(50000, 500000, n_samples),
    'loan_intent': np.random.choice(['PERSONAL', 'EDUCATION', 'HOMEIMPROVEMENT'], n_samples),
    'loan_int_rate': np.random.uniform(3, 15, n_samples).round(2),
    'loan_percent_income': np.random.uniform(0.1, 0.5, n_samples).round(2),
    'cb_person_cred_hist_length': np.random.uniform(1, 20, n_samples).round(1),
    'credit_score': np.random.randint(300, 850, n_samples),
    'previous_loan_defaults_on_file': np.random.choice(['Yes', 'No'], n_samples),
})

# Целевая переменная
data['loan_status'] = (
    (data['credit_score'] > 600) & 
    (data['person_income'] > 40000) & 
    (data['loan_int_rate'] < 10)
).astype(int)

print(f"Датасет: {data.shape}")
print(f"Target:\n{data['loan_status'].value_counts()}")

# Разделяем
train, test = train_test_split(data, test_size=0.2, random_state=42)
test.to_csv('test_data.csv', index=False)
print("test_data.csv сохранён")

# Колонки
categorical_cols = [
    'person_gender', 'person_education', 'person_home_ownership',
    'loan_intent', 'previous_loan_defaults_on_file'
]

feature_cols = [
    'person_age', 'person_gender', 'person_education', 'person_income',
    'person_emp_exp', 'person_home_ownership', 'loan_amnt', 'loan_intent',
    'loan_int_rate', 'loan_percent_income', 'cb_person_cred_hist_length',
    'credit_score', 'previous_loan_defaults_on_file'
]

# Обучаем LabelEncoder'ы на train
label_encoders = {}
for col in categorical_cols:
    le = LabelEncoder()
    le.fit(train[col])
    label_encoders[col] = le

# Функция предобработки
def preprocess(df):
    df = df.copy()
    for col in categorical_cols:
        if col in df.columns:
            le = label_encoders[col]
            # Обработка unseen значений
            df[col] = df[col].apply(lambda x: x if x in le.classes_ else le.classes_[0])
            df[col] = le.transform(df[col])
    return df[feature_cols]

# Предобрабатываем train
X_train = preprocess(train)
y_train = train['loan_status']

# Pipeline: scaler + модель
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
])

pipeline.fit(X_train, y_train)

# Оценка
X_test = preprocess(test)
y_test = test['loan_status']
y_proba = pipeline.predict_proba(X_test)[:, 1]
roc_auc = roc_auc_score(y_test, y_proba)
print(f"ROC-AUC: {roc_auc:.4f}")

# Сохраняем ВСЁ для бэкенда
model_data = {
    'pipeline': pipeline,
    'label_encoders': label_encoders,
    'categorical_cols': categorical_cols,
    'feature_cols': feature_cols,
    'metadata': {
        'algorithm': 'RandomForest',
        'roc_auc': roc_auc,
    }
}

joblib.dump(model_data, 'model.pkl')
print("model.pkl сохранён (с энкодерами)")  