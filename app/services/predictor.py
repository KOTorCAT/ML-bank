import joblib
import pandas as pd
import numpy as np
import sqlite3
import json
import os
import logging
from io import BytesIO
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score

logger = logging.getLogger(__name__)

DB_PATH = "app.db"


class ModelService:

    def __init__(self):
        self.pipeline = None
        self.is_loaded = False
        self.label_encoders = {}
        self.categorical_cols = []
        self.feature_cols = []
        self.current_model_id = None
        self._create_tables()

    def _connect_db(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        conn = self._connect_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                algorithm TEXT,
                roc_auc REAL,
                features TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER,
                input_data TEXT,
                prediction INTEGER,
                probability REAL,
                label TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (model_id) REFERENCES models(id)
            )
        """)
        conn.commit()
        conn.close()

    def load_model(self, model_bytes: bytes, filename: str = "model.pkl"):
        data = joblib.load(BytesIO(model_bytes))

        if isinstance(data, dict) and "pipeline" in data:
            self.pipeline = data["pipeline"]
            self.label_encoders = data.get("label_encoders", data.get("encoders", {}))
            self.categorical_cols = data.get("categorical_cols", [])
            self.feature_cols = data.get("feature_cols", [])
        elif isinstance(data, Pipeline):
            self.pipeline = data
        else:
            raise ValueError("Неизвестный формат модели")

        # Если feature_cols не указаны — берём из самого пайплайна
        if not self.feature_cols and hasattr(self.pipeline, 'feature_names_in_'):
            self.feature_cols = list(self.pipeline.feature_names_in_)

        self.is_loaded = True

        conn = self._connect_db()
        cursor = conn.execute(
            "INSERT INTO models (filename, algorithm, roc_auc, features) VALUES (?, ?, ?, ?)",
            (
                filename,
                data.get("metadata", {}).get("algorithm", "неизвестно") if isinstance(data, dict) else "неизвестно",
                data.get("metadata", {}).get("roc_auc") if isinstance(data, dict) else None,
                json.dumps(self.feature_cols),
            ),
        )
        self.current_model_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Модель '{filename}' загружена (id={self.current_model_id})")
        logger.info(f"Признаки: {self.feature_cols}")

    def _preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        for col in self.categorical_cols:
            if col in df.columns and col in self.label_encoders:
                encoder = self.label_encoders[col]
                df[col] = df[col].apply(lambda x: x if x in encoder.classes_ else encoder.classes_[0])
                df[col] = encoder.transform(df[col])

        if self.feature_cols:
            return df[self.feature_cols]
        return df

    def predict(self, records: list[dict]) -> list[dict]:
        if not self.is_loaded:
            raise ValueError("Модель не загружена")

        df = pd.DataFrame(records)
        logger.info(f"DataFrame колонки: {list(df.columns)}")
        logger.info(f"DataFrame dtypes: {df.dtypes.to_dict()}")

        if self.label_encoders:
            df = self._preprocess(df)
        elif self.feature_cols:
            # Выстраиваем колонки в правильном порядке
            df = df[self.feature_cols]

        predictions = self.pipeline.predict(df)

        try:
            probabilities = self.pipeline.predict_proba(df)[:, 1]
        except Exception:
            probabilities = [None] * len(predictions)

        results = []
        conn = self._connect_db()

        for i, record in enumerate(records):
            result = record.copy()
            result["loan_status"] = int(predictions[i])
            result["loan_status_label"] = "одобрено" if predictions[i] == 1 else "отказ"
            if probabilities[i] is not None:
                result["probability"] = round(float(probabilities[i]), 4)
            results.append(result)

            conn.execute(
                "INSERT INTO predictions (model_id, input_data, prediction, probability, label, source) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    self.current_model_id,
                    json.dumps(record, ensure_ascii=False),
                    int(predictions[i]),
                    probabilities[i] if probabilities[i] is not None else None,
                    result["loan_status_label"],
                    "json",
                ),
            )

        conn.commit()
        conn.close()
        return results

    def predict_from_csv(self, csv_bytes: bytes, filename: str = "data.csv"):
        if not self.is_loaded:
            raise ValueError("Модель не загружена")

        df = pd.read_csv(BytesIO(csv_bytes))
        original_df = df.copy()

        has_target = "loan_status" in df.columns
        if has_target:
            y_true = df["loan_status"].copy()
            df = df.drop(columns=["loan_status"])
        else:
            y_true = None

        df_processed = self._preprocess(df)
        predictions = self.pipeline.predict(df_processed)

        try:
            probabilities = self.pipeline.predict_proba(df_processed)[:, 1]
        except Exception:
            probabilities = None

        original_df["predicted_loan_status"] = predictions
        if probabilities is not None:
            original_df["probability"] = probabilities.round(4)

        conn = self._connect_db()
        for i in range(len(original_df)):
            conn.execute(
                "INSERT INTO predictions (model_id, input_data, prediction, probability, label, source) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    self.current_model_id,
                    json.dumps(df.iloc[i].to_dict(), ensure_ascii=False),
                    int(predictions[i]),
                    float(probabilities[i]) if probabilities is not None else None,
                    "одобрено" if predictions[i] == 1 else "отказ",
                    f"csv:{filename}",
                ),
            )
        conn.commit()
        conn.close()

        roc_auc = None
        if has_target and y_true is not None:
            try:
                roc_auc = float(roc_auc_score(y_true, predictions))
            except Exception:
                pass

        return original_df, roc_auc, len(original_df)

    def get_stats(self) -> dict:
        conn = self._connect_db()

        models_count = conn.execute("SELECT COUNT(*) FROM models").fetchone()[0]
        preds_count = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
        approved = conn.execute("SELECT COUNT(*) FROM predictions WHERE prediction = 1").fetchone()[0]
        rejected = conn.execute("SELECT COUNT(*) FROM predictions WHERE prediction = 0").fetchone()[0]

        recent = conn.execute(
            "SELECT * FROM predictions ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
        recent_list = [dict(row) for row in recent]

        conn.close()

        return {
            "models_uploaded": models_count,
            "predictions_made": preds_count,
            "approved": approved,
            "rejected": rejected,
            "recent_predictions": recent_list,
        }


model_service = ModelService()

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ml", "model.pkl")

if os.path.exists(MODEL_PATH):
    try:
        with open(MODEL_PATH, "rb") as f:
            model_service.load_model(f.read(), filename="model.pkl")
        logger.info(f"Модель автоматически загружена из {MODEL_PATH}")
    except Exception as e:
        logger.warning(f"Не удалось загрузить модель при старте: {e}")