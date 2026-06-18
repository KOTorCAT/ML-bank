"""
Эндпоинты для работы с моделью.
Все URL начинаются с /model/...
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status
import logging

from app.schemas.requests import PredictRequest
from app.services.predictor import model_service

router = APIRouter(prefix="/model", tags=["model"])
logger = logging.getLogger(__name__)


@router.post("/upload-model")
async def upload_model(file: UploadFile = File(...)):
    if not file.filename.endswith(".pkl"):
        raise HTTPException(400, detail="Файл должен иметь расширение .pkl")

    try:
        model_bytes = await file.read()
        model_service.load_model(model_bytes, filename=file.filename)
        return {"message": f"Модель '{file.filename}' загружена", "status": "success"}
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
    except Exception as e:
        raise HTTPException(500, detail=f"Ошибка сервера: {str(e)}")


@router.post("/predict")
async def predict(request: PredictRequest):
    if not model_service.is_loaded:
        raise HTTPException(400, detail="Модель не загружена. Сначала загрузите модель через /upload-model")

    try:
        records = [record.model_dump(exclude_none=True) for record in request.records]
        logger.info(f"Получены данные: {records}")
        results = model_service.predict(records)
        return {"records": results, "status": "success"}
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
    except Exception as e:
        raise HTTPException(500, detail=f"Ошибка предсказания: {str(e)}")


@router.post("/predict-from-csv")
async def predict_from_csv(file: UploadFile = File(...)):
    if not model_service.is_loaded:
        raise HTTPException(400, detail="Модель не загружена. Сначала загрузите модель через /upload-model")

    if not file.filename.endswith(".csv"):
        raise HTTPException(400, detail="Файл должен иметь расширение .csv")

    try:
        csv_bytes = await file.read()
        result_df, roc_auc, rows_count = model_service.predict_from_csv(csv_bytes, filename=file.filename)
        csv_string = result_df.to_csv(index=False)

        return {
            "csv_data": csv_string,
            "roc_auc": roc_auc,
            "status": "success",
            "rows_processed": rows_count,
        }
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
    except Exception as e:
        raise HTTPException(500, detail=f"Ошибка обработки CSV: {str(e)}")


@router.get("/stats")
async def get_stats():
    try:
        stats = model_service.get_stats()
        return {"status": "success", "data": stats}
    except Exception as e:
        raise HTTPException(500, detail=f"Ошибка получения статистики: {str(e)}")