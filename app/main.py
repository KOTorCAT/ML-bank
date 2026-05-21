from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


# Современный способ обработки событий жизненного цикла
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения"""
    # Startup
    logger.info("Starting Mortgage Approval Service...")
    yield
    # Shutdown
    logger.info("Shutting down Mortgage Approval Service...")


# Создаем приложение с lifespan
app = FastAPI(
    title="ML Mortgage Approval Service",
    description="Сервис для предсказания одобрения ипотеки",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,  # Передаем lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", summary="Корневой эндпоинт")
async def root():
    """Корневой эндпоинт с информацией о сервисе"""
    return {
        "service": "ML Mortgage Approval Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "upload_model": "/model/upload-model",
            "predict": "/model/predict",
            "predict_from_csv": "/model/predict-from-csv",
        },
    }


@app.get("/health", summary="Проверка здоровья сервиса")
async def health_check():
    """Эндпоинт для проверки работоспособности сервиса"""
    from app.services.predictor import model_service
    return {"status": "healthy", "model_loaded": model_service.is_loaded}


# Подключаем роутеры
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