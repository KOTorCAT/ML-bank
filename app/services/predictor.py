"""
Сервис модели — главный файл с логикой.
Здесь происходит:
- загрузка модели из файла
- предобработка данных (кодирование категорий)
- вызов model.predict()
- сохранение истории в базу данных
"""

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

# Путь к файлу базы данных (создаётся автоматически)
DB_PATH = "app.db"


class ModelService:
    """
    Класс, который управляет моделью.
    Создаётся один раз при запуске сервера и живёт в памяти.
    """

    def __init__(self):
        # Поля, которые заполнятся при загрузке модели
        self.pipeline = None          # sklearn Pipeline (scaler + модель)
        self.is_loaded = False        # Загружена ли модель
        self.label_encoders = {}      # Кодировщики категорий (текст → число)
        self.categorical_cols = []    # Список категориальных колонок
        self.feature_cols = []        # Список всех признаков в правильном порядке
        self.current_model_id = None  # ID модели в базе данных

        # Создаём таблицы в базе, если их ещё нет
        self._create_tables()

    # ------------------------------------------------------------
    # База данных
    # ------------------------------------------------------------

    def _connect_db(self):
        """Подключение к SQLite. Файл app.db создастся сам, если его нет."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Чтобы можно было обращаться к колонкам по имени
        return conn

    def _create_tables(self):
        """Создаём две таблицы: models (история моделей) и predictions (история запросов)."""
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

    # ------------------------------------------------------------
    # Загрузка модели
    # ------------------------------------------------------------

    def load_model(self, model_bytes: bytes, filename: str = "model.pkl"):
        """
        Загружает модель из байтов.
        
        Что должно быть внутри .pkl файла:
        - pipeline: обученный sklearn Pipeline
        - label_encoders: словарь с LabelEncoder для каждой категориальной колонки
        - categorical_cols: список названий категориальных колонок
        - feature_cols: список всех 13 признаков в правильном порядке
        """
        # joblib.load умеет читать из байтов, если обернуть их в BytesIO
        data = joblib.load(BytesIO(model_bytes))

        # Достаём pipeline
        if isinstance(data, dict) and "pipeline" in data:
            self.pipeline = data["pipeline"]
            self.label_encoders = data.get("label_encoders", {})
            self.categorical_cols = data.get("categorical_cols", [])
            self.feature_cols = data.get("feature_cols", [])
        elif isinstance(data, Pipeline):
            # Если сохранили просто pipeline (без доп. информации)
            self.pipeline = data
        else:
            raise ValueError("Неизвестный формат модели")

        self.is_loaded = True

        # Сохраняем запись в таблицу models
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

    # ------------------------------------------------------------
    # Предобработка данных
    # ------------------------------------------------------------

    def _preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Готовит данные к подаче в модель:
        1. Кодирует текстовые категории в числа
        2. Выстраивает колонки в том порядке, который ожидает модель
        """
        df = df.copy()

        # Кодируем категориальные колонки
        for col in self.categorical_cols:
            if col in df.columns and col in self.label_encoders:
                encoder = self.label_encoders[col]
                # Если встретилось значение, которого не было при обучении — заменяем на первое известное
                df[col] = df[col].apply(lambda x: x if x in encoder.classes_ else encoder.classes_[0])
                df[col] = encoder.transform(df[col])

        # Оставляем только нужные колонки в правильном порядке
        if self.feature_cols:
            return df[self.feature_cols]
        return df

    # ------------------------------------------------------------
    # Предсказание
    # ------------------------------------------------------------

    def predict(self, records: list[dict]) -> list[dict]:
        """
        Предсказание для списка записей.
        
        Принимает: список словарей с признаками клиента
        Возвращает: тот же список, но с добавленными полями:
        - loan_status: 0 или 1
        - loan_status_label: "одобрено" или "отказ"
        - probability: вероятность
        """
        if not self.is_loaded:
            raise ValueError("Модель не загружена")

        # Словари → DataFrame
        df = pd.DataFrame(records)

        # Предобработка (если есть энкодеры — закодируем)
        if self.label_encoders:
            df = self._preprocess(df)
        elif self.feature_cols:
            df = df[self.feature_cols]

        # Вызываем модель
        predictions = self.pipeline.predict(df)

        # Пытаемся получить вероятности (не все модели это умеют)
        try:
            probabilities = self.pipeline.predict_proba(df)[:, 1]
        except Exception:
            probabilities = [None] * len(predictions)

        # Формируем результат
        results = []
        conn = self._connect_db()

        for i, record in enumerate(records):
            result = record.copy()
            result["loan_status"] = int(predictions[i])
            result["loan_status_label"] = "одобрено" if predictions[i] == 1 else "отказ"
            if probabilities[i] is not None:
                result["probability"] = round(float(probabilities[i]), 4)
            results.append(result)

            # Сохраняем в базу
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
        """
        Предсказание из CSV-файла.
        
        Возвращает:
        - DataFrame с исходными данными + колонки predicted_loan_status и probability
        - roc_auc (если в CSV была колонка loan_status)
        - количество обработанных строк
        """
        if not self.is_loaded:
            raise ValueError("Модель не загружена")

        # Читаем CSV
        df = pd.read_csv(BytesIO(csv_bytes))
        original_df = df.copy()

        # Проверяем, есть ли колонка с правильным ответом
        has_target = "loan_status" in df.columns
        if has_target:
            y_true = df["loan_status"].copy()
            df = df.drop(columns=["loan_status"])
        else:
            y_true = None

        # Предобработка и предсказание
        df_processed = self._preprocess(df)
        predictions = self.pipeline.predict(df_processed)

        try:
            probabilities = self.pipeline.predict_proba(df_processed)[:, 1]
        except Exception:
            probabilities = None

        # Добавляем результаты к исходным данным
        original_df["predicted_loan_status"] = predictions
        if probabilities is not None:
            original_df["probability"] = probabilities.round(4)

        # Сохраняем все предсказания в базу
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

        # Считаем ROC-AUC, если есть правильные ответы
        roc_auc = None
        if has_target and y_true is not None:
            try:
                roc_auc = float(roc_auc_score(y_true, predictions))
            except Exception:
                pass

        return original_df, roc_auc, len(original_df)

    # ------------------------------------------------------------
    # Статистика
    # ------------------------------------------------------------

    def get_stats(self) -> dict:
        """Собирает статистику из базы данных."""
        conn = self._connect_db()

        models_count = conn.execute("SELECT COUNT(*) FROM models").fetchone()[0]
        preds_count = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]

        # Сколько одобрено и сколько отказов
        approved = conn.execute("SELECT COUNT(*) FROM predictions WHERE prediction = 1").fetchone()[0]
        rejected = conn.execute("SELECT COUNT(*) FROM predictions WHERE prediction = 0").fetchone()[0]

        # Последние 10 запросов
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


# Создаём один экземпляр сервиса при запуске
model_service = ModelService()