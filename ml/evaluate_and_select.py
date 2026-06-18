import pandas as pd
import joblib
import os
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'loan_data.csv')


def select_best_model():
    print("--- Запуск судьи: сравнение моделей ---")

    # 1. Загрузка данных
    df = pd.read_csv(DATA_PATH).dropna()

    # 2. Получаем энкодеры из одной из сохраненных моделей
    # (они одинаковые в обоих скриптах обучения)
    data_example = joblib.load(os.path.join(BASE_DIR, 'model_rf.pkl'))
    encoders = data_example['encoders']

    # 3. Применяем кодирование к тестовым данным
    for col, le in encoders.items():
        df[col] = le.transform(df[col].astype(str))

    X = df.drop('loan_status', axis=1)
    y = df['loan_status']
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model_files = {'Random Forest': 'model_rf.pkl', 'Logistic Regression': 'model_lr.pkl'}

    best_score = -1
    best_model_data = None
    best_name = ""

    for name, filename in model_files.items():
        data = joblib.load(os.path.join(BASE_DIR, filename))
        pipeline = data['pipeline']

        score = roc_auc_score(y_test, pipeline.predict_proba(X_test)[:, 1])
        print(f"Модель {name}: ROC-AUC = {score:.4f}")

        if score > best_score:
            best_score = score
            best_model_data = data
            best_name = name

    joblib.dump(best_model_data, os.path.join(BASE_DIR, 'model.pkl'))
    print(f"\nПобедитель: {best_name} (ROC-AUC: {best_score:.4f})")


if __name__ == "__main__":
    select_best_model()