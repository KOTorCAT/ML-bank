# Сервис предсказания одобрения ипотеки

Веб-сервис на FastAPI. Принимает данные клиента и предсказывает: одобрят ипотеку или нет.

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


#Windows (CMD)

# 1. Создать виртуальное окружение
python -m venv venv

# 2. Активировать
venv\Scripts\activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Запустить
python -m app.main
```

Открыть в браузере: `http://localhost:8000`

---

## Все страницы и эндпоинты

| Адрес | Кому | Что там |
|-------|------|---------|
| `/` | Всем | Список всех эндпоинтов |
| `/health` | Фронтендеру | Проверка: жив ли сервер, загружена ли модель |
| `/docs` | Разработчикам | Интерактивная документация API (Swagger) |
| `/test` | Разработчикам | Страница для ручного тестирования |
| `/app` | Пользователям | Интерфейс для клиентов (фронтендер делает здесь) |
| `/model/upload-model` | Администратору | Загрузка обученной модели |
| `/model/predict` | Фронтендеру | Предсказание по JSON (один клиент) |
| `/model/predict-from-csv` | Аналитику | Предсказание из CSV (много клиентов) |
| `/model/stats` | Всем | Статистика использования |

---

## API

### Проверка состояния

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
- 400 — файл не `.pkl`, или внутри не модель
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

Все 13 признаков обязательны. Категории (gender, education и т.д.) — числами, не текстом. Порядок полей не важен.

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
- `probability` — вероятность от 0 до 1

**Ошибки:**
- 400 — модель не загружена, не хватает признаков
- 500 — ошибка внутри модели

---

### Предсказание из CSV

```
POST /model/predict-from-csv
```

**Что делает:** принимает CSV-файл, предсказывает для каждой строки и возвращает CSV с результатами.

**Запрос:** файл `.csv`

Категориальные признаки можно текстом ("male"/"female") — бэкенд сам закодирует. Если в CSV есть колонка `loan_status` — бэкенд вычислит ROC-AUC (сравнит предсказания с реальными ответами).

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
- `roc_auc` — качество модели (только если был `loan_status`); 1.0 — идеально, 0.5 — угадывает как монетка
- `csv_data` — CSV-строка с новыми колонками: `predicted_loan_status` и `probability`

---

### Статистика

```
GET /model/stats
```

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
- `recent_predictions` — последние 10 запросов

---

## Структура проекта

```
ML-bank/
├── app/                    # Бэкенд
│   ├── main.py             # Запуск сервера, эндпоинты /, /health, /test
│   ├── routers/
│   │   └── model.py        # Эндпоинты /model/*
│   ├── services/
│   │   └── predictor.py    # Логика: модель, предобработка, база данных
│   └── schemas/
│       └── requests.py     # Формат входных данных
├── frontend/               # Фронтенд (здесь работает фронтендер)
│   └── index.html          # Заглушка, заменить на интерфейс
├── ml/                     # ML (здесь работает ML-инженер)
│   ├── create_test_model.py
│   ├── model.pkl
│   └── test_data.csv
├── app.db                  # База SQLite (создаётся автоматически)
├── requirements.txt
└── README.md
```

---

## Для ML-инженера

### Что нужно сделать

1. Взять датасет
2. Очистить данные (пропуски, выбросы)
3. Закодировать категориальные признаки
4. Отмасштабировать числа
5. Отобрать признаки
6. Обучить минимум 2 модели (например, LogisticRegression и RandomForest)
7. Сравнить по ROC-AUC, выбрать лучшую
8. Сохранить модель в правильном формате

### Как сохранять модель

Модель сохраняется словарём с ключами:

```python
import joblib

model_data = {
    'pipeline': pipeline,               # sklearn Pipeline (scaler + модель)
    'label_encoders': label_encoders,   # словарь LabelEncoder для категорий
    'categorical_cols': ['col1', ...],  # список категориальных колонок
    'feature_cols': ['col1', ...],      # все 13 признаков в правильном порядке
    'metadata': {'algorithm': 'RandomForest', 'roc_auc': 0.85}
}

joblib.dump(model_data, 'model.pkl')
```

Без `label_encoders` и `categorical_cols` бэкенд не сможет обработать CSV с текстовыми категориями.

### Как протестировать

```bash
cd ml
python create_test_model.py    # тестовая модель и CSV
cd ..
python -m app.main             # запуск сервера
```

Открыть `http://localhost:8000/test`, загрузить `model.pkl`, проверить.

---

## Для фронтендера

### Что нужно сделать

1. Открыть папку `frontend/`
2. Заменить `index.html` на свой интерфейс
3. Добавить CSS и JS в эту же папку

### Как отправлять запрос

Перед отправкой данных проверить, загружена ли модель:

```javascript
const health = await fetch('/health');
const healthData = await health.json();
// healthData.model_loaded === true — можно предсказывать
```

Отправить данные:

```javascript
const res = await fetch('/model/predict', {
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

Категориальные признаки (gender, education, home_ownership, loan_intent, defaults) передаются **числами**, не текстом. Таблицу кодировки (какая цифра что значит) запросить у ML-инженера.

### Где смотреть интерфейс

```
http://localhost:8000/app
```

Сервер сам отдаст файлы из папки `frontend/`. Можно использовать любые CSS и JS файлы — сервер их обслуживает как статику.

---

