# Сервис предсказания одобрения ипотеки

Сервер на FastAPI. Принимает данные клиента и предсказывает: одобрят ипотеку или нет.

---

## Как это работает

Сервер запускается и ждёт запросы на порту 8000. Вся логика сводится к трём шагам:
1. Принять данные от клиента (JSON или CSV)
2. Передать их модели
3. Вернуть ответ модели обратно

Модель — это файл формата `.pkl`. Внутри него лежит обученный sklearn Pipeline: сначала данные масштабируются, потом подаются в модель. Плюс там же лежат правила кодирования текстовых категорий в числа.

При старте сервера модель не загружена. Нужно один раз вызвать эндпоинт загрузки, после этого можно делать предсказания. Модель хранится в оперативной памяти до перезапуска сервера.

Все запросы на предсказание сохраняются в базу данных SQLite (файл `app.db`). Это позволяет посмотреть историю: сколько было запросов, сколько одобрений и отказов, какие данные отправляли.

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

Сервис доступен на `http://localhost:8000`.

### Как проверить, что сервер жив

```
GET /health
```

Ответ:
```json
{
  "status": "работает",
  "model_loaded": false
}
```

`model_loaded: true` — модель загружена, можно предсказывать.
`model_loaded: false` — нужно сначала загрузить модель.

---

### Загрузка модели

```
POST /model/upload-model
```

**Что делает:** загружает файл `model.pkl` в память сервера. Без этого шага предсказания не работают.

**Запрос:** файл в multipart/form-data, расширение `.pkl`

**Ответ:**
```json
{
  "message": "Модель 'model.pkl' загружена",
  "status": "success"
}
```

**Ошибки:**
- 400 — файл не `.pkl`, или внутри не модель, или модель сломана
- 500 — непредвиденная ошибка

---

### Предсказание по JSON

```
POST /model/predict
```

**Что делает:** принимает данные одного или нескольких клиентов, возвращает решение по каждому.

**Запрос:** JSON, внутри массив `records`

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

Все 13 признаков обязательны. Категории (gender, education и т.д.) — числами, не текстом. Порядок полей не важен, бэкенд сам выстроит правильный.

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

- `loan_status` — 1 (одобрено) или 0 (отказ)
- `loan_status_label` — текст "одобрено" или "отказ"
- `probability` — вероятность от 0 до 1 (насколько модель уверена)

**Ошибки:**
- 400 — модель не загружена, не хватает признаков, не тот формат
- 500 — ошибка внутри модели

---

### Предсказание из CSV

```
POST /model/predict-from-csv
```

**Что делает:** принимает CSV-файл с данными клиентов, предсказывает для каждой строки и возвращает CSV с результатами.

**Запрос:** файл `.csv` в multipart/form-data

Категориальные признаки могут быть текстом ("male"/"female") — бэкенд сам закодирует их в числа, используя энкодеры из модели. Если в CSV есть колонка `loan_status` — бэкенд вычислит ROC-AUC (сравнит предсказания с реальными ответами).

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
- `roc_auc` — качество модели (только если в CSV была колонка `loan_status`); 1.0 — идеально, 0.5 — угадывает как монетка
- `csv_data` — CSV-строка с двумя новыми колонками: `predicted_loan_status` и `probability`

**Ошибки:**
- 400 — модель не загружена, файл не CSV, нет нужных колонок
- 500 — ошибка при обработке

---

### Статистика

```
GET /model/stats
```

**Что делает:** возвращает историю использования сервиса из базы данных.

**Ответ:**
```json
{
  "status": "success",
  "data": {
    "models_uploaded": 2,
    "predictions_made": 402,
    "approved": 68,
    "rejected": 334,
    "recent_predictions": [...]
  }
}
```

- `models_uploaded` — сколько раз загружали модель
- `predictions_made` — сколько всего предсказаний
- `approved` / `rejected` — сколько одобрено и сколько отказов
- `recent_predictions` — последние 10 запросов с полными данными

---

### Тестовая страница

```
GET /test
```

Открывается в браузере. Можно вручную загрузить модель, отправить JSON или CSV, посмотреть результат и статистику.

---

### Список всех эндпоинтов

```
GET /
```

---

## Структура проекта

```
ML-bank/
├── app/
│   ├── main.py              # Запуск сервера, эндпоинты /, /health, /test
│   ├── routers/
│   │   └── model.py         # /model/upload-model, /model/predict, /model/predict-from-csv, /model/stats
│   ├── services/
│   │   └── predictor.py     # Вся логика: загрузка модели, предобработка, вызов model.predict(), работа с БД
│   └── schemas/
│       └── requests.py      # Описание формата входных данных
├── ml/
│   ├── create_test_model.py # Скрипт для создания тестовой модели
│   ├── model.pkl            # Файл с обученной моделью
│   └── test_data.csv        # Тестовые данные
├── app.db                   # База данных SQLite (создаётся автоматически)
├── requirements.txt
└── README.md
```

---

## Для ML-инженера

### Как сохранять модель

Модель должна сохраняться словарём с ключами:

```python
import joblib

model_data = {
    'pipeline': pipeline,               # sklearn Pipeline (scaler + модель)
    'label_encoders': label_encoders,   # словарь LabelEncoder для каждой категориальной колонки
    'categorical_cols': ['col1', ...],  # список категориальных колонок
    'feature_cols': ['col1', ...],      # все 13 признаков в правильном порядке
    'metadata': {'algorithm': 'RandomForest', 'roc_auc': 0.85}
}

joblib.dump(model_data, 'model.pkl')
```

Без `label_encoders` и `categorical_cols` бэкенд не сможет обработать сырой CSV с текстовыми категориями.

### Как протестировать модель через бэкенд

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

1. Проверить, что сервер жив: `GET /health`
2. Если `model_loaded: false` — сообщить пользователю, что модель не загружена
3. Отправить данные клиента на `POST /model/predict`
4. Показать результат: `loan_status_label` и `probability`

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
// data.records[0].loan_status_label → "одобрено" или "отказ"
// data.records[0].probability       → 0.87
```

### Важно

Категориальные признаки (gender, education, home_ownership, loan_intent, defaults) передаются **числами**, не текстом. Таблицу кодировки (какой цифре соответствует какая категория) нужно запросить у ML-инженера.

---

