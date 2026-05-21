from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import Optional
import pandas as pd
from io import StringIO

from app.schemas.requests import (
    PredictRequest,
    PredictResponse,
    UploadModelResponse,
    PredictCsvResponse,
)
from app.services.predictor import model_service

router = APIRouter(prefix="/model", tags=["model"])


@router.post(
    "/upload-model",
    response_model=UploadModelResponse,
    summary="Загрузка модели",
    description="Загружает модель машинного обучения в формате .pkl",
)
async def upload_model(file: UploadFile = File(...)):
    """
    Загружает обученную модель в формате pkl.
    
    Модель должна быть сохранена как sklearn Pipeline или словарь с ключом 'pipeline'.
    """
    # Проверяем расширение файла
    if not file.filename.endswith(".pkl"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have .pkl extension",
        )

    try:
        # Читаем содержимое файла
        model_bytes = await file.read()

        # Пробуем загрузить модель
        model_service.load_model(model_bytes)

        return UploadModelResponse(
            message=f"Model '{file.filename}' successfully loaded",
            status="success",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.post(
    "/predict",
    response_model=PredictResponse,
    summary="Предсказание",
    description="Делает предсказание на основе предоставленных данных",
)
async def predict(request: PredictRequest):
    """
    Получает предсказание для одной или нескольких записей.
    
    Данные должны быть предобработаны (закодированы и отмасштабированы).
    """
    if not model_service.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model not loaded. Please upload model first via /upload-model",
        )

    try:
        # Конвертируем записи в словари
        records = [record.model_dump(exclude_none=True) for record in request.records]

        # Получаем предсказания
        results = model_service.predict(records)

        return PredictResponse(records=results, status="success")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction error: {str(e)}",
        )


@router.post(
    "/predict-from-csv",
    response_model=PredictCsvResponse,
    summary="Предсказание из CSV",
    description="Принимает CSV файл и возвращает предсказания для всех строк",
)
async def predict_from_csv(file: UploadFile = File(...)):
    """
    Принимает CSV файл (с предобработкой или без) и возвращает полный датасет с предсказаниями.
    
    Если в CSV есть колонка loan_status, вычисляется ROC-AUC.
    """
    if not model_service.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model not loaded. Please upload model first via /upload-model",
        )

    # Проверяем расширение файла
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have .csv extension",
        )

    try:
        # Читаем содержимое
        csv_bytes = await file.read()

        # Получаем предсказания
        result_df, roc_auc, rows_count = model_service.predict_from_csv(csv_bytes)

        # Конвертируем результат в CSV строку
        csv_string = result_df.to_csv(index=False)

        return PredictCsvResponse(
            csv_data=csv_string,
            roc_auc=roc_auc,
            status="success",
            rows_processed=rows_count,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CSV processing error: {str(e)}",
        )