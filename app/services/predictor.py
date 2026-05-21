import joblib
import pandas as pd
import numpy as np
from io import BytesIO, StringIO
from typing import Optional, List, Dict, Any, Tuple
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
import logging

logger = logging.getLogger(__name__)


class ModelService:
    """Сервис для работы с ML-моделью"""

    def __init__(self):
        self.pipeline: Optional[Pipeline] = None
        self.is_loaded: bool = False
        self.model_metadata: Dict[str, Any] = {}

    def load_model(self, model_data: bytes) -> None:
        """
        Загружает модель из байтов
        
        Args:
            model_data: Сериализованная модель в формате bytes
        
        Raises:
            ValueError: Если модель невалидна
        """
        try:
            # Загружаем из байтов
            loaded_object = joblib.load(BytesIO(model_data))

            # Проверяем, что загружен pipeline
            if isinstance(loaded_object, dict) and "pipeline" in loaded_object:
                self.pipeline = loaded_object["pipeline"]
                self.model_metadata = loaded_object.get("metadata", {})
            elif isinstance(loaded_object, Pipeline):
                self.pipeline = loaded_object
                self.model_metadata = {}
            else:
                raise ValueError(
                    "Invalid model format. Expected sklearn Pipeline or dict with 'pipeline' key"
                )

            self.is_loaded = True
            logger.info("Model successfully loaded")

        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self.is_loaded = False
            self.pipeline = None
            raise ValueError(f"Failed to load model: {str(e)}")

    def predict(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Делает предсказание для списка записей
        
        Args:
            records: Список словарей с признаками
            
        Returns:
            Список словарей с добавленным полем loan_status
        """
        if not self.is_loaded or self.pipeline is None:
            raise ValueError("Model not loaded. Please upload model first.")

        try:
            # Конвертируем в DataFrame
            df = pd.DataFrame(records)

            # Делаем предсказание
            predictions = self.pipeline.predict(df)
            probabilities = None

            # Пробуем получить вероятности
            try:
                probabilities = self.pipeline.predict_proba(df)
                prob_values = probabilities[:, 1].tolist()
            except Exception:
                prob_values = [None] * len(predictions)

            # Формируем результат
            results = []
            for i, record in enumerate(records):
                result_record = record.copy()
                result_record["loan_status"] = int(predictions[i])
                result_record["loan_status_label"] = (
                    "одобрено" if predictions[i] == 1 else "отказ"
                )
                if prob_values[i] is not None:
                    result_record["probability"] = round(float(prob_values[i]), 4)
                results.append(result_record)

            logger.info(f"Predictions made for {len(records)} records")
            return results

        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            raise ValueError(f"Prediction failed: {str(e)}")

    def predict_from_csv(
        self, csv_data: bytes
    ) -> Tuple[pd.DataFrame, Optional[float], int]:
        """
        Делает предсказание из CSV файла
        
        Args:
            csv_data: CSV файл в байтах
            
        Returns:
            DataFrame с предсказаниями, ROC-AUC (если был target), количество строк
        """
        if not self.is_loaded or self.pipeline is None:
            raise ValueError("Model not loaded. Please upload model first.")

        try:
            # Читаем CSV
            df = pd.read_csv(BytesIO(csv_data))
            original_df = df.copy()
            rows_count = len(df)

            # Проверяем наличие target
            has_target = "loan_status" in df.columns

            # Отделяем target если есть
            if has_target:
                y_true = df["loan_status"].copy()
                df_processed = df.drop(columns=["loan_status"])
            else:
                y_true = None
                df_processed = df

            # Предсказание
            predictions = self.pipeline.predict(df_processed)
            
            # Пробуем получить вероятности
            try:
                probabilities = self.pipeline.predict_proba(df_processed)[:, 1]
            except Exception:
                probabilities = None

            # Добавляем предсказания
            original_df["predicted_loan_status"] = predictions
            if probabilities is not None:
                original_df["probability"] = probabilities.round(4)

            # Вычисляем ROC-AUC если есть target
            roc_auc = None
            if has_target and y_true is not None:
                try:
                    roc_auc = float(roc_auc_score(y_true, predictions))
                    logger.info(f"ROC-AUC: {roc_auc:.4f}")
                except Exception as e:
                    logger.warning(f"Could not calculate ROC-AUC: {str(e)}")

            logger.info(f"CSV predictions made for {rows_count} records")
            return original_df, roc_auc, rows_count

        except Exception as e:
            logger.error(f"CSV prediction error: {str(e)}")
            raise ValueError(f"CSV prediction failed: {str(e)}")


# Синглтон сервиса
model_service = ModelService()