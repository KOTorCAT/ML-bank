from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import logging
import sys

from app.routers import model

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Mortgage Approval Service...")
    yield
    logger.info("Shutting down Mortgage Approval Service...")


app = FastAPI(
    title="ML Mortgage Approval Service",
    description="Сервис для предсказания одобрения ипотеки",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "service": "ML Mortgage Approval Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "test_page": "/test",
            "upload_model": "/model/upload-model",
            "predict": "/model/predict",
            "predict_from_csv": "/model/predict-from-csv",
        },
    }


@app.get("/health")
async def health_check():
    from app.services.predictor import model_service
    return {"status": "healthy", "model_loaded": model_service.is_loaded}


@app.get("/test", response_class=HTMLResponse)
async def test_page():
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Тест сервиса одобрения ипотеки</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 750px; margin: 30px auto; padding: 0 20px; color: #333; }
        h1 { font-size: 20px; border-bottom: 1px solid #ddd; padding-bottom: 10px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 6px; }
        .section h3 { margin-top: 0; font-size: 15px; }
        textarea { width: 100%; font-family: monospace; font-size: 12px; box-sizing: border-box; }
        button { padding: 6px 18px; margin: 6px 0; cursor: pointer; font-size: 13px; }
        pre { background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 12px; max-height: 300px; }
        input[type="file"] { font-size: 13px; }
        #status { font-weight: bold; }
    </style>
</head>
<body>
    <h1>Сервис одобрения ипотеки — тестовая страница</h1>
    <p>Статус: <span id="status">проверка...</span></p>

    <div class="section">
        <h3>1. Загрузка модели (.pkl)</h3>
        <input type="file" id="modelFile" accept=".pkl">
        <button onclick="uploadModel()">Загрузить</button>
        <pre id="uploadResult"></pre>
    </div>

    <div class="section">
        <h3>2. Предсказание (JSON)</h3>
        <textarea id="inputData" rows="14">{
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
            try {
                const res = await fetch('/model/upload-model', { method: 'POST', body: formData });
                const data = await res.json();
                document.getElementById('uploadResult').textContent = JSON.stringify(data, null, 2);
                checkStatus();
            } catch(e) {
                document.getElementById('uploadResult').textContent = 'Ошибка: ' + e.message;
            }
        }

        async function predict() {
            const input = document.getElementById('inputData').value;
            try {
                const res = await fetch('/model/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: input
                });
                const data = await res.json();
                document.getElementById('predictResult').textContent = JSON.stringify(data, null, 2);
            } catch(e) {
                document.getElementById('predictResult').textContent = 'Ошибка: ' + e.message;
            }
        }

        async function predictCsv() {
            const file = document.getElementById('csvFile').files[0];
            if (!file) return alert('Выберите CSV файл');
            const formData = new FormData();
            formData.append('file', file);
            try {
                const res = await fetch('/model/predict-from-csv', { method: 'POST', body: formData });
                const data = await res.json();
                const display = { ...data };
                if (display.csv_data) {
                    display.csv_preview = display.csv_data.substring(0, 300) + '...';
                    delete display.csv_data;
                }
                document.getElementById('csvResult').textContent = JSON.stringify(display, null, 2);
            } catch(e) {
                document.getElementById('csvResult').textContent = 'Ошибка: ' + e.message;
            }
        }

        checkStatus();
    </script>
</body>
</html>
"""


app.include_router(model.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )