from abc import ABC, abstractmethod
from typing import Optional
from models.domain import ClientProfile, TransferApplication


class Repository(ABC):

    @abstractmethod
    async def get_user(self, user_id: int) -> Optional[ClientProfile]:
        """Получить пользователя по ID. Вернет None, если не найден."""
        pass

    @abstractmethod
    async def save_user(self, user: ClientProfile) -> bool:
        """Сохранить или обновить пользователя."""
        pass

    @abstractmethod
    async def create_application(self, application: TransferApplication) -> bool:
        """Создать новую заявку."""
        pass