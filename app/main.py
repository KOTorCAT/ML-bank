"""
Точка входа в приложение.
Этот файл запускает сервер и регистрирует все эндпоинты.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Подключаем роутер с эндпоинтами из соседнего файла
from app.routers import model

# Создаём приложение FastAPI
app = FastAPI(
    title="Сервис одобрения ипотеки",
    description="Предсказывает, одобрят ипотеку или нет, на основе данных клиента",
    version="1.0.0",
)

# Разрешаем запросы с любого адреса (нужно, чтобы фронтенд мог обращаться к API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем эндпоинты из router/model.py
app.include_router(model.router)


# --- Простые эндпоинты ---

@app.get("/")
async def root():
    """Главная страница — показывает список всех доступных эндпоинтов"""
    return {
        "service": "Сервис одобрения ипотеки",
        "version": "1.0.0",
        "status": "работает",
        "endpoints": {
            "документация": "/docs",
            "тестовая_страница": "/test",
            "загрузить_модель": "/model/upload-model",
            "предсказание_json": "/model/predict",
            "предсказание_csv": "/model/predict-from-csv",
            "статистика": "/model/stats",
        },
    }


@app.get("/health")
async def health_check():
    """
    Проверка состояния сервера.
    Возвращает, загружена ли модель.
    Фронтенд может спросить этот эндпоинт перед тем, как отправлять данные.
    """
    from app.services.predictor import model_service
    return {
        "status": "работает",
        "model_loaded": model_service.is_loaded
    }


@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """
    Тестовая страница для ручной проверки.
    Открывается в браузере, можно загрузить модель, ввести JSON или CSV.
    """
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Тест сервиса</title>
    <style>
        body { font-family: Arial; max-width: 750px; margin: 30px auto; padding: 0 20px; }
        h1 { font-size: 20px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 6px; }
        .section h3 { margin-top: 0; }
        textarea { width: 100%; font-family: monospace; font-size: 12px; box-sizing: border-box; }
        button { padding: 6px 18px; margin: 6px 0; cursor: pointer; }
        pre { background: #f5f5f5; padding: 10px; border-radius: 4px; font-size: 12px; max-height: 300px; overflow-x: auto; }
        #status { font-weight: bold; }
    </style>
</head>
<body>
    <h1>Тест сервиса одобрения ипотеки</h1>
    <p>Статус: <span id="status">проверка...</span></p>

    <div class="section">
        <h3>1. Загрузить модель (.pkl)</h3>
        <input type="file" id="modelFile" accept=".pkl">
        <button onclick="uploadModel()">Загрузить</button>
        <pre id="uploadResult"></pre>
    </div>

    <div class="section">
        <h3>2. Предсказание по JSON</h3>
        <textarea id="inputData" rows="14">{
  "records": [{
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
  }]
}</textarea>
        <button onclick="predict()">Предсказать</button>
        <pre id="predictResult"></pre>
    </div>

    <div class="section">
        <h3>3. Предсказание из CSV</h3>
        <input type="file" id="csvFile" accept=".csv">
        <button onclick="predictCsv()">Обработать</button>
        <pre id="csvResult"></pre>
    </div>

    <div class="section">
        <h3>4. Статистика</h3>
        <button onclick="getStats()">Обновить</button>
        <pre id="statsResult"></pre>
    </div>

    <script>
        async function checkStatus() {
            try {
                const res = await fetch('/health');
                const data = await res.json();
                const s = document.getElementById('status');
                if (data.model_loaded) {
                    s.textContent = 'Модель загружена';
                    s.style.color = 'green';
                } else {
                    s.textContent = 'Модель не загружена';
                    s.style.color = 'orange';
                }
            } catch(e) {
                document.getElementById('status').textContent = 'Сервер недоступен';
            }
        }

        async function uploadModel() {
            const file = document.getElementById('modelFile').files[0];
            if (!file) return alert('Выберите файл');
            const formData = new FormData();
            formData.append('file', file);
            const res = await fetch('/model/upload-model', { method: 'POST', body: formData });
            const data = await res.json();
            document.getElementById('uploadResult').textContent = JSON.stringify(data, null, 2);
            checkStatus();
        }

        async function predict() {
            const input = document.getElementById('inputData').value;
            const res = await fetch('/model/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: input
            });
            const data = await res.json();
            document.getElementById('predictResult').textContent = JSON.stringify(data, null, 2);
        }

        async function predictCsv() {
            const file = document.getElementById('csvFile').files[0];
            if (!file) return alert('Выберите CSV');
            const formData = new FormData();
            formData.append('file', file);
            const res = await fetch('/model/predict-from-csv', { method: 'POST', body: formData });
            const data = await res.json();
            const display = { ...data };
            if (display.csv_data) {
                display.csv_preview = display.csv_data.substring(0, 300) + '...';
                delete display.csv_data;
            }
            document.getElementById('csvResult').textContent = JSON.stringify(display, null, 2);
        }

        async function getStats() {
            const res = await fetch('/model/stats');
            const data = await res.json();
            document.getElementById('statsResult').textContent = JSON.stringify(data, null, 2);
        }

        checkStatus();
    </script>
</body>
</html>
"""


# Запуск сервера
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)