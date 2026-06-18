import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

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

# Обучение
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

# Сохранение (Используем ключ 'model')
joblib.dump({'model': model, 'encoders': encoders, 'features': X.columns.tolist()}, 'model_rf.pkl')
print("Random Forest сохранен в model_rf.pkl")