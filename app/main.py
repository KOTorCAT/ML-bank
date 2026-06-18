"""
Точка входа в приложение.
Этот файл запускает сервер и регистрирует все эндпоинты.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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

# Подключаем папку frontend для статических файлов (HTML, CSS, JS)
# Фронтендер кладёт свои файлы в папку frontend/
app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")

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
            "документация_api": "/docs",
            "интерфейс_пользователя": "/app",
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)