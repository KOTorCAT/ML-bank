from pydantic import BaseModel, Field
from typing import List, Optional


class PreprocessedRecord(BaseModel):
    """Схема для уже предобработанных данных (из ML-пайплайна)"""
    person_age: float
    person_income: float
    person_emp_exp: Optional[int] = None
    loan_amnt: float
    loan_int_rate: float
    loan_percent_income: float
    cb_person_cred_hist_length: float
    credit_score: int
    person_gender_encoded: Optional[int] = None
    person_education_encoded: Optional[int] = None
    person_home_ownership_encoded: Optional[int] = None
    loan_intent_encoded: Optional[int] = None
    previous_loan_defaults_on_file_encoded: Optional[int] = None

    class Config:
        extra = "allow"  # Разрешаем дополнительные поля


class PredictRequest(BaseModel):
    """Запрос на предсказание"""
    records: List[PreprocessedRecord]


class PredictResponse(BaseModel):
    """Ответ с предсказаниями"""
    records: List[dict]
    status: str = "success"


class UploadModelResponse(BaseModel):
    """Ответ на загрузку модели"""
    message: str
    status: str = "success"


class PredictCsvResponse(BaseModel):
    """Ответ на предсказание из CSV"""
    csv_data: str  # CSV в виде строки
    roc_auc: Optional[float] = None
    status: str = "success"
    rows_processed: int