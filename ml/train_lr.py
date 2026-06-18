import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline

# Загрузка
df = pd.read_csv('loan_data.csv').dropna()

# Кодирование
cat_cols = ['person_gender', 'person_education', 'person_home_ownership',
            'loan_intent', 'previous_loan_defaults_on_file']
encoders = {col: LabelEncoder().fit(df[col].astype(str)) for col in cat_cols}

for col, le in encoders.items():
    df[col] = le.transform(df[col].astype(str))

# Разделение
X = df.drop('loan_status', axis=1)
y = df['loan_status']

# Обучение (Pipeline объединяет масштабирование и саму модель)
model = Pipeline([
    ('scaler', StandardScaler()),
    ('clf', LogisticRegression(max_iter=1000))
])
model.fit(X, y)

# Сохранение (Ключ 'model' такой же, как в RF, чтобы скрипт выбора работал)
joblib.dump({'model': model, 'encoders': encoders, 'features': X.columns.tolist()}, 'model_lr.pkl')
print("Logistic Regression сохранена в model_lr.pkl")