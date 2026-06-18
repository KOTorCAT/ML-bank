import pandas as pd
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'loan_data.csv')


def train_rf():
    df = pd.read_csv(DATA_PATH).dropna()

    # Кодирование категориальных признаков
    cat_cols = ['person_gender', 'person_education', 'person_home_ownership',
                'loan_intent', 'previous_loan_defaults_on_file']
    encoders = {col: LabelEncoder().fit(df[col].astype(str)) for col in cat_cols}
    for col, le in encoders.items():
        df[col] = le.transform(df[col].astype(str))

    X = df.drop('loan_status', axis=1)
    y = df['loan_status']

    # Pipeline: масштабирование + модель
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', RandomForestClassifier(n_estimators=100, random_state=42))
    ])

    pipeline.fit(X, y)

    # Сохранение
    joblib.dump({'pipeline': pipeline, 'encoders': encoders}, os.path.join(BASE_DIR, 'model_rf.pkl'))
    print("Random Forest успешно обучен и сохранен как model_rf.pkl")


if __name__ == "__main__":
    train_rf()