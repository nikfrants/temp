from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ClientProfile(BaseModel):
    """Модель данных клиента"""
    user_id: int
    username: Optional[str] = None
    full_name: str
    phone_number: str
    passport_series_number: Optional[str] = None  # Можно заполнить позже
    passport_issued_by: Optional[str] = None
    passport_date_of_issue: Optional[str] = None
    registration_address: Optional[str] = None

    # Системные поля
    registered_at: datetime = Field(default_factory=datetime.now)


class TransferApplication(BaseModel):
    """Модель заявки на трансфер"""
    id: str  # Уникальный ID заявки
    user_id: int
    event_id: str
    event_name: str

    # Логистика
    dropoff_point: str
    dropoff_date: str

    # Доп услуги
    tech_service_needed: bool
    comment: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.now)