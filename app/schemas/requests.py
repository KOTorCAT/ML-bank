"""
Схемы данных.
Описывают, как должны выглядеть запросы и ответы.
FastAPI использует их для автоматической проверки входных данных.
"""

from pydantic import BaseModel
from typing import Optional


class PreprocessedRecord(BaseModel):
    """
    Одна запись с данными клиента.
    Все 13 признаков, категории должны быть числами.
    """
    person_age: float
    person_income: float
    person_emp_exp: Optional[int] = None
    loan_amnt: float
    loan_int_rate: float
    loan_percent_income: float
    cb_person_cred_hist_length: float
    credit_score: int
    person_gender: Optional[int] = None
    person_education: Optional[int] = None
    person_home_ownership: Optional[int] = None
    loan_intent: Optional[int] = None
    previous_loan_defaults_on_file: Optional[int] = None


class PredictRequest(BaseModel):
    """Запрос на предсказание: список записей."""
    records: list[PreprocessedRecord]