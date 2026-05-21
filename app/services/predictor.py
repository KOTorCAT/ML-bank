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
        self.label_encoders: Dict[str, Any] = {}
        self.categorical_cols: List[str] = []
        self.feature_cols: List[str] = []

    def load_model(self, model_data: bytes) -> None:
        try:
            loaded_object = joblib.load(BytesIO(model_data))

            if isinstance(loaded_object, dict) and "pipeline" in loaded_object:
                self.pipeline = loaded_object["pipeline"]
                self.model_metadata = loaded_object.get("metadata", {})
                self.label_encoders = loaded_object.get("label_encoders", {})
                self.categorical_cols = loaded_object.get("categorical_cols", [])
                self.feature_cols = loaded_object.get("feature_cols", [])
            elif isinstance(loaded_object, Pipeline):
                self.pipeline = loaded_object
                self.model_metadata = {}
            else:
                raise ValueError("Invalid model format")

            self.is_loaded = True
            logger.info("Model loaded successfully")

        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self.is_loaded = False
            raise ValueError(f"Failed to load model: {str(e)}")

    def _preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """Предобработка сырых данных"""
        df = df.copy()
        for col in self.categorical_cols:
            if col in df.columns and col in self.label_encoders:
                le = self.label_encoders[col]
                df[col] = df[col].apply(
                    lambda x: x if x in le.classes_ else le.classes_[0]
                )
                df[col] = le.transform(df[col])
        
        # Оставляем только нужные признаки в правильном порядке
        if self.feature_cols:
            return df[self.feature_cols]
        return df

    def predict(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self.is_loaded or self.pipeline is None:
            raise ValueError("Model not loaded. Please upload model first.")

        try:
            df = pd.DataFrame(records)

            # Если есть энкодеры, значит данные сырые — предобрабатываем
            if self.label_encoders:
                df = self._preprocess(df)
            elif self.feature_cols:
                df = df[self.feature_cols]

            predictions = self.pipeline.predict(df)
            
            try:
                prob_values = self.pipeline.predict_proba(df)[:, 1].tolist()
            except Exception:
                prob_values = [None] * len(predictions)

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
        if not self.is_loaded or self.pipeline is None:
            raise ValueError("Model not loaded. Please upload model first.")

        try:
            df = pd.read_csv(BytesIO(csv_data))
            original_df = df.copy()
            rows_count = len(df)

            has_target = "loan_status" in df.columns
            if has_target:
                y_true = df["loan_status"].copy()
                df = df.drop(columns=["loan_status"])
            else:
                y_true = None

            # Предобработка
            df_processed = self._preprocess(df)

            predictions = self.pipeline.predict(df_processed)
            
            try:
                probabilities = self.pipeline.predict_proba(df_processed)[:, 1]
            except Exception:
                probabilities = None

            original_df["predicted_loan_status"] = predictions
            if probabilities is not None:
                original_df["probability"] = probabilities.round(4)

            roc_auc = None
            if has_target and y_true is not None:
                try:
                    roc_auc = float(roc_auc_score(y_true, predictions))
                except Exception as e:
                    logger.warning(f"ROC-AUC error: {str(e)}")

            logger.info(f"CSV predictions made for {rows_count} records")
            return original_df, roc_auc, rows_count

        except Exception as e:
            logger.error(f"CSV prediction error: {str(e)}")
            raise ValueError(f"CSV prediction failed: {str(e)}")


model_service = ModelService()