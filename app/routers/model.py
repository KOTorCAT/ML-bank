"""
Эндпоинты для работы с моделью.
"""

from fastapi import APIRouter, UploadFile, File
from app.services.predictor import model_service
from io import BytesIO
import pandas as pd

router = APIRouter(prefix="/model", tags=["model"])


@router.post("/upload-model")
async def upload_model(file: UploadFile = File(...)):
    if not file.filename.endswith(".pkl"):
        return {"error": "Файл должен иметь расширение .pkl"}

    contents = await file.read()
    model_service.load_model(contents)
    return {"message": "Модель успешно загружена", "filename": file.filename}


@router.post("/predict")
async def predict(data: dict):
    records = data.get("records", [])
    if not records:
        return {"error": "Поле 'records' пустое"}

    results = model_service.predict(records)
    return {"records": results, "count": len(results)}


@router.post("/predict-from-csv")
async def predict_from_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        return {"error": "Файл должен иметь расширение .csv"}

    contents = await file.read()
    result_df, roc_auc, rows_count = model_service.predict_from_csv(contents)

    return {
        "message": "Предсказание выполнено",
        "rows_processed": rows_count,
        "roc_auc": roc_auc,
        "csv_data": result_df.to_csv(index=False),
    }