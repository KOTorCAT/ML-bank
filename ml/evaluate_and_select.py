import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# 1. Загружаем данные
df = pd.read_csv('loan_data.csv').dropna()
X = df.drop('loan_status', axis=1)
y = df['loan_status']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

models = ['model_rf.pkl', 'model_lr.pkl']
best_score = 0
best_model_path = ""

for path in models:
    # Загружаем модель и её энкодеры
    data = joblib.load(path)
    model = data['model']
    encoders = data['encoders']  # Получаем энкодеры, которые учились на train

    # 2. ПРЕОБРАЗУЕМ ТЕСТОВЫЕ ДАННЫЕ
    X_test_encoded = X_test.copy()
    for col, le in encoders.items():
        # Превращаем слова в числа, как при обучении
        X_test_encoded[col] = le.transform(X_test_encoded[col].astype(str))

    # 3. Предсказание
    preds = model.predict(X_test_encoded)
    score = accuracy_score(y_test, preds)
    print(f"Модель {path}: Accuracy = {score:.4f}")

    if score > best_score:
        best_score = score
        best_model_path = path

# 4. Сохраняем лучшую
final_data = joblib.load(best_model_path)
joblib.dump(final_data, 'final_model.pkl')
print(f"\nЛучшая модель: {best_model_path} с точностью {best_score:.4f}. Сохранена как final_model.pkl")