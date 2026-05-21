# Сервис предсказания одобрения ипотеки

Веб-сервис на FastAPI. Принимает данные клиента и предсказывает: одобрят ипотеку или нет.

---

## Первый запуск

```bash
# 1. Создать виртуальное окружение
python3 -m venv venv

# 2. Активировать
source venv/bin/activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Запустить
python -m app.main
```

Открыть в браузере: `http://localhost:8000/test`

---

## API

Сервис поднимается на `http://localhost:8000`. Есть три рабочих эндпоинта.

### POST /model/upload-model

Загружает модель. Нужно вызвать первым делом.

**Запрос:** файл `model.pkl` (multipart/form-data)

**Ответ:**
```json
{"message": "Model 'model.pkl' successfully loaded", "status": "success"}
```

**Ошибка:** 400 если файл не .pkl или внутри не модель

---

### POST /model/predict

Предсказание по данным клиента.

**Запрос:** JSON с массивом records

```json
{
  "records": [
    {
      "person_age": 25,
      "person_gender": 0,
      "person_education": 2,
      "person_income": 50000,
      "person_emp_exp": 5,
      "person_home_ownership": 1,
      "loan_amnt": 150000,
      "loan_intent": 0,
      "loan_int_rate": 6.5,
      "loan_percent_income": 0.3,
      "cb_person_cred_hist_length": 5,
      "credit_score": 720,
      "previous_loan_defaults_on_file": 1
    }
  ]
}
```

**Ответ:**
```json
{
  "records": [
    {
      "person_age": 25,
      "person_income": 50000,
      "loan_status": 1,
      "loan_status_label": "одобрено",
      "probability": 0.87
    }
  ],
  "status": "success"
}
```

Поля в ответе:
- `loan_status` — 1 (одобрено) или 0 (отказ)
- `loan_status_label` — текст "одобрено" или "отказ"
- `probability` — вероятность от 0 до 1

**Ошибки:**
- 400 — модель не загружена, или не те признаки
- 500 — ошибка предсказания

---

### POST /model/predict-from-csv

Пакетная обработка. Загружаешь CSV — получаешь CSV с предсказаниями.

**Запрос:** файл .csv (multipart/form-data)

**Ответ:**
```json
{
  "status": "success",
  "rows_processed": 200,
  "roc_auc": 0.9853,
  "csv_data": "person_age,...,predicted_loan_status,probability\n..."
}
```

- `rows_processed` — сколько строк обработано
- `roc_auc` — точность модели (появляется только если в CSV была колонка `loan_status`)
- `csv_data` — CSV строка с двумя новыми колонками: `predicted_loan_status` и `probability`

**Ошибки:**
- 400 — модель не загружена, файл не CSV, или нет нужных колонок

---

## Дополнительные эндпоинты

### GET /

Информация о сервисе и список всех эндпоинтов.

### GET /health

Проверка, жив ли сервер и загружена ли модель.
```json
{"status": "healthy", "model_loaded": true}
```

### GET /test

Тестовая страница. Можно вручную загрузить модель, отправить JSON или CSV и посмотреть результат.

---

## Структура проекта

```
ML-bank/
├── app/
│   ├── main.py              # Запуск, эндпоинты /, /health, /test
│   ├── routers/
│   │   └── model.py         # /model/upload-model, /model/predict, /model/predict-from-csv
│   ├── services/
│   │   └── predictor.py     # Загрузка модели, предсказания, предобработка
│   └── schemas/
│       └── requests.py      # Схемы для валидации данных
├── ml/
│   ├── create_test_model.py # Скрипт для создания тестовой модели
│   ├── model.pkl            # Файл с обученной моделью
│   └── test_data.csv        # Тестовые данные
├── requirements.txt
└── README.md
```

---

## Для ML-инженера

### Как сохранять модель

Модель должна сохраняться словарём, а не просто пайплайном. Бэкенду нужны энкодеры и список признаков:

```python
import joblib

model_data = {
    'pipeline': pipeline,               # sklearn Pipeline (scaler + модель)
    'label_encoders': label_encoders,   # словарь LabelEncoder для каждой категориальной колонки
    'categorical_cols': ['col1', ...],  # список категориальных колонок
    'feature_cols': ['col1', ...],      # все 13 признаков в правильном порядке
    'metadata': {'roc_auc': 0.85}       # что угодно для информации
}

joblib.dump(model_data, 'model.pkl')
```

Без этого бэкенд не сможет обработать сырой CSV.

### Как протестировать модель

```bash
cd ml
python create_test_model.py    # создаст model.pkl и test_data.csv
cd ..
python -m app.main             # запустит сервер
```

Открыть `http://localhost:8000/test`, загрузить `model.pkl`, проверить предсказания.

---

## Для фронтендера

### Порядок работы

1. Проверить, что модель загружена — `GET /health`
2. Отправить данные клиента на `POST /model/predict`
3. Показать результат

### Запрос из JavaScript

```javascript
const res = await fetch('http://localhost:8000/model/predict', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    records: [{
      person_age: 25,
      person_gender: 0,
      person_education: 2,
      person_income: 50000,
      person_emp_exp: 5,
      person_home_ownership: 1,
      loan_amnt: 150000,
      loan_intent: 0,
      loan_int_rate: 6.5,
      loan_percent_income: 0.3,
      cb_person_cred_hist_length: 5,
      credit_score: 720,
      previous_loan_defaults_on_file: 1
    }]
  })
});

const data = await res.json();
// data.records[0].loan_status       → 0 или 1
// data.records[0].loan_status_label → "одобрено" / "отказ"
// data.records[0].probability       → 0.87
```

### Важно

Категориальные признаки (gender, education, home_ownership, loan_intent, defaults) передаются **числами**, не текстом. Какой цифре что соответствует — спросить у ML-инженера.

