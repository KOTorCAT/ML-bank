import pandas as pd
import joblib
import os
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'loan_data.csv')


def train_lr():
    df = pd.read_csv(DATA_PATH).dropna()

    # Кодирование (используем те же методы, что и в RF)
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
        ('clf', LogisticRegression(max_iter=1000))
    ])

    pipeline.fit(X, y)

    # Сохранение
    joblib.dump({'pipeline': pipeline, 'encoders': encoders}, os.path.join(BASE_DIR, 'model_lr.pkl'))
    print("Logistic Regression успешно обучена и сохранена как model_lr.pkl")


if __name__ == "__main__":
    train_lr()